"""Project pipelines."""
from typing import Dict

from kedro.pipeline import Pipeline, pipeline

from looping.pipelines.testpipe import looping_pipe

auto_pipeline = looping_pipe()


def register_pipelines() -> Dict[str, Pipeline]:
    """Register the project's pipelines.

    Returns:
        A mapping from a pipeline name to a ``Pipeline`` object.
    """

    return {"__default__": auto_pipeline}
