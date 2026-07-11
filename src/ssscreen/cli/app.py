"""Command-line interface: ``ss-screen``.

Subcommands mirroring the implemented pipeline stages:

  ``ss-screen valence-filter``  pre-filter metallic / mixed-valence structures
  ``ss-screen condense``        build robocrys condensed JSON inputs
  ``ss-screen group``           group by composition template + environment
  ``ss-screen pair``            enumerate promising alloying pairs from gaps

Each command surfaces the notebook magic numbers as ``--options`` with sensible
defaults (the research values). All paths are CLI arguments — nothing is
hard-coded.
"""

from __future__ import annotations

from pathlib import Path

import click
import pandas as pd

from ..config import Thresholds, coerce_excluded
from ..data.io import (
    CondenseLoader,
    dump_group_df,
    load_group_df,
    read_mbj_gaps,
    write_pairs_csv,
)
from ..pair.envmatch import find_unique_envs, group_similar_structures
from ..pair.filters import apply_element_exclusion, apply_size_gate, has_gap_diversity
from ..pair.grouping import attach_band_gaps, group_by_composition_template
from ..pair.pairing import enumerate_pairs, pairs_to_dataframe


@click.group()
@click.version_option(package_name="ss-screen")
def cli() -> None:
    """Screen materials pairs for solid-solution formation."""


# ---------------------------------------------------------------------------
# valence-filter
# ---------------------------------------------------------------------------
@cli.command("valence-filter")
@click.option(
    "--df-mp",
    "df_mp",
    type=click.Path(exists=True, path_type=Path),
    help="Pickled MP dataset DataFrame (e.g. mp.df).",
)
@click.option(
    "--df-wbm",
    "df_wbm",
    type=click.Path(exists=True, path_type=Path),
    help="Pickled WBM dataset DataFrame (e.g. wbm-dataset.df).",
)
@click.option(
    "--output",
    "output",
    type=click.Path(path_type=Path),
    required=True,
    help="Where to write the JSON list of valid material IDs.",
)
@click.option("--no-verbose", is_flag=True, default=False, help="Disable the progress bar.")
def valence_filter_cmd(
    df_mp: Path | None, df_wbm: Path | None, output: Path, no_verbose: bool
) -> None:
    """Pre-filter metallic / mixed-valence structures via bond-valence analysis.

    Loads one or both pickled DataFrames (indexed by material ID, with a
    ``structure`` column of pymatgen Structures) and writes the IDs whose
    oxidation states BVAnalyzer can assign.
    """
    from monty.serialization import dumpfn

    from ..pair.filters import valence_filter

    frames = []
    if df_mp:
        frames.append(pd.read_pickle(df_mp))
    if df_wbm:
        frames.append(pd.read_pickle(df_wbm))
    if not frames:
        raise click.UsageError("Provide at least one of --df-mp / --df-wbm.")
    df = pd.concat(frames, axis=0)

    valid = valence_filter(df, verbose=not no_verbose)
    dumpfn(valid, str(output))
    click.echo(f"Wrote {len(valid)} valence-valid IDs to {output}")


# ---------------------------------------------------------------------------
# condense
# ---------------------------------------------------------------------------
@cli.command("condense")
@click.option(
    "--input",
    "inputs",
    multiple=True,
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Structure file or directory to condense (repeatable).",
)
@click.option(
    "--output-dir",
    "output_dir",
    type=click.Path(path_type=Path),
    required=True,
    help="Directory for {material_id}.json condensed outputs.",
)
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing outputs.")
def condense_cmd(inputs: tuple[Path, ...], output_dir: Path, overwrite: bool) -> None:
    """Build robocrys condensed-structure JSON files."""
    from ..data.condense import condense_paths

    try:
        summary = condense_paths(list(inputs), output_dir, overwrite=overwrite)
    except ImportError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(
        "Condense summary: "
        f"written={summary.written} skipped={summary.skipped} failed={summary.failed}"
    )


# ---------------------------------------------------------------------------
# group
# ---------------------------------------------------------------------------
@cli.command("group")
@click.option("--df-mp", "df_mp", type=click.Path(exists=True, path_type=Path))
@click.option("--df-wbm", "df_wbm", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--valence-ids",
    "valence_ids",
    type=click.Path(exists=True, path_type=Path),
    help="Optional JSON list of valence-valid IDs (from `valence-filter`).",
)
@click.option(
    "--nelems",
    type=int,
    default=2,
    show_default=True,
    help="Number of elements in the reduced composition (2 or 3).",
)
@click.option(
    "--condensed-dirs",
    "condensed_dirs",
    multiple=True,
    required=True,
    type=click.Path(exists=True, file_okay=False),
    help="Directories of robocrys condensed JSONs (repeatable).",
)
@click.option(
    "--max-bandgap",
    type=float,
    default=1.0,
    show_default=True,
    help="Keep materials with PBE band gap below this (eV).",
)
@click.option(
    "--max-e-hull",
    "max_e_hull",
    type=float,
    default=0.0,
    show_default=True,
    help="Keep materials with energy above hull at most this (eV/atom).",
)
@click.option(
    "--max-natoms",
    type=int,
    default=None,
    help="Primitive-cell atom cap for the *output* structures (default 30 binary / 45 ternary).",
)
@click.option(
    "--excluded-elements",
    "excluded_elements",
    multiple=True,
    default=[],
    help="Extra elements to exclude (added to the default list).",
)
@click.option(
    "--output",
    "output",
    type=click.Path(path_type=Path),
    required=True,
    help="Output group JSON (array of StructureGroup records).",
)
@click.option("--no-verbose", is_flag=True, default=False)
def group_cmd(
    df_mp,
    df_wbm,
    valence_ids,
    nelems,
    condensed_dirs,
    max_bandgap,
    max_e_hull,
    max_natoms,
    excluded_elements,
    output,
    no_verbose,
):
    """Group materials by composition template + environment fingerprint."""
    from tqdm.auto import tqdm

    # Load + concatenate data.
    frames = []
    if df_mp:
        frames.append(pd.read_pickle(df_mp))
    if df_wbm:
        frames.append(pd.read_pickle(df_wbm))
    if not frames:
        raise click.UsageError("Provide at least one of --df-mp / --df-wbm.")
    df_all = pd.concat(frames, axis=0)

    # Optional valence pre-filter.
    if valence_ids:
        from monty.serialization import loadfn

        valid = loadfn(str(valence_ids))
        df_all = df_all.loc[valid]

    # Selection thresholds (stage 1).
    t = Thresholds.default(nelems).with_nelems(nelems)
    sel = t.selection
    if max_bandgap != sel.max_bandgap or max_e_hull != sel.max_e_hull:
        from dataclasses import replace

        t = replace(t, selection=replace(sel, max_bandgap=max_bandgap, max_e_hull=max_e_hull))
    excluded = coerce_excluded(excluded_elements) if excluded_elements else t.excluded_elements
    if max_natoms is not None:
        from dataclasses import replace

        t = replace(t, max_natoms=max_natoms)

    # Stage 1: select by nelems, gap, hull.
    df_t = df_all.loc[
        (df_all["nelems"] == nelems)
        & (df_all["e_hull"] <= max_e_hull)
        & (df_all["band_gap"] < max_bandgap),
        :,
    ]
    click.echo(
        f"Selected {len(df_t)} materials (nelems={nelems}, gap<{max_bandgap}, e_hull<={max_e_hull})"
    )

    # Stage 2: composition-template grouping.
    templates = group_by_composition_template(df_t, nelems=nelems)
    click.echo(f"{len(templates)} composition templates with >=2 members")

    # Stage 3: environment grouping within each template.
    loader = CondenseLoader(list(condensed_dirs))
    all_groups = []
    iterator = tqdm(
        templates.items(), disable=no_verbose, desc="env grouping", total=len(templates)
    )
    for key, entries in iterator:
        # entries: list of [mp_id, x_elem, band_gap]
        mp_ids = [e[0] for e in entries]
        condensed = [loader.get_condensed(mid) for mid in mp_ids]
        envs = find_unique_envs(condensed)
        groups = group_similar_structures(envs, key, mp_ids)
        attach_band_gaps(groups, entries)
        all_groups.extend(groups)

    # Keep groups with X-element diversity.
    import numpy as np

    all_groups = [g for g in all_groups if len(np.unique(g.X_element)) > 1]
    click.echo(f"{len(all_groups)} groups after X-diversity filter")

    # Stage 4: element exclusion + gap-diversity gate.
    valid_groups = []
    for g in all_groups:
        kept = apply_element_exclusion(g, excluded)
        if kept is None:
            continue
        if not has_gap_diversity(kept, require_zero=t.group.require_zero_gap_member):
            continue
        valid_groups.append(kept)
    click.echo(f"{len(valid_groups)} groups after element-exclusion + gap gate")

    # Stage 4b (output preparation): apply size gate to the referenced structures.
    all_ids = {mid for g in valid_groups for mid in g.mp_ids}
    if all_ids:
        calc_df = df_t.loc[list(all_ids)].copy()
        calc_df = apply_size_gate(calc_df, t.max_natoms)
        surviving = set(calc_df.index.astype(str))
        valid_groups = [g for g in valid_groups if all(m in surviving for m in g.mp_ids)]
    click.echo(f"{len(valid_groups)} groups survive the size gate (natoms<{t.max_natoms})")

    dump_group_df(valid_groups, output)
    click.echo(f"Wrote {len(valid_groups)} groups to {output}")


# ---------------------------------------------------------------------------
# pair
# ---------------------------------------------------------------------------
@cli.command("pair")
@click.option(
    "--groups",
    "groups_path",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Group JSON from `ss-screen group`.",
)
@click.option(
    "--gaps",
    "gaps_path",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="mbj_gaps_*_pmg_info.csv with computed gaps.",
)
@click.option("--low-gap", "low_gap", type=float, default=0.15, show_default=True)
@click.option("--direct-min", "direct_min", type=float, default=0.15, show_default=True)
@click.option("--direct-max", "direct_max", type=float, default=1.5, show_default=True)
@click.option("--pair-any-below", "pair_any_below", type=float, default=0.3, show_default=True)
@click.option("--pair-any-above", "pair_any_above", type=float, default=0.2, show_default=True)
@click.option("--pair-both-below", "pair_both_below", type=float, default=0.8, show_default=True)
@click.option("--output", "output", type=click.Path(path_type=Path), required=True)
def pair_cmd(
    groups_path,
    gaps_path,
    low_gap,
    direct_min,
    direct_max,
    pair_any_below,
    pair_any_above,
    pair_both_below,
    output,
):
    """Enumerate promising alloying pairs from computed gaps."""
    from ..config import PairThresholds
    from ..pair.pairing import attach_gaps_and_compress, gaps_valid

    groups = load_group_df(groups_path)
    gap_map = read_mbj_gaps(gaps_path)

    t = PairThresholds(
        low_gap=low_gap,
        direct_min=direct_min,
        direct_max=direct_max,
        pair_any_below=pair_any_below,
        pair_any_above=pair_any_above,
        pair_both_below=pair_both_below,
    )

    all_pairs = []
    for g in groups:
        compressed = attach_gaps_and_compress(g, gap_map)
        if compressed is None:
            continue
        g_aligned, gaps = compressed
        if not gaps_valid(gaps, t):
            continue
        all_pairs.extend(enumerate_pairs(g_aligned, gaps, t))

    pairs_df = pairs_to_dataframe(all_pairs)
    write_pairs_csv(pairs_df, output)
    click.echo(f"Wrote {len(pairs_df)} pairs to {output}")


if __name__ == "__main__":
    cli()
