#!/usr/bin/env python3
"""Quick-start demo entry point.

Run without arguments to generate all example layouts in examples/ into
output/. For full control over a single spec, use the CLI module instead:

    python -m architectural_design.cli generate --spec examples/studio_apartment.json --out output/
"""

from __future__ import annotations

import glob
import os
import sys

from architectural_design.cli import build_parser


def run_all_examples(out_dir: str = "output") -> int:
    spec_files = sorted(glob.glob(os.path.join(os.path.dirname(__file__), "examples", "*.json")))
    if not spec_files:
        print("No example specs found in examples/", file=sys.stderr)
        return 1

    parser = build_parser()
    for spec_path in spec_files:
        print(f"\n=== {os.path.basename(spec_path)} ===")
        args = parser.parse_args(["generate", "--spec", spec_path, "--out", out_dir])
        args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(run_all_examples())
