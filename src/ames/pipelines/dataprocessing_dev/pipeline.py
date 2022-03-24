# If Node is in initial capital letter (Node) it will blow up your kedro environment
# If Node is in initial capital letter (Node) it will blow up your kedro environment
from kedro.pipeline import Pipeline, node

from .nodes import drop_covariates, process_categorical, split_target
from .nodes import train_test_split, concat_df, process_numeric, join_num_cat

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
                ,name="DropIrrelevantCovariates-Train"
            )
            ,node(
                func=process_categorical
                ,inputs=["train_dropped","parameters"]
                ,outputs="train_categorical"
                ,name="FeatureEngineeringCategoricals-Train"
            )
            ,node(
                func=process_numeric
                ,inputs=["train_dropped","parameters"]
                ,outputs="train_numeric"
                ,name="FeatureEngineeringNumericals-Train"
            )
            ,node(
                func=drop_covariates
                ,inputs=["test","parameters"]
                ,outputs="test_dropped"
                ,name="DropIrrelevantCovariates-Test"
            )
            ,node(
                func=process_categorical
                ,inputs=["test_dropped","parameters"]
                ,outputs="test_categorical"
                ,name="FeatureEngineeringCategoricals-Test"
            )
            ,node(
                func=process_numeric
                ,inputs=["test_dropped","parameters"]
                ,outputs="test_numeric"
                ,name="FeatureEngineeringNumericals-Test"
            )
            ,node(
                func=join_num_cat
                ,inputs=["train_numeric","train_categorical"]
                ,outputs="train_joined_num_cat"
                ,name="JoinCategoricalandNumerical-Train"
            )
            ,node(
                func=join_num_cat
                ,inputs=["test_numeric","test_categorical"]
                ,outputs="test_joined_num_cat"
                ,name="JoinCategoricalandNumerical-Test"
            )
        ]
    )