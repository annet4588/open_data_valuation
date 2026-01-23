import pandas as pd
from dataclasses import dataclass


# Class to compute dataset quality metrics
@dataclass
class DatasetQualityValuator:
    df: pd.DataFrame

    def score(self) -> dict:
        if self.df.empty:
            return {
                "rows": 0,
                "cols": 0,
                "missing_cell_values": 0,
                "missing_ratio": 0.0,
                "duplicates": 0,
                "empty_columns": 0,
            }

        rows = int(len(self.df))
        cols = int(len(self.df.columns))
        total_cells = int(self.df.size)

        # Missing values
        missing_cell_values = int(self.df.isna().sum().sum())
        missing_ratio = float(missing_cell_values / total_cells) if total_cells else 0.0

        # Duplicate rows
        duplicates = int(self.df.duplicated().sum())

        # Empty columns
        empty_columns = int(sum(
            self.df[col].replace(r"^\s*$", pd.NA, regex=True).isna().all()
            for col in self.df.columns
        ))

        return {
            "rows": rows,
            "cols": cols,
            "missing_cell_values": missing_cell_values,
            "missing_ratio": round(missing_ratio, 4),
            "duplicates": duplicates,
            "empty_columns": empty_columns,
        }
