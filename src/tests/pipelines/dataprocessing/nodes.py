# typing hings
from typing import List

import pandas as pd 
import numpy as np 

# separate data
from sklearn.model_selection import train_test_split

def split_target(alldata: pd.DataFrame, target:str) -> List[pd.DataFrame, pd.Series]:
    '''Splits data into target series and covariates dataframe'''

    X = alldata.drop([target], axis = 1)
    y = alldata[target]

    assert ((y.shape[1] == 1) & (X.shape[0] == alldata.shape[0]-1))

# def split_data(alldata: pd.DataFrame) -> List[pd.DataFrame]:
#     """
#     Separates data into 
#     """
