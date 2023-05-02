from kedro.pipeline import node, Pipeline

from .nodes import print_param

def create_pipeline(**kwargs):

    return Pipeline([

        node(
            func = print_param,
            inputs = 'params:x',
            outputs = None,
            name = 'node_context'
        )

    ])