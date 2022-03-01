# If Node is in initial capital letter (Node) it will blow up your kedro environment
from kedro.pipeline import Pipeline, node

from .nodes import preprocess_companies, preprocess_shuttles, create_master_table

def create_pipeline(**kwargs):
    return Pipeline(
        [
            node(
                func=preprocess_companies,
                inputs="companies",
                outputs="preprocessed_companies",
                name="preprocess_companies_node",
            ),
            node(
                func=preprocess_shuttles,
                inputs="shuttles",
                outputs="preprocessed_shuttles",
                name="preprocess_shuttles_node",
            ),
            node(
                func = create_master_table,
                inputs = ["preprocessed_shuttles","preprocessed_companies","reviews"],
                # be careful with outputs types, since here we could not have a list, since we actually return a dataframe
                outputs="master_table",
                name="master_table"
            )
        ]
    )