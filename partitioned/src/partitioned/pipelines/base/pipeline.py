'''
This is a boilerplate pipeline
generated using Kedro 0.18.0
'''

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import partition_by_day

def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=partition_by_day,
                inputs='ontime_2019',
                outputs='ontime_2019_by_day',
                name='partition_dataset',
            ),
        ]
    )
