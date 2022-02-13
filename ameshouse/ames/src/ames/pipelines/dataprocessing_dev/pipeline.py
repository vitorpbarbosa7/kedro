# If Node is in initial capital letter (Node) it will blow up your kedro environment
# If Node is in initial capital letter (Node) it will blow up your kedro environment
from kedro.pipeline import Pipeline, node



from .nodes import split_target, train_test_split, concat_df

def create_pipeline(**kwargs):
    return Pipeline(
        [
            node(
                func=split_target
                ,inputs=["alldata","parameters"]
                ,outputs=["X_dev","y_dev"]
                ,name="split_target_node_dev"
            )
            ,node(
                func=train_test_split
                ,inputs=["X_dev", "y_dev", "parameters"]
                ,outputs=["X_train","X_test","y_train","y_test"]
                ,name="split_train_test_node_dev"
            )
            ,node(
                func=concat_df
                ,inputs=["X_train","X_test","y_train","y_test"]
                ,outputs=["train","test"]
                ,name="train_test_datasets"
            )
        ]
    )