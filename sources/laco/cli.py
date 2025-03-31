# pragma: no cover
import sys
import argparse
import laco
import expath


def _get_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="laco",
        description="Laco CLI - A command line interface for Laco.",
    )
    p.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output file. Defaults to stdout.",
    )
    p.add_argument("input", type=str, help="Input file to process.")
    return p


def main():
    args = _get_parser().parse_args()

    cfg = laco.load(args.input)

    if args.output is None:
        laco.dump(cfg, sys.stdout)
        return

    with expath.open(args.output, "w") as f:
        laco.dump(cfg, f)


if __name__ == "__main__":
    main()
