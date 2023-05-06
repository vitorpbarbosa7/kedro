from kedro.pipeline import Pipeline, node
from kedro.io import DataCatalog
from kedro .runner.sequential_runner import SequentialRunner

from kedro.extras.datasets.pandas.csv_dataset import CSVDataSet
from kedro.extras.datasets.pandas.parquet_dataset import ParquetDataSet

import pandas as pd
import yaml

with open('conf/credentials.yml', 'r') as file:
    credentials = yaml.safe_load(file)

print(credentials)

# Sequential runner (ParallelRunner is also available)
runner = SequentialRunner()

def data_process(df:pd.DataFrame):
    print(df)

# general common every day kedro pipeline
pipeline = Pipeline([
    node(
        func = data_process,
        inputs = 'iris',
        outputs = None,
        name = 'data_process'
    ),
])

# empty pipeline for us to start

config = {
        "iris": {
            "type": "pandas.CSVDataSet",
            "filepath": "s3://vpb-spark-bucket/iris.csv",
            "credentials":"iris_credentials"
        }
    }

catalog = DataCatalog.from_config(config, credentials)

runner.run(pipeline = pipeline, catalog = catalog)