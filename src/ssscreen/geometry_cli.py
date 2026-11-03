"""Standalone CLI entry for Stage 13 offline geometry evidence."""
from __future__ import annotations

from pathlib import Path
import click

from .geometry_pipeline import evaluate


@click.command('geometry-evaluate')
@click.option('--input', 'input_dir', type=click.Path(path_type=Path,exists=True,file_okay=False),required=True)
@click.option('--config','config_path',type=click.Path(path_type=Path,exists=True,dir_okay=False),required=True)
@click.option('--output','output_dir',type=click.Path(path_type=Path),required=True)
def main(input_dir: Path, config_path: Path, output_dir: Path) -> None:
    """Compute endmember lattice alignment and seed-selected substrate geometry."""
    try:
        summary=evaluate(input_dir,config_path,output_dir)
    except (ValueError,FileNotFoundError,ImportError,OSError) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Evaluated {summary['candidate_count']} candidates; "
               f"{summary['matching_solutions']} geometric matches; output={output_dir}")


if __name__=='__main__':main()
