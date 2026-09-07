import pandas as pd


def Transform_price(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        raise ValueError("DataFrame is empty")

    col_required = [
        "time",
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]
    for col in col_required:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")
            
    df = df.copy()
    df =  df.drop_duplicates()
    df = df.dropna()
    df = df.sort_values("time")
    return df
