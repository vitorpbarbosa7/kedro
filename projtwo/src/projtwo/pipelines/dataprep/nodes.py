import pandas as pd 
import numpy as np 
from typing import Any, List

def splittarget(df:pd.DataFrame, parameters):
    df.columns = df.columns.str.lower()
    df = df.rename(columns = {parameters["splitting"]["originaltarget"]:parameters["splitting"]["target"]})

    X_train = df.drop(parameters["splitting"]["target"], axis = 1)
    y_train = df[parameters["splitting"]["target"]]

    return [X_train,y_train]
