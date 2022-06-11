from kedro.pipeline import Pipeline

from ames.pipelines import dataprocessing_dev as dp
# from ames.pipelines import datascience as ds


def register_pipelines(**kwargs):
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