from __future__ import annotations

import argparse
import csv
import math
import statistics
from pathlib import Path


NEAR_FALL_START_LABEL = 2
NEAR_FALL_END_LABEL = 3


def load_labels_file(path: str | Path) -> list[dict[str, int | float]]:
	"""Load a label CSV with columns: label_id, time_ms, event_type."""
	rows: list[dict[str, int | float]] = []
	with open(path, "r", newline="", encoding="utf-8") as f:
		reader = csv.reader(f)
		for row in reader:
			if len(row) < 3:
				continue
			rows.append(
				{
					"label_id": int(row[0]),
					"time_ms": float(row[1]),
					"event_type": int(row[2]),
				}
			)
	return rows


def extract_near_fall_periods(labels_df: list[dict[str, int | float]], source: str) -> list[dict]:
	"""Extract near-fall periods as start/end pairs from one labels DataFrame."""
	periods: list[dict] = []
	if not labels_df:
		return periods

	df = sorted(labels_df, key=lambda r: float(r["time_ms"]))
	open_start_ms: float | None = None

	for row in df:
		label_id = int(row["label_id"])
		time_ms = float(row["time_ms"])

		if label_id == NEAR_FALL_START_LABEL:
			open_start_ms = time_ms
			continue

		if label_id == NEAR_FALL_END_LABEL and open_start_ms is not None and time_ms >= open_start_ms:
			duration_ms = time_ms - open_start_ms
			periods.append(
				{
					"source": source,
					"start_ms": open_start_ms,
					"end_ms": time_ms,
					"duration_ms": duration_ms,
					"duration_s": duration_ms / 1000.0,
				}
			)
			open_start_ms = None

	return periods


def summarize_periods(periods_df: list[dict]) -> dict[str, float | int]:
	"""Compute count and duration statistics for near-fall periods."""
	if not periods_df:
		return {
			"count": 0,
			"total_duration_s": 0.0,
			"mean_s": math.nan,
			"median_s": math.nan,
			"q1_s": math.nan,
			"q3_s": math.nan,
			"iqr_s": math.nan,
			"std_s": math.nan,
		}

	durations = sorted(float(row["duration_s"]) for row in periods_df)

	def _percentile(sorted_values: list[float], p: float) -> float:
		if not sorted_values:
			return math.nan
		if len(sorted_values) == 1:
			return sorted_values[0]
		rank = (len(sorted_values) - 1) * p
		lo = math.floor(rank)
		hi = math.ceil(rank)
		if lo == hi:
			return sorted_values[lo]
		weight = rank - lo
		return sorted_values[lo] * (1.0 - weight) + sorted_values[hi] * weight

	q1 = _percentile(durations, 0.25)
	q3 = _percentile(durations, 0.75)
	return {
		"count": int(len(durations)),
		"total_duration_s": float(sum(durations)),
		"mean_s": float(statistics.fmean(durations)),
		"median_s": float(statistics.median(durations)),
		"q1_s": float(q1),
		"q3_s": float(q3),
		"iqr_s": float(q3 - q1),
		"std_s": float(statistics.pstdev(durations)),
	}


def analyze_near_falls(labels_dir: str | Path = "data") -> tuple[list[dict], dict[str, float | int]]:
	"""
	Analyze all labels CSV files in a directory.

	Expected filename pattern: labels_*.csv
	"""
	labels_dir = Path(labels_dir)
	label_files = sorted(labels_dir.glob("labels_*.csv"))

	all_periods: list[dict] = []
	for file_path in label_files:
		labels_df = load_labels_file(file_path)
		all_periods.extend(extract_near_fall_periods(labels_df, source=file_path.name))

	summary = summarize_periods(all_periods)
	return all_periods, summary


def _fmt(v: float | int) -> str:
	if isinstance(v, int):
		return str(v)
	if isinstance(v, float) and math.isnan(v):
		return "NaN"
	return f"{float(v):.4f}"


def main() -> None:
	parser = argparse.ArgumentParser(description="Near-fall period statistics from labels CSV files")
	parser.add_argument(
		"--labels-dir",
		default="data",
		help="Directory containing labels_*.csv files (default: data)",
	)
	parser.add_argument(
		"--save-periods",
		default="",
		help="Optional path to save extracted near-fall periods as CSV",
	)
	args = parser.parse_args()

	periods, summary = analyze_near_falls(args.labels_dir)

	print("Near-fall summary")
	print("-----------------")
	print(f"total near-fall periods: {_fmt(summary['count'])}")
	print(f"total near-fall duration (s): {_fmt(summary['total_duration_s'])}")
	print(f"average period (s): {_fmt(summary['mean_s'])}")
	print(f"median period (s): {_fmt(summary['median_s'])}")
	print(f"Q1 period (s): {_fmt(summary['q1_s'])}")
	print(f"Q3 period (s): {_fmt(summary['q3_s'])}")
	print(f"IQR period (s): {_fmt(summary['iqr_s'])}")
	print(f"standard deviation (s): {_fmt(summary['std_s'])}")

	if args.save_periods:
		out_path = Path(args.save_periods)
		with open(out_path, "w", newline="", encoding="utf-8") as f:
			writer = csv.DictWriter(
				f,
				fieldnames=["source", "start_ms", "end_ms", "duration_ms", "duration_s"],
			)
			writer.writeheader()
			writer.writerows(periods)
		print(f"saved periods to: {out_path}")


if __name__ == "__main__":
	main()

