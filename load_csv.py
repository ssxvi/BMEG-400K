#load and plot CSV files

import re
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt


def _title_to_filename(title: str, ext: str = ".png") -> str:
    """Turn plot title into a safe default save filename."""
    s = title.replace(" – ", "_").replace(" ", "_").replace(".csv", "")
    s = re.sub(r"[^\w.\-]", "_", s).rstrip("_")
    return s + ext if not s.endswith(ext) else s

# Headers by sensor type (from filename: data_P*_T*_*_Back.csv etc.)
IMU_HEADERS = [
    "time_s",
    "acc_x_ms2", "acc_y_ms2", "acc_z_ms2",
    "angvel_x_degs", "angvel_y_degs", "angvel_z_degs",
]  # Back, Left_Thigh, Right_Thigh: time, triaxial accel (m/s²), triaxial angular vel (deg/s)
ECG_HEADERS = ["time_s", "voltage_V"]   # time, single voltage channel (V)
GSS_HEADERS = ["time_s", "voltage_V"]   # time, skin conductance–related voltage (V)

SENSOR_HEADERS = {
    "Back": IMU_HEADERS,
    "Left_Thigh": IMU_HEADERS,
    "Right_Thigh": IMU_HEADERS,
    "ECG": ECG_HEADERS,
    "GSS": GSS_HEADERS,
}


def get_headers(path: str | Path) -> list[str]:
    """Get column names from filename. Example: data_P1960_T01_Slip_ECG.csv -> ECG -> time_s, voltage_V."""
    name = Path(path).stem  # e.g. data_P1960_T01_Slip_ECG or data_P1960_T04_Hit_Right_Thigh
    for sensor in ("Right_Thigh", "Left_Thigh", "Back", "ECG", "GSS"):
        if name.endswith("_" + sensor):
            return SENSOR_HEADERS[sensor]
    return None


def load_csv(path: str | Path) -> pd.DataFrame:
    """Load a data CSV with headers based on sensor type."""
    headers = get_headers(path)
    kwargs = {"header": None}
    if headers is not None:
        kwargs["names"] = headers
    return pd.read_csv(path, **kwargs)


def get_sensor(path: str | Path) -> str | None:
    # Get sensor name from filename.
    name = Path(path).stem
    for sensor in ("Right_Thigh", "Left_Thigh", "Back", "ECG", "GSS"):
        if name.endswith("_" + sensor):
            return sensor
    return None


def get_participant_activity(path: str | Path) -> tuple[str, str] | None:
    # FIND LABEL FILE data_P1960_T01_Slip_ECG.csv -> (P1960, Slip). Returns None if pattern doesn't match
    name = Path(path).stem
    parts = name.split("_")
    if len(parts) >= 4 and parts[0] == "data": #dont look at label files
        return parts[1], parts[3]  # participant, activity
    return None


# Fall/near-fall label timings: col1 = timing label, col2 = time (ms), col3 = event type (1=near-fall, 4=fall)
LABEL_NAMES = {
    1: "Movement start",
    2: "Near-fall start",
    3: "Near-fall end",
    4: "Fall",
    5: "End",
}
LABEL_COLORS = {1: "green", 2: "orange", 3: "blue", 4: "red", 5: "purple"}


def load_labels_for_data(data_path: str | Path) -> pd.DataFrame | None:
    """Load labels CSV for the same participant and activity as the data file. Returns DataFrame with label_id, time_ms, event_type, time_s, label_name; or None if no file."""
    pair = get_participant_activity(data_path)
    if not pair:
        return None
    participant, activity = pair
    data_path = Path(data_path)
    labels_path = data_path.parent / f"labels_{participant}_{activity}.csv"
    if not labels_path.exists():
        return None
    df = pd.read_csv(labels_path, header=None, names=["label_id", "time_ms", "event_type"])
    df["time_s"] = df["time_ms"] / 1000.0
    df["label_name"] = df["label_id"].map(LABEL_NAMES)
    return df


def _add_label_lines(axes, labels_df: pd.DataFrame, t_min: float, t_max: float) -> None:
    """Draw vertical lines at label times on the given axis/axes. axes can be a single Axes or list of Axes."""
    if axes is None or labels_df is None or labels_df.empty:
        return
    ax_list = np.atleast_1d(axes).flatten().tolist()
    drawn = set()
    for _, row in labels_df.iterrows():
        ts = row["time_s"]
        if not (t_min <= ts <= t_max):
            continue
        lid = row["label_id"]
        color = LABEL_COLORS.get(lid, "gray")
        first_occurrence = lid not in drawn
        if first_occurrence:
            drawn.add(lid)
        for i, ax in enumerate(ax_list):
            # Only add legend label on last axis, and only first time we see each label_id
            label = row["label_name"] if (first_occurrence and i == len(ax_list) - 1) else None
            ax.axvline(ts, color=color, alpha=0.7, linestyle="--", linewidth=1, label=label)
            
    # Dedupe legend on last axis only (event labels)
    if ax_list:
        ax = ax_list[-1]
        handles, leg_labels = ax.get_legend_handles_labels()
        by_label = dict(zip(leg_labels, handles))
        # Keep only event-label entries (from our axvlines); drop empty string
        by_label = {k: v for k, v in by_label.items() if k}
        if by_label:
            ax.legend(by_label.values(), by_label.keys(), loc="upper right", fontsize=7)


def plot_csv(path: str | Path, max_rows: int | None = 500000, figsize: tuple = (10, 6)) -> None:
    # Load a data CSV and plot
    df = load_csv(path)
    if max_rows and len(df) > max_rows:
        df = df.iloc[:max_rows]
    sensor = get_sensor(path)
    t = df["time_s"]

    if sensor in ("ECG", "GSS"):
        v = df["voltage_V"].copy()
        # Treat 0 (and near-zero) as dropout so they don't draw as spikes
        v[v == 0] = np.nan
        plt.figure(figsize=figsize)
        plt.plot(t, v)
        labels_df = load_labels_for_data(path)
        if labels_df is not None:
            _add_label_lines(plt.gca(), labels_df, float(t.min()), float(t.max()))
        plt.xlabel("Time (s)")
        plt.ylabel("Voltage (V)")
        title = f"{sensor} – {Path(path).name}"
        plt.title(title)
        fig = plt.gcf()
        fig.canvas.get_default_filename = lambda: _title_to_filename(title)
        plt.tight_layout()
        plt.show()

    elif sensor in ("Back", "Left_Thigh", "Right_Thigh"):
        fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=figsize)
        ax1.plot(t, df["acc_x_ms2"], label="x")
        ax1.plot(t, df["acc_y_ms2"], label="y")
        ax1.plot(t, df["acc_z_ms2"], label="z")
        ax1.set_ylabel("Accel (m/s²)")
        ax1.legend(loc="upper right")
        ax1.set_title("Linear acceleration")
        ax2.plot(t, df["angvel_x_degs"], label="x")
        ax2.plot(t, df["angvel_y_degs"], label="y")
        ax2.plot(t, df["angvel_z_degs"], label="z")
        ax2.set_ylabel("Angular vel (deg/s)")
        ax2.set_xlabel("Time (s)")
        ax2.legend(loc="upper right")
        ax2.set_title("Angular velocity")
        labels_df = load_labels_for_data(path)
        if labels_df is not None:
            _add_label_lines([ax1, ax2], labels_df, float(t.min()), float(t.max()))
        title = f"{sensor} IMU – {Path(path).name}"
        fig.suptitle(title)
        fig.canvas.get_default_filename = lambda: _title_to_filename(title)
        plt.tight_layout()
        plt.show()

    else: #??? 
        print("WTF are you doing")
        title = str(path)
        df.plot(x="time_s", figsize=figsize, title=title)
        plt.gcf().canvas.get_default_filename = lambda: _title_to_filename(title)
        plt.xlabel("Time (s)")
        plt.tight_layout()
        plt.show()


# graph one or more CSVs
if __name__ == "__main__":
    paths = [
        "data/data_P2070_T16_Trip_ECG.csv",
        "data/data_P2070_T14_LOS_ECG.csv",
        "data/data_P2070_T05_Sit_ECG.csv",
        "data/data_P2070_T16_Trip_GSS.csv",

    ]
    for p in paths:
        plot_csv(p, max_rows=120000)  # set max_rows=None to plot full file
