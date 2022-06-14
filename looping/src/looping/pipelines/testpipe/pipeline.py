from kedro.pipeline import Pipeline, node
from kedro.pipeline.modular_pipeline import pipeline as ModularPipeline

from .nodes import return_value
import pandas as pd

# pipeline to be modularized with different inputs
def simple_pipe() -> Pipeline:

    return Pipeline(
        [
            node(
                func = return_value,
                inputs = ['starter_point','value'],
                outputs = 'value_output',
                name = 'return_row'
            )
        ]
    )

simple_pipe_template = simple_pipe()

def looping_pipe(data:pd.DataFrame) -> Pipeline:

    auto_pipeline = Pipeline([])

    nums = data['a'].values

    for num in nums:

        #for namespace
        pipeline_key = f'pipeline_{num}'

        # malabarismo para retornar funcao
        def generate_param_node(param_to_return):
            def _dummy_return():
                return param_to_return
            return _dummy_return

        auto_pipeline += Pipeline([
            node(
                func = generate_param_node(num),
                inputs = None, 
                outputs = pipeline_key,
            )
        ])

        intermediary_pipeline = ModularPipeline(
            pipe = simple_pipe_template,
            inputs = {'starter_point':'starter_point',
                        'value': pipeline_key},
            # outputs = {'value_output': pipeline_key},
            namespace = pipeline_key
        )

        auto_pipeline = auto_pipeline + intermediary_pipeline

    return auto_pipeline









