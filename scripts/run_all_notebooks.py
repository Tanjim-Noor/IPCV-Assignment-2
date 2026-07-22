"""Execute the numbered IPCV stage notebooks in order."""

from __future__ import annotations

import argparse
import traceback
from pathlib import Path

import nbformat
from nbclient import NotebookClient


def stage_notebooks(repo_root: Path) -> list[Path]:
    """Return stage notebooks in numeric directory order."""

    return sorted(
        (repo_root / "implementation" / "stages").glob("*/[0-9][0-9]_*.ipynb"),
        key=lambda path: path.as_posix(),
    )


def execute_notebook(notebook_path: Path, repo_root: Path, timeout: int, save_results: bool) -> None:
    """Execute one notebook with the repository root as its working directory."""

    notebook = nbformat.read(notebook_path, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=timeout,
        kernel_name="python3",
        resources={"metadata": {"path": str(repo_root)}},
        allow_errors=False,
    )
    client.execute()
    if save_results:
        nbformat.write(notebook, notebook_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--timeout",
        type=int,
        default=900,
        help="Maximum seconds allowed for each notebook cell (default: 900).",
    )
    parser.add_argument(
        "--write-results",
        action="store_true",
        help="Save execution counts and outputs back into the source notebooks.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    notebooks = stage_notebooks(repo_root)
    if not notebooks:
        print("No stage notebooks found.")
        return 1

    failures: list[tuple[Path, BaseException]] = []
    for notebook_path in notebooks:
        relative_path = notebook_path.relative_to(repo_root)
        print(f"\n=== Running {relative_path} ===", flush=True)
        try:
            execute_notebook(notebook_path, repo_root, args.timeout, args.write_results)
        except BaseException as exc:  # keep the remaining ordered stages running
            failures.append((relative_path, exc))
            print(f"FAILED: {type(exc).__name__}: {exc}", flush=True)
            traceback.print_exc()
        else:
            print("PASSED", flush=True)

    print(f"\nCompleted {len(notebooks)} notebook(s): {len(notebooks) - len(failures)} passed, {len(failures)} failed.")
    if failures:
        print("Failures:")
        for path, exc in failures:
            print(f"- {path}: {type(exc).__name__}: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
