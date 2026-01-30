#load and plot CSV files

import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

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


def plot_csv(path: str | Path, max_rows: int | None = 50000, figsize: tuple = (10, 6)) -> None:
    # Load a data CSV and plot
    df = load_csv(path)
    if max_rows and len(df) > max_rows:
        df = df.iloc[:max_rows]
    sensor = get_sensor(path)
    t = df["time_s"]

    if sensor in ("ECG", "GSS"):
        plt.figure(figsize=figsize)
        plt.plot(t, df["voltage_V"])
        plt.xlabel("Time (s)")
        plt.ylabel("Voltage (V)")
        plt.title(f"{sensor} – {Path(path).name}")
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
        fig.suptitle(f"{sensor} IMU – {Path(path).name}")
        plt.tight_layout()
        plt.show()

    else: #??? 
        print("WTF are you doing")
        df.plot(x="time_s", figsize=figsize, title=str(path))
        plt.xlabel("Time (s)")
        plt.tight_layout()
        plt.show()


# graph one or more CSVs
if __name__ == "__main__":
    paths = [
        "data/data_P9853_T16_ITR_ECG.csv",
        "data/data_P1960_T01_Slip_Back.csv",
    ]
    for p in paths:
        plot_csv(p, max_rows=50000)  # set max_rows=None to plot full file
