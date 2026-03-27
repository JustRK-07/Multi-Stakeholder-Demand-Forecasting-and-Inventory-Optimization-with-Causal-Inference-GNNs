from __future__ import annotations

import argparse
from pathlib import Path

from .forecast_model import train_and_save, training_summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the RetailCast forecast model.")
    parser.add_argument("--data-path", type=str, default=None, help="Optional CSV path to train on.")
    args = parser.parse_args()

    train_and_save(Path(args.data_path) if args.data_path else None)
    print(training_summary())


if __name__ == "__main__":
    main()
