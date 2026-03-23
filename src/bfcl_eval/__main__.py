from typing import List, Optional

import typer
from dotenv import load_dotenv

from bfcl_eval.constants.eval_config import DOTENV_PATH, PROJECT_ROOT, RESULT_PATH, SCORE_PATH


cli = typer.Typer(
    context_settings=dict(help_option_names=["-h", "--help"]),
    no_args_is_help=True,
)


@cli.command()
def evaluate(
    model: List[str] = typer.Option(
        None,
        help="A list of model names to evaluate.",
    ),
    test_category: List[str] = typer.Option(
        ["all"],
        help="A list of test categories to run the evaluation on.",
    ),
    result_dir: str = typer.Option(
        None,
        "--result-dir",
        help="Path to the model response folder.",
    ),
    score_dir: str = typer.Option(
        None,
        "--score-dir",
        help="Path to the evaluation score folder.",
    ),
    partial_eval: bool = typer.Option(
        False,
        "--partial-eval",
        help="Run evaluation on a partial set of benchmark entries.",
    ),
    is_fc: bool = typer.Option(
        True,
        "--is-fc/--no-fc",
        help="Whether model results use function-calling format (default: True).",
    ),
    underscore_to_dot: bool = typer.Option(
        True,
        "--underscore-to-dot/--no-underscore-to-dot",
        help="Whether to convert '.' to '_' in function names (default: True).",
    ),
):
    """Evaluate results from one or more models on a test-category."""
    from bfcl_eval.checker.eval_runner import main as evaluation_main

    load_dotenv(dotenv_path=DOTENV_PATH, verbose=True, override=True)
    evaluation_main(
        model, test_category, result_dir, score_dir,
        partial_eval=partial_eval, is_fc=is_fc, underscore_to_dot=underscore_to_dot,
    )


if __name__ == "__main__":
    cli()
