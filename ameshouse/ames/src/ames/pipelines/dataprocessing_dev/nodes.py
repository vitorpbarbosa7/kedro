# typing hings
from typing import Tuple, Dict, Type
from abc import ABC, abstractmethod
import pandas as pd 
import numpy as np 
# separate data
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split as _train_test_split

# utils
def _intersection(*args:set):
    return set.intersection(args)

# Nodes
class ProcessFeatures():
    def __init__(self, df: pd.DataFrame, catvars):
        self.catvars = catvars
        self.df = df

    # setter : set vars
    def set_vars(self):
        _varlist = self.catvars
        _varlist = [_col.lower() for _col in _varlist]

        self.catvars = _intersection(set(_varlist), set(list(self.df)))

    def get_vars(self, df):
        return self.vars

class ProcessCategorical(ProcessFeatures):
    def __init__(self, df: pd.DataFrame, catvars):
        self.catvars = catvars
        self.df = df

        # all vars are categoricals, so I can convert all to categorical
        self.df_categorical = self.df[self.catvars]
        self.df_categorical = self.df_categorical.astype(str)

class Features(ABC):
    @abstractmethod
    def features(self, df:pd.DataFrame, varlist:str):
        pass
class Dummies(Features):
    def features(self, df:pd.DataFrame, varlist:str):
        _df = df[varlist]
        return pd.get_dummies(data = _df)
class Encoded(Features):
    def features(self, df:pd.DataFrame, varlist:str):
        le = LabelEncoder()
        _df = df[varlist]
        le.fit(_df)
        return le.transform(_df)

class AllFeatures:
    @abstractmethod
    def get_all_features(df, varlist):
        # concatenar conjunto de Features, pode ser nominal, dummy, o que for, eh tudo derivado de Features
        return pd.concat(feature_set.features(df, varlist) for feature_set in Features.__subclasses__())


def process_categoricals(df: pd.DataFrame, catvars):

    _process_categoricals = ProcessCategorical(df = df, catvars = catvars)

    # categorical dataframe:
    df_cat = _process_categoricals.df_categorical

    # agora soh precisamos juntar a lista de dummies e encoded, mas a lista eh diferente

    return print(_process_categoricals.df_categorical)

if __name__ == '__main__':
    import pandas as pd

    df = pd.read_csv('../../../../data/01_raw/alldata.csv')

    catvars = ['MS.SubClass','MS.Zoning','Street','Alley',
        'Land.Contour','Lot.Config','Neighborhood','Condition.1',
        'Condition.2','Bldg.Type','House.Style','Roof.Style',
        'Roof.Matl','Exterior.1st','Exterior.2nd','Mas.Vnr.Type',
        'Foundation','Heating','Central.Air','Garage.Type','Sale.Type','Sale.Condition']

    process_categoricals(df = df, catvars=catvars)















# class ProcessNumeric(ProcessFeatures):
#     def __init__(self, df: pd.DataFrame, catvars):
#         self.parameters = parameters
#         self.vartype = vartype
#         self.df = df

# AllFeatures.get_all_features(self, )







# def process_numeric(df:pd.DataFrame, parameters:Dict) -> pd.DataFrame:

#     __cat = parameters['preprocess']['numericvars']
#     __cat = [_col.lower() for _col in __cat]

#     catinter = list(set(__cat).intersection(list(df)))

#     df = df.drop(catinter, axis = 1)

#     LotShape = {'Reg':3,'IR1':2,'IR2':1,'IR3':0}
#     Utilities = {'AllPub':3,'NoSewr':2,'NoSewa':1,'ELO':0}
#     LandSlope = {'Gtl':2,'Mod':1,'Sev':0}
#     ExterQual = {'Ex':4,'Gd':3,'TA':2,'Fa':1,'Po':0}
#     ExterCond = ExterQual # They're the same values 
#     BsmtQual = {'Ex':5,'Gd':4,'TA':3,'Fa':2,'Po':1,np.nan:0}
#     BsmtCond = BsmtQual
#     BsmtExposure = {'Gd':4,'Av':3,'Mn':2,'No':1, np.nan:0}
#     BsmtFinType1 = {'GLQ':6,'ALQ':5,'BLQ':4,'Rec':3,'LwQ':2,'Unf':1,np.nan:0}
#     BsmtFinType2 = BsmtFinType1
#     HeatingQC = ExterQual
#     Electrical = {'SBrkr':4,'FuseA':3,'FuseF':2,'FuseP':1,'Mix':0}
#     KitchenQual = ExterQual
#     Functional = {'Typ':7,'Min1':6,'Min2':5,'Mod':4,'Maj1':3,'Maj2':2,'Sev':1,'Sal':0}
#     FireplaceQu = BsmtQual
#     GarageFinish = {'Fin':3,'RFn':2,'Unf':1,np.nan:0}
#     GarageQual = BsmtQual
#     GarageCond = BsmtQual
#     PavedDrive = {'Y':2,'P':1,'N':0}
#     PoolQC = {'Ex':4,'Gd':3,'TA':2,'Fa':1,np.nan:0}
#     Fence = {'GdPrv':4,'MnPrv':3,'GdWo':2,'MnWw':1,np.nan:0}
    
#     ordinal_dict = {'lot.shape':LotShape,
#                 'utilities':Utilities,
#                 'land.slope':LandSlope,
#                 'exter.qual':ExterQual,
#                 'exter.cond':ExterCond,
#                 'bsmt.qual':BsmtQual,
#                 'bsmt.cond':BsmtCond,
#                 'bsmt.exposure':BsmtExposure,
#                 'bsmtFin.type.1':BsmtFinType1,
#                 'bsmtFin.type.2':BsmtFinType2,
#                 'heating.qc':HeatingQC,
#                 'electrical':Electrical,
#                 'kitchen.qual':KitchenQual,
#                 'functional':Functional,
#                 'fireplace.qu':FireplaceQu,
#                 'garage.finish':GarageFinish,
#                 'garage.qual':GarageQual,
#                 'garage.cond':GarageCond,
#                 'paved.drive':PavedDrive,
#                 'pool.qc':PoolQC,
#                 'fence':Fence}

#     # add to logging
#     # ordinal_vars = list(ordinal_dict.keys())

#     df_numeric = df.replace(ordinal_dict)

#     return df_numeric




# def split_target(alldata: pd.DataFrame, parameters: Dict) -> Tuple[pd.DataFrame, pd.Series]:
#     '''Splits data into target series and covariates dataframe'''

#     alldata.columns = alldata.columns.str.lower()

#     X = alldata.drop(parameters['vars']['target'], axis = 1)
#     y = alldata[parameters['vars']['target']]

#     return X, y 

# def train_test_split(X_dev: pd.DataFrame, y_dev: pd.Series, parameters:Dict) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
#     X_train, X_test, y_train, y_test = _train_test_split(X_dev,y_dev,test_size = parameters['preprocess']['test_size'])

#     return X_train, X_test, y_train, y_test

# def concat_df(X_train:pd.DataFrame, X_test:pd.Series, y_train:pd.DataFrame, y_test:pd.Series) -> Tuple[pd.DataFrame]:
#     train = pd.concat([y_train, X_train], axis = 1)
#     test = pd.concat([y_test, X_test], axis = 1)

#     return train, test

# def drop_covariates(df:pd.DataFrame, parameters:Dict) -> pd.DataFrame:

#     df = df.drop(columns = parameters['preprocess']['dropvars'], axis = 1)

#     return df


    

# def join_num_cat(dfnum:pd.DataFrame, dfcat:pd.DataFrame) -> pd.DataFrame:

#     _pk = 'id'

#     dfnum[_pk] = dfnum.index
#     dfcat[_pk] = dfcat.index
    
#     df_num_cat = pd.merge(left=dfnum, right=dfcat, on=_pk)

#     return df_num_cat



