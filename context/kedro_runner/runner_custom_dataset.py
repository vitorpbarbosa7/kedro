from kedro.pipeline import Pipeline, node
from kedro.io import DataCatalog
from kedro .runner.sequential_runner import SequentialRunner

import pandas as pd

from kedro.io import AbstractDataSet

class MyParquetDataSet(AbstractDataSet):

    def __init__(self, filepath):
        self._filepath = filepath

    def _load(self):
        return pd.read_parquet(self._filepath)
    
    def _save(self, data):
        data.to_parquet(self._filepath)

    def _describe(self):
        return {
            "filepath": self._filepath
        }


# Sequential runner (ParallelRunner is also available)
runner = SequentialRunner()

def data_process(df:pd.DataFrame):
    return df**2

# general common every day kedro pipeline
pipeline = Pipeline([
    node(
        func = data_process,
        inputs = 'custom_dataset',
        outputs = 'custom_dataset_out',
        name = 'data_process'
    ),
])

# empty pipeline for us to start

catalog = DataCatalog(
    {
        'custom_dataset' : MyParquetDataSet(filepath='toy.parquet'),
        'custom_dataset_out' : MyParquetDataSet(filepath='toy_out.parquet'),
    }
)

runner.run(pipeline = pipeline, catalog = catalog)



# >>>>>> Pickle example to see that the logic is the same

    # def _load(self) -> Any:
    #     load_path = get_filepath_str(self._get_load_path(), self._protocol)

    #     with self._fs.open(load_path, **self._fs_open_args_load) as fs_file:
    #         imported_backend = importlib.import_module(self._backend)
    #         return imported_backend.load(fs_file, **self._load_args)  # type: ignore

    # def _save(self, data: Any) -> None:
    #     save_path = get_filepath_str(self._get_save_path(), self._protocol)

    #     with self._fs.open(save_path, **self._fs_open_args_save) as fs_file:
    #         try:
    #             imported_backend = importlib.import_module(self._backend)
    #             imported_backend.dump(data, fs_file, **self._save_args)  # type: ignore
    #         except Exception as exc:
    #             raise DataSetError(
    #                 f"{data.__class__} was not serialised due to: {exc}"
    #             ) from exc

    #     self._invalidate_cache()