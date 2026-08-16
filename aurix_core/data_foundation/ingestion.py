import pandas as pd


class DataIngestionEngine:
    """Handles file ingestion from CSV, Parquet, and Excel into pandas DataFrames."""

    @staticmethod
    def ingest_file(file_path: str) -> pd.DataFrame:
        if file_path.endswith(".csv"):
            return pd.read_csv(file_path)
        elif file_path.endswith(".parquet"):
            return pd.read_parquet(file_path)
        elif file_path.endswith(".xlsx") or file_path.endswith(".xls"):
            return pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format for ingestion: {file_path}")
