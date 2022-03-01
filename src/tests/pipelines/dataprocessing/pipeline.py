# If Node is in initial capital letter (Node) it will blow up your kedro environment
from kedro.pipeline import Pipeline, node

from .nodes import split_target

def create_pipeline(**kwargs):
    return Pipeline(
        [
            node(
                func=split_target
                ,inputs="alldata"
                ,outputs=["X_dev","y_dev"]
               ,name="split_target_node"
            )
            # ,node(
            #     func=preprocess_shuttles,
            #     inputs="shuttles",
            #     outputs="preprocessed_shuttles",
            #     name="preprocess_shuttles_node",
            # ),
            # ,node(
            #     func = create_master_table,
            #     inputs = ["preprocessed_shuttles","preprocessed_companies","reviews"],
            #     # be careful with outputs types, since here we could not have a list, since we actually return a dataframe
            #     outputs="master_table",
            #     name="master_table"
            # )
        ]
    )