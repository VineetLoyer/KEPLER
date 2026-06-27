"""Download FEVER shared-task datasets."""

from __future__ import annotations

import argparse
import urllib.request
from pathlib import Path

FEVER_URLS = {
    "dev": "https://fever.ai/download/fever/shared_task_dev.jsonl",
    "test": "https://fever.ai/download/fever/shared_task_test.jsonl",
}


def download(split: str, output_dir: str = "evaluation/data") -> Path:
    url = FEVER_URLS[split]
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"fever_{split}.jsonl"
    urllib.request.urlretrieve(url, target)
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="Download FEVER dataset splits")
    parser.add_argument("--split", choices=["dev", "test"], default="dev")
    parser.add_argument("--output-dir", default="evaluation/data")
    args = parser.parse_args()
    path = download(args.split, args.output_dir)
    print(f"Downloaded {args.split} split to {path}")


if __name__ == "__main__":
    main()
