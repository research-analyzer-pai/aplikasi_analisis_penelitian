"""Contoh extension yang aman: tidak dipanggil otomatis oleh aplikasi."""
import pandas as pd

def summarize_missingness(data: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(data, pd.DataFrame):
        raise TypeError("data harus berupa pandas DataFrame")
    return pd.DataFrame({
        "variable": data.columns,
        "missing_n": data.isna().sum().values,
        "missing_percent": (data.isna().mean().values * 100).round(2),
    })
