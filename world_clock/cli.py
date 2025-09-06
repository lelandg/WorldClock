from __future__ import annotations

import argparse
import time
from datetime import datetime
from typing import List

from .time_utils import get_timezones_for_input, now_in_zone, format_time


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="World Clock CLI (country codes or time zones)")
    p.add_argument("codes", nargs="+", help="Country codes (US IN GB), IANA zones (America/Chicago), or abbreviations (CST)")
    p.add_argument("--one-per-country", action="store_true", help="Show only one representative timezone per country (when country codes are used)")
    p.add_argument("--no-seconds", action="store_true", help="Hide seconds in display")
    p.add_argument("--interval", type=float, default=1.0, help="Refresh interval in seconds (default: 1.0)")
    return p.parse_args(argv)


def run_cli(args: argparse.Namespace) -> int:
    # Build list of (country, zone)
    entries: list[tuple[str, str]] = []
    for code in args.codes:
        zones = get_timezones_for_input(code, include_all=not args.one_per_country)
        if not zones:
            print(f"Warning: No time zones found for input '{code}'")
            continue
        for z in zones:
            entries.append((code, z))

    if not entries:
        print("No valid inputs provided.")
        return 2

    try:
        while True:
            now_lines = []
            for code, zone in entries:
                try:
                    dt = now_in_zone(zone)
                    now_lines.append(f"{code} | {zone:<30} | {format_time(dt, show_seconds=not args.no_seconds)}")
                except Exception as e:
                    print(str(e))
                    return 3
            # Clear screen area then print
            print("\x1b[2J\x1b[H", end="")  # ANSI clear screen + home
            print("\n".join(now_lines))
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("Exiting.")
        return 0


def main():
    args = parse_args()
    raise SystemExit(run_cli(args))


if __name__ == "__main__":
    main()
