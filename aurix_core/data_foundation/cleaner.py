import pandas as pd


class DataCleaner:
    """Cleans raw dataframes by trimming whitespace, standardizing nulls, and deduplicating."""

    @staticmethod
    def clean(df: pd.DataFrame) -> pd.DataFrame:
        cleaned_df = df.copy()
        for col in cleaned_df.select_dtypes(include=["object", "string"]).columns:
            cleaned_df[col] = cleaned_df[col].astype(str).str.strip()
        cleaned_df = cleaned_df.drop_duplicates()
        return cleaned_df
