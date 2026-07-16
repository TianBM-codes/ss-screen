"""Command-line interface: ``ss-screen``.

Subcommands mirroring the implemented pipeline stages:

  ``ss-screen valence-filter``  pre-filter metallic / mixed-valence structures
  ``ss-screen dataset mp``      build normalized MP dataset DataFrames
  ``ss-screen composition-screen`` pre-screen composition-template candidates
  ``ss-screen condense``        build robocrys condensed JSON inputs
  ``ss-screen structure-match`` match candidates by condensed structure archive
  ``ss-screen gap-export``      export candidates for external gap calculations
  ``ss-screen gap-compare``     compare final pairs across gap methods
  ``ss-screen stability``       generate optional stability-screening inputs
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
from ..pair.grouping import (
    attach_band_gaps,
    group_by_composition_template,
    screen_composition_candidates,
)
from ..pair.pairing import enumerate_pairs, pairs_to_dataframe


@click.group()
@click.version_option(package_name="ss-screen")
def cli() -> None:
    """Screen materials pairs for solid-solution formation."""


def _parse_supercell(value: str) -> tuple[int, int, int]:
    parts = [part.strip() for part in value.replace("x", ",").split(",")]
    if len(parts) != 3:
        raise click.BadParameter("expected three integers, for example 2,2,2")
    try:
        supercell = tuple(int(part) for part in parts)
    except ValueError as exc:
        raise click.BadParameter("expected three integers, for example 2,2,2") from exc
    if any(dim <= 0 for dim in supercell):
        raise click.BadParameter("supercell dimensions must be positive")
    return supercell


# ---------------------------------------------------------------------------
# dataset
# ---------------------------------------------------------------------------
@cli.group("dataset")
def dataset_cmd() -> None:
    """Build normalized source dataset DataFrames."""


@dataset_cmd.command("mp")
@click.option(
    "--backend",
    type=click.Choice(["offline", "api"]),
    default="offline",
    show_default=True,
    help="Materials Project source backend.",
)
@click.option(
    "--offline-db",
    "offline_db",
    type=click.Path(path_type=Path),
    help="Optional mp_offline SQLite database path.",
)
@click.option(
    "--output",
    "output",
    type=click.Path(path_type=Path),
    required=True,
    help="Where to write the normalized MP pickle DataFrame.",
)
@click.option(
    "--max-e-hull",
    "max_e_hull",
    type=float,
    default=0.01,
    show_default=True,
    help="Maximum MP energy above hull to request (eV/atom).",
)
def dataset_mp_cmd(backend: str, offline_db: Path | None, output: Path, max_e_hull: float) -> None:
    """Fetch Materials Project summaries into the screening schema."""
    from ..data.mp import load_mp_dataset

    try:
        df = load_mp_dataset(
            output=output,
            max_e_hull=max_e_hull,
            backend=backend,
            offline_db=offline_db,
        )
    except ImportError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Wrote {len(df)} MP rows to {output}")


@dataset_cmd.command("wbm")
@click.option(
    "--xyz",
    "xyz_path",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="WBM extxyz file, e.g. wbm-dataset.xyz.",
)
@click.option(
    "--summary",
    "summary_path",
    type=click.Path(exists=True, path_type=Path),
    help="Optional WBM summary TSV/CSV file.",
)
@click.option(
    "--output",
    "output",
    type=click.Path(path_type=Path),
    required=True,
    help="Where to write the normalized WBM pickle DataFrame.",
)
def dataset_wbm_cmd(xyz_path: Path, summary_path: Path | None, output: Path) -> None:
    """Load WBM extxyz data into the screening schema."""
    from ..data.wbm import load_wbm_dataset

    try:
        df = load_wbm_dataset(xyz_path=xyz_path, output=output, summary_path=summary_path)
    except ImportError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Wrote {len(df)} WBM rows to {output}")


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
    type=click.Path(exists=True, path_type=Path),
    help="Structure file or directory to condense (repeatable).",
)
@click.option(
    "--df",
    "df_path",
    type=click.Path(exists=True, path_type=Path),
    help="Pickled normalized dataset DataFrame to condense.",
)
@click.option(
    "--structure-column",
    "structure_col",
    default="structure",
    show_default=True,
    help="DataFrame column containing pymatgen Structure objects.",
)
@click.option(
    "--material-id-column",
    "material_id_col",
    help="Optional DataFrame column for material IDs; default uses the DataFrame index.",
)
@click.option(
    "--output-dir",
    "output_dir",
    type=click.Path(path_type=Path),
    required=True,
    help="Directory for {material_id}.json condensed outputs.",
)
@click.option("--manifest", "manifest_path", type=click.Path(path_type=Path))
@click.option("--index", "index_path", type=click.Path(path_type=Path))
@click.option("--limit", type=int, help="Limit number of DataFrame rows to condense.")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing outputs.")
@click.option(
    "--stop-on-error",
    is_flag=True,
    default=False,
    help="Stop on the first condensation error instead of recording failures.",
)
def condense_cmd(
    inputs: tuple[Path, ...],
    df_path: Path | None,
    structure_col: str,
    material_id_col: str | None,
    output_dir: Path,
    manifest_path: Path | None,
    index_path: Path | None,
    limit: int | None,
    overwrite: bool,
    stop_on_error: bool,
) -> None:
    """Build robocrys condensed-structure JSON files."""
    from ..data.condense import condense_dataframe, condense_paths

    if bool(inputs) == bool(df_path):
        raise click.UsageError("Provide exactly one of --input or --df.")
    try:
        if df_path:
            summary = condense_dataframe(
                df_path=df_path,
                output_dir=output_dir,
                structure_col=structure_col,
                material_id_col=material_id_col,
                limit=limit,
                overwrite=overwrite,
                manifest_path=manifest_path,
                index_path=index_path,
                continue_on_error=not stop_on_error,
            )
        else:
            summary = condense_paths(
                list(inputs),
                output_dir,
                overwrite=overwrite,
                manifest_path=manifest_path,
                index_path=index_path,
                continue_on_error=not stop_on_error,
            )
    except ImportError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(
        "Condense summary: "
        f"written={summary.written} skipped={summary.skipped} failed={summary.failed}"
    )


@cli.command("condense-index")
@click.option(
    "--condensed-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
)
@click.option("--output", type=click.Path(path_type=Path), required=True)
def condense_index_cmd(condensed_dir: Path, output: Path) -> None:
    """Build a CSV index for a condensed-structure JSON directory."""
    from ..data.condense import build_archive_index

    index = build_archive_index(condensed_dir, output)
    click.echo(f"Indexed {len(index)} condensed files to {output}")


@cli.command("condense-validate")
@click.option(
    "--condensed-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
)
@click.option("--output", type=click.Path(path_type=Path), required=True)
def condense_validate_cmd(condensed_dir: Path, output: Path) -> None:
    """Validate required robocrys keys in a condensed-structure archive."""
    from ..data.condense import validate_archive

    validation = validate_archive(condensed_dir, index_path=output)
    counts = validation["status"].value_counts().to_dict() if len(validation) else {}
    click.echo(
        f"Validation summary: valid={counts.get('valid', 0)} "
        f"invalid={counts.get('invalid', 0)} output={output}"
    )


# ---------------------------------------------------------------------------
# structure-match
# ---------------------------------------------------------------------------
@cli.command("structure-match")
@click.option(
    "--candidates",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Composition-candidate CSV from `ss-screen composition-screen`.",
)
@click.option(
    "--condensed-dir",
    "condensed_dirs",
    multiple=True,
    required=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Condensed JSON archive directory (repeatable).",
)
@click.option("--min-x-elements", type=int, default=2, show_default=True)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    required=True,
    help="Output structure-group JSON.",
)
@click.option(
    "--summary",
    type=click.Path(path_type=Path),
    help="Optional JSON structure-match summary.",
)
def structure_match_cmd(
    candidates: Path,
    condensed_dirs: tuple[Path, ...],
    min_x_elements: int,
    output: Path,
    summary: Path | None,
) -> None:
    """Match composition candidates by robocrys environment descriptors."""
    from monty.serialization import dumpfn

    from ..pair.structure_match import match_structure_candidates

    groups, report = match_structure_candidates(
        candidates,
        list(condensed_dirs),
        min_x_elements=min_x_elements,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    dump_group_df(groups, output)
    if summary:
        summary.parent.mkdir(parents=True, exist_ok=True)
        dumpfn(report, str(summary))
    click.echo(
        f"Wrote {len(groups)} structure groups to {output} "
        f"(missing_descriptions={report['missing_descriptions']})"
    )


# ---------------------------------------------------------------------------
# gap-export / gap-validate
# ---------------------------------------------------------------------------
@cli.command("gap-export")
@click.option(
    "--groups", "groups_path", type=click.Path(exists=True, path_type=Path), required=True
)
@click.option(
    "--dataset",
    "dataset_path",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Normalized dataset pickle containing source structures.",
)
@click.option("--method", default="external", show_default=True)
@click.option("--structure-dir", type=click.Path(path_type=Path))
@click.option("--structure-column", "structure_col", default="structure", show_default=True)
@click.option("--max-natoms", type=int, default=30, show_default=True)
@click.option("--output", type=click.Path(path_type=Path), required=True)
def gap_export_cmd(
    groups_path: Path,
    dataset_path: Path,
    method: str,
    structure_dir: Path | None,
    structure_col: str,
    max_natoms: int | None,
    output: Path,
) -> None:
    """Export matched group members for external high-level gap calculations."""
    from ..pair.gap_export import export_gap_candidates

    exported = export_gap_candidates(
        groups_path=groups_path,
        dataset_path=dataset_path,
        output=output,
        method=method,
        structure_dir=structure_dir,
        structure_col=structure_col,
        max_natoms=max_natoms,
    )
    click.echo(f"Wrote {len(exported)} gap candidates to {output}")


@cli.command("gap-validate")
@click.option("--gaps", type=click.Path(exists=True, path_type=Path), required=True)
def gap_validate_cmd(gaps: Path) -> None:
    """Validate external high-level gap-result schema."""
    from ..pair.gap_export import validate_gap_results

    results = validate_gap_results(gaps)
    click.echo(f"Validated {len(results)} gap-result rows from {gaps}")


@cli.command("gap-compare")
@click.option(
    "--groups", "groups_path", type=click.Path(exists=True, path_type=Path), required=True
)
@click.option(
    "--gap-results",
    "gap_results",
    multiple=True,
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="External gap-result CSV using the stable schema from `gap-validate`.",
)
@click.option("--low-gap", "low_gap", type=float, default=0.15, show_default=True)
@click.option("--direct-min", "direct_min", type=float, default=0.15, show_default=True)
@click.option("--direct-max", "direct_max", type=float, default=1.5, show_default=True)
@click.option("--pair-any-below", "pair_any_below", type=float, default=0.3, show_default=True)
@click.option("--pair-any-above", "pair_any_above", type=float, default=0.2, show_default=True)
@click.option("--pair-both-below", "pair_both_below", type=float, default=0.8, show_default=True)
@click.option("--output-dir", type=click.Path(path_type=Path), required=True)
@click.option("--summary", type=click.Path(path_type=Path), required=True)
def gap_compare_cmd(
    groups_path: Path,
    gap_results: tuple[Path, ...],
    low_gap: float,
    direct_min: float,
    direct_max: float,
    pair_any_below: float,
    pair_any_above: float,
    pair_both_below: float,
    output_dir: Path,
    summary: Path,
) -> None:
    """Compare final pair outputs across external gap methods."""
    from ..config import PairThresholds
    from ..pair.gap_feedback import compare_gap_methods

    report = compare_gap_methods(
        groups_path=groups_path,
        gap_paths=gap_results,
        output_dir=output_dir,
        summary=summary,
        thresholds=PairThresholds(
            low_gap=low_gap,
            direct_min=direct_min,
            direct_max=direct_max,
            pair_any_below=pair_any_below,
            pair_any_above=pair_any_above,
            pair_both_below=pair_both_below,
        ),
    )
    click.echo(f"Compared {len(report['methods'])} methods to {summary} (outputs={output_dir})")


# ---------------------------------------------------------------------------
# stability
# ---------------------------------------------------------------------------
@cli.group("stability")
def stability_cmd() -> None:
    """Generate optional preliminary stability-screening inputs."""


@stability_cmd.command("sqs-generate")
@click.option(
    "--pairs",
    "pairs_path",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Final pair CSV from `ss-screen pair`.",
)
@click.option(
    "--dataset",
    "dataset_path",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Normalized dataset pickle containing endpoint structures.",
)
@click.option(
    "--target-fraction",
    "target_fractions",
    multiple=True,
    type=click.FloatRange(0.0, 1.0),
    default=(0.5,),
    show_default=True,
    help="Target fraction of endpoint B on the substituted site.",
)
@click.option(
    "--supercell",
    callback=lambda _ctx, _param, value: _parse_supercell(value),
    default="2,2,2",
    show_default=True,
    help="Diagonal supercell as 'a,b,c' or 'axbxc'.",
)
@click.option(
    "--backend",
    type=click.Choice(["random", "icet"]),
    default="random",
    show_default=True,
    help="Alloy structure generator backend.",
)
@click.option(
    "--cutoff",
    "cutoffs",
    multiple=True,
    type=float,
    default=(4.0,),
    show_default=True,
    help="icet cluster-space cutoff in Angstrom; repeat for higher orders.",
)
@click.option(
    "--sqs-steps",
    type=int,
    help="Number of icet/mchammer Monte Carlo steps; icet chooses a default if omitted.",
)
@click.option("--seed", type=int, default=0, show_default=True)
@click.option("--output-dir", type=click.Path(path_type=Path), required=True)
@click.option("--manifest", "manifest_path", type=click.Path(path_type=Path), required=True)
def stability_sqs_generate_cmd(
    pairs_path: Path,
    dataset_path: Path,
    target_fractions: tuple[float, ...],
    supercell: tuple[int, int, int],
    backend: str,
    cutoffs: tuple[float, ...],
    sqs_steps: int | None,
    seed: int,
    output_dir: Path,
    manifest_path: Path,
) -> None:
    """Generate representative random-substitution alloy structures."""
    from ..stability.sqs import generate_sqs_inputs

    records = generate_sqs_inputs(
        pairs_path=pairs_path,
        dataset_path=dataset_path,
        output_dir=output_dir,
        manifest_path=manifest_path,
        target_fractions=target_fractions,
        supercell=supercell,
        seed=seed,
        backend=backend,
        cutoffs=cutoffs,
        sqs_steps=sqs_steps,
    )
    statuses = pd.Series([record["status"] for record in records]).value_counts().to_dict()
    click.echo(
        f"SQS input summary: written={statuses.get('written', 0)} "
        f"skipped={statuses.get('skipped', 0)} manifest={manifest_path}"
    )


# ---------------------------------------------------------------------------
# composition-screen
# ---------------------------------------------------------------------------
@cli.command("composition-screen")
@click.option(
    "--df",
    "df_paths",
    multiple=True,
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Pickled normalized dataset DataFrame (repeatable).",
)
@click.option(
    "--valence-ids",
    "valence_ids",
    type=click.Path(exists=True, path_type=Path),
    help="Optional JSON list of valence-valid IDs (from `valence-filter`).",
)
@click.option("--nelems", type=int, default=2, show_default=True)
@click.option("--max-bandgap", type=float, default=1.0, show_default=True)
@click.option("--max-e-hull", "max_e_hull", type=float, default=0.0, show_default=True)
@click.option("--min-group-size", type=int, default=2, show_default=True)
@click.option("--min-x-elements", type=int, default=2, show_default=True)
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
    help="CSV table of composition-template candidates.",
)
@click.option(
    "--summary",
    "summary",
    type=click.Path(path_type=Path),
    help="Optional JSON screening summary.",
)
def composition_screen_cmd(
    df_paths: tuple[Path, ...],
    valence_ids: Path | None,
    nelems: int,
    max_bandgap: float,
    max_e_hull: float,
    min_group_size: int,
    min_x_elements: int,
    excluded_elements: tuple[str, ...],
    output: Path,
    summary: Path | None,
) -> None:
    """Screen composition-template candidates before structure matching."""
    from monty.serialization import dumpfn, loadfn

    frames = [pd.read_pickle(path) for path in df_paths]
    df = pd.concat(frames, axis=0)
    if valence_ids:
        valid = loadfn(str(valence_ids))
        df = df.loc[valid]

    thresholds = Thresholds.default(nelems).with_nelems(nelems)
    excluded = (
        coerce_excluded(excluded_elements) if excluded_elements else thresholds.excluded_elements
    )
    candidates, report = screen_composition_candidates(
        df,
        nelems=nelems,
        max_bandgap=max_bandgap,
        max_e_hull=max_e_hull,
        excluded_elements=excluded,
        min_group_size=min_group_size,
        min_x_elements=min_x_elements,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(output, index=False)
    if summary:
        summary.parent.mkdir(parents=True, exist_ok=True)
        dumpfn(report, str(summary))

    click.echo(
        f"Wrote {len(candidates)} composition-candidate rows "
        f"across {report['template_count']} templates to {output}"
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
    help="Legacy mbj_gaps_*_pmg_info.csv with computed gaps.",
)
@click.option(
    "--gap-results",
    "gap_results",
    multiple=True,
    type=click.Path(exists=True, path_type=Path),
    help="External gap-result CSV using the stable schema from `gap-validate`.",
)
@click.option("--low-gap", "low_gap", type=float, default=0.15, show_default=True)
@click.option("--direct-min", "direct_min", type=float, default=0.15, show_default=True)
@click.option("--direct-max", "direct_max", type=float, default=1.5, show_default=True)
@click.option("--pair-any-below", "pair_any_below", type=float, default=0.3, show_default=True)
@click.option("--pair-any-above", "pair_any_above", type=float, default=0.2, show_default=True)
@click.option("--pair-both-below", "pair_both_below", type=float, default=0.8, show_default=True)
@click.option("--method", help="Method to select from --gap-results when multiple are present.")
@click.option("--summary", type=click.Path(path_type=Path), help="Optional coverage JSON summary.")
@click.option("--output", "output", type=click.Path(path_type=Path), required=True)
def pair_cmd(
    groups_path,
    gaps_path,
    gap_results,
    low_gap,
    direct_min,
    direct_max,
    pair_any_below,
    pair_any_above,
    pair_both_below,
    method,
    summary,
    output,
):
    """Enumerate promising alloying pairs from computed gaps."""
    from ..config import PairThresholds
    from ..pair.pairing import attach_gaps_and_compress, gaps_valid

    t = PairThresholds(
        low_gap=low_gap,
        direct_min=direct_min,
        direct_max=direct_max,
        pair_any_below=pair_any_below,
        pair_any_above=pair_any_above,
        pair_both_below=pair_both_below,
    )
    if bool(gaps_path) == bool(gap_results):
        raise click.UsageError("Provide exactly one of --gaps or --gap-results.")

    if gap_results:
        from ..pair.gap_feedback import generate_pairs_from_gap_results

        pairs_df, report = generate_pairs_from_gap_results(
            groups_path=groups_path,
            gap_paths=gap_results,
            output=output,
            summary=summary,
            method=method,
            thresholds=t,
        )
        click.echo(
            f"Wrote {len(pairs_df)} pairs to {output} "
            f"(coverage={report['covered_materials']}/{report['materials_in_groups']})"
        )
        return

    groups = load_group_df(groups_path)
    gap_map = read_mbj_gaps(gaps_path)

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
