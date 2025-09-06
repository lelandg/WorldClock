from __future__ import annotations

import argparse
import sys

from .cli import run_cli, parse_args as parse_cli_args
# GUI import deferred to runtime to avoid requiring PySide6 for CLI usage


def main():
    parser = argparse.ArgumentParser(description="World Clock - CLI and GUI")
    parser.add_argument("codes", nargs="*", help="Country codes or time zones for CLI mode")
    parser.add_argument("--gui", action="store_true", help="Run GUI instead of CLI")
    parser.add_argument("--one-per-country", action="store_true")
    parser.add_argument("--no-seconds", action="store_true")
    parser.add_argument("--interval", type=float, default=1.0)
    args, unknown = parser.parse_known_args()

    if args.gui:
        from . import gui as _gui
        _gui.run_gui()
    else:
        # Reuse CLI implementation with parsed args
        from .cli import parse_args
        cli_args = []
        if args.one_per_country:
            cli_args.append("--one-per-country")
        if args.no_seconds:
            cli_args.append("--no-seconds")
        if args.interval != 1.0:
            cli_args += ["--interval", str(args.interval)]
        cli_args += args.codes
        ns = parse_args(cli_args)
        raise SystemExit(run_cli(ns))


if __name__ == "__main__":
    main()
