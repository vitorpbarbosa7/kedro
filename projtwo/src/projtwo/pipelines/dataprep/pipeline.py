from kedro.pipeline import Pipeline, node

from .nodes import splittarget

def create_pipeline(**kwargs):
    return Pipeline(
        [
            node(      
                func = splittarget,
                inputs = ["initialdata","parameters"],
                outputs = ["X_train","y_train"]
            ),
        ]
    )