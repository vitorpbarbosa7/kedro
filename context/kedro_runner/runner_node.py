from kedro.pipeline import Pipeline, node
from kedro.io import DataCatalog
from kedro .runner.sequential_runner import SequentialRunner

from kedro.extras.datasets.pandas.csv_dataset import CSVDataSet
from kedro.extras.datasets.pandas.parquet_dataset import ParquetDataSet

import pandas as pd

# Sequential runner (ParallelRunner is also available)
runner = SequentialRunner()

def data_process(df:pd.DataFrame):
    return df**2

# general common every day kedro pipeline
pipeline = Pipeline([
    node(
        func = data_process,
        inputs = 'toy',
        outputs = 'toy_out',
        name = 'data_process'
    ),
])

# empty pipeline for us to start

catalog = DataCatalog(
    {
        'toy': CSVDataSet(filepath='toy.csv',
                          load_args=None,
                          save_args=None),
        'toy_out': CSVDataSet(filepath='toy_out.csv',
                              load_args=None,
                              save_args=None)
    }
)

runner.run(pipeline = pipeline, catalog = catalog)