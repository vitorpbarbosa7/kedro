from kedro.io import AbstractDataSet

import pandas as pd

class MyParquetDataSet(AbstractDataSet):

    def __init__(self, filepath):
        self._filepath = filepath

    def _load(self):
        return pd.read_parquet(self._filepath)
    
    def _save(self):
        pd.to_parquet(self._filepath)
