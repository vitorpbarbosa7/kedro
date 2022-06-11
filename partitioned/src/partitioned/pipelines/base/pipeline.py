'''
This is a boilerplate pipeline
generated using Kedro 0.18.0
'''

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import partition_by_month
from .nodes import partition_by_month_incremental

def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=partition_by_month,
                inputs='ontime_2019',
                outputs='ontime_2019_by_day',
                name='partition_dataset',
            ),
            node(
                func = partition_by_month_incremental,
                inputs='ontime_2019',
                outputs='ontime_2019_incremental',
                name='incremental_dataset',                
            )
        ]
    )
