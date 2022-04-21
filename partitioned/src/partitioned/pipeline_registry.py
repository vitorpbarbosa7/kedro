"""Project pipelines."""
from typing import Dict

from kedro.pipeline import Pipeline

from .pipelines import base as b

def register_pipelines() -> Dict[str, Pipeline]:
    """Register the project's pipelines.

    Returns:
        A mapping from a pipeline name to a ``Pipeline`` object.
    """

    base_pipeline = b.create_pipeline()

    return {
        "__default__": base_pipeline
        }
