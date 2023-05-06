from kedro.pipeline import Pipeline, node
from kedro.io import DataCatalog
from kedro .runner.sequential_runner import SequentialRunner


from kedro.extras.datasets.pandas.csv_dataset import CSVDataSet
from kedro.extras.datasets.pandas.parquet_dataset import ParquetDataSet

# Sequential runner (ParallelRunner is also available)
runner = SequentialRunner()

# general common every day kedro pipeline
pipeline = Pipeline([
    node(lambda: [print(x**2) for x in range(4)], None, 'bar'),
])

# empty pipeline for us to start
catalog = DataCatalog()

runner.run(pipeline = pipeline, catalog = catalog)