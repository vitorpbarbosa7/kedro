
# from typing import Dict

from kedro.pipeline import Pipeline

from tests.pipelines import dataprocessing as dp
# from ames.pipelines import datascience as ds

def create_pipelines(**kwargs):
    """Create the project's pipeline.

    Args:
        kwargs: Ignore any additional arguments added in the future.

    Returns:
        A mapping from a pipeline name to a ``Pipeline`` object.

    """

    dataprocessing_pipeline = dp.create_pipeline()
    # datascience_pipeline = ds.create_pipeline()

    return {
            "__default__": dataprocessing_pipeline,
            "dp": dataprocessing_pipeline 
            # ,"ds": datascience_pipeline
            }