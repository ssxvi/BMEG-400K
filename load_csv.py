import pandas as pd
from pathlib import Path

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


# path to your csv
path1 = "data/data_P9853_T16_ITR_ECG.csv"
path2 = "data/data_P9853_T16_ITR_ECG.csv"
path3 = "data/data_P9853_T16_ITR_ECG.csv"
df1 = load_csv(path1)
df2 = load_csv(path2)
df3 = load_csv(path3)
print(df1.head())
print(df2.head())
print(df3.head())
