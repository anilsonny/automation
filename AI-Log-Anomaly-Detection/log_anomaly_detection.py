#!/usr/bin/env python3
"""
AI-Based System Log Anomaly Detection

Parses timestamped text logs and uses scikit-learn's Isolation Forest to flag
statistical outliers based on log severity and message length.

Expected input format:
    YYYY-MM-DD HH:MM:SS LEVEL MESSAGE

Example:
    2026-11-16 09:00:00 INFO System started successfully
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


LEVEL_SCORES = {
    "DEBUG": 0,
    "INFO": 1,
    "NOTICE": 1,
    "WARNING": 2,
    "WARN": 2,
    "ERROR": 3,
    "CRITICAL": 4,
    "FATAL": 4,
}


def parse_log_lines(lines: Iterable[str]) -> tuple[pd.DataFrame, int]:
    """Parse log lines; return parsed records and the number of skipped lines."""
    records: list[dict[str, object]] = []
    skipped = 0

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line:
            skipped += 1
            continue

        # Split into date, time, level, and the complete remaining message.
        parts = line.split(maxsplit=3)
        if len(parts) != 4:
            skipped += 1
            continue

        timestamp_text = f"{parts[0]} {parts[1]}"
        try:
            timestamp = pd.to_datetime(
                timestamp_text, format="%Y-%m-%d %H:%M:%S", errors="raise"
            )
        except (ValueError, TypeError):
            skipped += 1
            continue

        level = parts[2].upper()
        message = parts[3].strip()
        if not message:
            skipped += 1
            continue

        records.append(
            {
                "timestamp": timestamp,
                "level": level,
                "message": message,
                # Unknown levels receive 0 and remain visible in the report.
                "level_score": LEVEL_SCORES.get(level, 0),
                "message_length": len(message),
                "source_line": line_number,
            }
        )

    columns = [
        "timestamp", "level", "message", "level_score",
        "message_length", "source_line",
    ]
    return pd.DataFrame(records, columns=columns), skipped


def detect_anomalies(
    df: pd.DataFrame, contamination: str | float, random_state: int = 42
) -> pd.DataFrame:
    """Fit Isolation Forest and add prediction and readable classification."""
    if len(df) < 2:
        raise ValueError(
            "At least two valid log entries are required for anomaly detection."
        )

    features = df[["level_score", "message_length"]].astype(float)
    if not np.isfinite(features.to_numpy()).all():
        raise ValueError("The extracted feature values contain invalid numbers.")

    model = IsolationForest(
        contamination=contamination,
        random_state=random_state,
        n_estimators=200,
    )
    result = df.copy()
    result["anomaly_prediction"] = model.fit_predict(features)
    result["classification"] = result["anomaly_prediction"].map(
        {1: "Normal", -1: "Anomaly"}
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Detect statistically unusual system log entries using "
            "Isolation Forest."
        )
    )
    parser.add_argument(
        "-i", "--input",
        type=Path,
        default=Path("system_logs.txt"),
        help="Input log file (default: system_logs.txt).",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("output/anomalies.csv"),
        help="CSV report path (default: output/anomalies.csv).",
    )
    parser.add_argument(
        "-c", "--contamination",
        default="0.1",
        help=(
            "Expected anomaly proportion between 0 and 0.5, or 'auto' "
            "(default: 0.1)."
        ),
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Display all classified entries instead of anomalies only.",
    )
    return parser


def parse_contamination(value: str) -> str | float:
    if value.lower() == "auto":
        return "auto"
    try:
        numeric_value = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "contamination must be a number between 0 and 0.5, or 'auto'."
        ) from exc
    if not 0 < numeric_value <= 0.5:
        raise argparse.ArgumentTypeError(
            "contamination must be greater than 0 and no more than 0.5."
        )
    return numeric_value


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        contamination = parse_contamination(args.contamination)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    if not args.input.is_file():
        print(f"ERROR: Input file not found: {args.input}", file=sys.stderr)
        return 1

    try:
        with args.input.open("r", encoding="utf-8", errors="replace") as log_file:
            df, skipped_count = parse_log_lines(log_file)
    except OSError as exc:
        print(f"ERROR: Could not read input file: {exc}", file=sys.stderr)
        return 1

    if df.empty:
        print("ERROR: No valid log entries were found.", file=sys.stderr)
        return 1

    try:
        results = detect_anomalies(df, contamination)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    anomalies = results[results["anomaly_prediction"] == -1].copy()
    report = results if args.show_all else anomalies

    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        report.to_csv(args.output, index=False)
    except OSError as exc:
        print(f"ERROR: Could not write CSV report: {exc}", file=sys.stderr)
        return 1

    print("\nAI-Based System Log Anomaly Detection")
    print("-------------------------------------")
    print(f"Input file       : {args.input}")
    print(f"Valid entries    : {len(results)}")
    print(f"Skipped lines    : {skipped_count}")
    print(f"Detected anomalies: {len(anomalies)}")
    print(f"CSV report       : {args.output}")

    if args.show_all:
        display_df = results
    else:
        display_df = anomalies

    if display_df.empty:
        print("\nNo anomalies detected.")
    else:
        print("\nDetected Anomalies:" if not args.show_all else "\nClassified Log Entries:")
        print(
            display_df[
                ["timestamp", "level", "message", "classification"]
            ].to_string(index=False)
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
