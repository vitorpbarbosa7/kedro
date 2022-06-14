"""Project pipelines."""
from typing import Dict

from kedro.pipeline import Pipeline, pipeline

from looping.pipelines.testpipe import looping_pipe


import pandas as pd
datas = pd.read_csv('data/01_raw/data.csv')

auto_pipeline = looping_pipe(datas)


def register_pipelines() -> Dict[str, Pipeline]:
    """Register the project's pipelines.

    Returns:
        A mapping from a pipeline name to a ``Pipeline`` object.
    """

    return {"__default__": auto_pipeline}
