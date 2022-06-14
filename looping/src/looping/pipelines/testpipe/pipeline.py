from kedro.pipeline import Pipeline, node
from kedro.pipeline.modular_pipeline import pipeline as ModularPipeline

from .nodes import entry_node
from .nodes import return_value

# pipeline to be modularized with different inputs
def simple_pipe() -> Pipeline:

    return Pipeline(
        [
            node(
                func = return_value,
                inputs = ['entry_point','value'],
                outputs = 'value_output',
                name = 'return_row'
            )
        ]
    )

simple_pipe_template = simple_pipe()

def looping_pipe() -> Pipeline:

    auto_pipeline = Pipeline([])

    auto_pipeline += Pipeline([
            node(
                func = entry_node,
                inputs = 'starter_point',
                outputs = 'entry_point',
                name = 'entry_point'
            )
        ])

    for num in range(3):

        #for namespace
        pipeline_key = f'{num}'

        intermediary_pipeline = ModularPipeline(
            pipe = simple_pipe_template,
            inputs = {'entry_point':'entry_point',
                        'value': pipeline_key},
            namespace = pipeline_key
        )

        auto_pipeline = auto_pipeline + intermediary_pipeline

    return auto_pipeline









