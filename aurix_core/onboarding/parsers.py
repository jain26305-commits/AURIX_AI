"""Multi-format tabular parsers for CSV, XLSX, JSON, and Google Sheets datasets in Phase 11."""

import csv
import io
import json
from typing import Any, Dict, List, Literal, Optional, Tuple, Union, cast
import pandas as pd

from aurix_core.onboarding.contracts import SourceType
from aurix_core.onboarding.safety import FileSafetyException


XLS_LEGACY_MAGIC_BYTES = b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1"


class DataParser:
    """Parses multi-format tabular data into canonical dictionary records."""

    @staticmethod
    def _clean_dataframe(df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Standardizes DataFrame headers, drops entirely empty rows, and converts NaNs to None."""
        if df.empty:
            return [], []

        # 1. Clean column headers: strip whitespace, stringify
        clean_columns: List[str] = []
        for col in df.columns:
            col_str = str(col).strip()
            clean_columns.append(col_str if col_str else "unnamed_col")
        df.columns = pd.Index(clean_columns)

        # 2. Drop rows where all elements are NaN
        df = df.dropna(how="all")

        # 3. Replace NaN / NaT with None for clean Python JSON serialization
        df = df.where(pd.notnull(df), None)

        # 4. Convert records to typed list of dicts
        raw_list = cast(List[Dict[Any, Any]], df.to_dict(orient="records"))
        records_raw: List[Dict[str, Any]] = [{str(k): v for k, v in r.items()} for r in raw_list]
        return records_raw, clean_columns

    @classmethod
    def parse_csv(cls, content: bytes) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Parses CSV content supporting UTF-8, UTF-8-SIG, and Latin-1 with delimiter detection."""
        text: str
        for encoding in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                text = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise FileSafetyException("Unable to decode CSV file with supported encodings (UTF-8, Latin-1).")

        if not text.strip():
            return [], []

        # Auto-detect delimiter from sample
        sample = text[:4096]
        delimiter = ","
        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample, delimiters=",\t;|")
            delimiter = dialect.delimiter
        except Exception:
            delimiter = ","

        try:
            df = pd.read_csv(io.StringIO(text), sep=delimiter, engine="python", dtype=object)
        except Exception as e:
            raise FileSafetyException(f"Failed to parse CSV tabular content: {str(e)}")

        return cls._clean_dataframe(df)

    @classmethod
    def parse_xlsx(
        cls,
        content: bytes,
        sheet_name: Optional[Union[str, int]] = 0,
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Parses Excel spreadsheets (.xlsx, .xls) using the matching engine."""
        try:
            excel_io = io.BytesIO(content)
            engine: Literal["xlrd", "openpyxl"] = (
                "xlrd" if content.startswith(XLS_LEGACY_MAGIC_BYTES) else "openpyxl"
            )
            sheet_arg: Union[str, int] = 0 if sheet_name is None else sheet_name

            df_result = pd.read_excel(
                excel_io,
                sheet_name=sheet_arg,
                engine=engine,
                dtype=object,
            )
            if isinstance(df_result, dict):
                df: pd.DataFrame = next(iter(df_result.values())) if df_result else pd.DataFrame()
            else:
                df = df_result
        except Exception as e:
            raise FileSafetyException(f"Failed to parse Excel spreadsheet: {str(e)}")

        return cls._clean_dataframe(df)

    @classmethod
    def parse_json(cls, content: bytes) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Parses JSON content supporting lists of objects or wrapped object arrays."""
        try:
            text = content.decode("utf-8")
            data = json.loads(text)
        except Exception as e:
            raise FileSafetyException(f"Malformed JSON syntax: {str(e)}")

        raw_records: List[Any]
        if isinstance(data, list):
            raw_records = data
        elif isinstance(data, dict):
            for key in ("records", "data", "items", "rows"):
                if key in data and isinstance(data[key], list):
                    raw_records = data[key]
                    break
            else:
                raw_records = [data]
        else:
            raise FileSafetyException("JSON content must resolve to an array of objects or an object envelope.")

        dict_records: List[Dict[str, Any]] = [r for r in raw_records if isinstance(r, dict)]
        if not dict_records:
            return [], []

        df = pd.DataFrame(dict_records)
        return cls._clean_dataframe(df)

    @classmethod
    def parse_google_sheets(cls, content: bytes) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Parses exported Google Sheets tabular CSV or JSON export payloads."""
        try:
            return cls.parse_json(content)
        except FileSafetyException:
            return cls.parse_csv(content)

    @classmethod
    def parse(
        cls,
        source_type: SourceType,
        content: bytes,
        **kwargs: Any,
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Unified parsing dispatcher returning standardized records and extracted column names."""
        if source_type == SourceType.CSV:
            return cls.parse_csv(content)
        elif source_type == SourceType.XLSX:
            sheet = kwargs.get("sheet_name", 0)
            return cls.parse_xlsx(content, sheet_name=sheet)
        elif source_type == SourceType.JSON:
            return cls.parse_json(content)
        elif source_type == SourceType.GOOGLE_SHEETS:
            return cls.parse_google_sheets(content)
        elif source_type == SourceType.API:
            return cls.parse_json(content)
        else:
            raise FileSafetyException(f"Unsupported source type '{source_type}'.")