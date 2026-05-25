import pandas as pd


def group_average(frame: pd.DataFrame, group_column: str, value_column: str) -> pd.Series:
    return frame.groupby(group_column)[value_column].mean().sort_values(ascending=False)

