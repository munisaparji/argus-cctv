import argparse
from pathlib import Path

from argus.train.detector import train

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("artifacts/checkpoints/detector.pt"))
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()
    train(args.index, args.output, args.epochs, args.device)
