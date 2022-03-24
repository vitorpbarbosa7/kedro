# If Node is in initial capital letter (Node) it will blow up your kedro environment
# If Node is in initial capital letter (Node) it will blow up your kedro environment
from kedro.pipeline import Pipeline, node

from .nodes import (
    concat_df,
    drop_covariates,
    join_num_cat,
    process_categoricals,
    process_numeric,
    split_target,
    train_test_split,
)


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
            ,node(
                func=drop_covariates
                ,inputs=["train","parameters"]
                ,outputs="train_dropped"
                ,name="Drop_Irrelevant_Covariates-Train"
            )
            ,node(
                func=process_categoricals
                ,inputs=["train_dropped","parameters"]
                ,outputs="train_categorical"
                ,name="Feature_Engineering_Categoricals-Train"
            )
            ,node(
                func=process_numeric
                ,inputs=["train_dropped","parameters"]
                ,outputs="train_numeric"
                ,name="Feature_Engineering_Numericals-Train"
            )
            ,node(
                func=drop_covariates
                ,inputs=["test","parameters"]
                ,outputs="test_dropped"
                ,name="Drop_Irrelevant_Covariates-Test"
            )
            ,node(
                func=process_categoricals
                ,inputs=["test_dropped","parameters"]
                ,outputs="test_categorical"
                ,name="Feature_Engineering_Categoricals-Test"
            )
            ,node(
                func=process_numeric
                ,inputs=["test_dropped","parameters"]
                ,outputs="test_numeric"
                ,name="Feature_Engineering_Numericals-Test"
            )
            ,node(
                func=join_num_cat
                ,inputs=["train_numeric","train_categorical"]
                ,outputs="train_joined_num_cat"
                ,name="Join_Categorical_and_Numerical-Train"
            )
            ,node(
                func=join_num_cat
                ,inputs=["test_numeric","test_categorical"]
                ,outputs="test_joined_num_cat"
                ,name="Join_Categorical_and_Numerical-Test"
            )
        ]
    )
