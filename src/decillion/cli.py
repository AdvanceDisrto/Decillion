from __future__ import annotations

import argparse

from .keys import generate_master_key


def main() -> None:
    parser = argparse.ArgumentParser(prog="decillion")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("generate-master-key", help="print a new URL-safe 256-bit master key")
    args = parser.parse_args()
    if args.command == "generate-master-key":
        print(generate_master_key())


if __name__ == "__main__":
    main()
