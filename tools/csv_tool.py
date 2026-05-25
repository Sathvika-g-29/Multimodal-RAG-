from pathlib import Path

import pandas as pd


def load_csv(csv_path: str | Path) -> pd.DataFrame:
    return pd.read_csv(csv_path)

