# typing hings
from typing import Tuple, Dict

import pandas as pd 
import numpy as np 

# separate data
from sklearn.model_selection import train_test_split as _train_test_split

def split_target(alldata: pd.DataFrame, parameters: Dict) -> Tuple[pd.DataFrame, pd.Series]:
    '''Splits data into target series and covariates dataframe'''

    alldata.columns = alldata.columns.str.lower()

    X = alldata.drop(parameters['vars']['target'], axis = 1)
    y = alldata[parameters['vars']['target']]

    return X, y 

def train_test_split(X_dev: pd.DataFrame, y_dev: pd.Series, parameters:Dict) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    X_train, X_test, y_train, y_test = _train_test_split(X_dev,y_dev,test_size = parameters['preprocess']['test_size'])

    return X_train, X_test, y_train, y_test

def concat_df(X_train:pd.DataFrame, X_test:pd.Series, y_train:pd.DataFrame, y_test:pd.Series) -> Tuple[pd.DataFrame]:
    train = pd.concat([y_train, X_train], axis = 1)
    test = pd.concat([y_test, X_test], axis = 1)

    return train, test
