"""
This is a boilerplate pipeline
generated using Kedro 0.18.0
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import make_predictions, report_accuracy, split_data
from .nodes import make_scatter_plot

def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                make_scatter_plot, 
                inputs = 'example_iris_data',
                outputs = "iris_scatter_plot@matplotlib",
                name = "make_scatter_plot"
            ),
            node(
                lambda x : x, 
                inputs = 'iris_scatter_plot@bytes',
                outputs = "iris_scatter_plot_base64",
                name = "make_scatter_base64"
            ),
            node(
                func=split_data,
                inputs=["example_iris_data", "parameters"],
                outputs=["X_train", "X_test", "y_train", "y_test"],
                name="split",
            ),
            node(
                func=make_predictions,
                inputs=["X_train", "X_test", "y_train"],
                outputs="y_pred",
                name="make_predictions",
            ),
            node(
                func=report_accuracy,
                inputs=["y_pred", "y_test"],
                outputs=None,
                name="report_accuracy",
            ),
        ]
    )
