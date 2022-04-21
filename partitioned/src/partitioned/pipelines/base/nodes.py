from typing import Dict
import pandas as pd

def partition_by_day(df:pd.DataFrame) -> Dict[str, pd.DataFrame]:
    parts = {}

    for day_of_month in df['DAY_OF_MONTH'].unique():
        parts[f'DAY_OF_MONTH = {day_of_month}'] = df[df['DAY_OF_MONTH'] == day_of_month]  

    return parts