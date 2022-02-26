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

class MultiColumnLabelEncoder:
    def __init__(self,columns = None):
        self.columns = columns # array of column names to encode

    def fit(self,X,y=None):
        return self # not relevant here

    def transform(self,X):
        '''
        Transforms columns of X specified in self.columns using
        LabelEncoder(). If no columns specified, transforms all
        columns in X.
        '''
        output = X.copy()
        if self.columns is not None:
            for col in self.columns:
                output[col] = LabelEncoder().fit_transform(output[col])
        else:
            for colname,col in output.iteritems():
                output[colname] = LabelEncoder().fit_transform(col)
        return output

    def fit_transform(self,X,y=None):
        return self.fit(X,y).transform(X)

# Nodes
class ProcessFeatures():
    def __init__(self, df: pd.DataFrame, vars):
        self.vars = vars
        self.df = df

    # setter : set vars
    def set_vars(self):
        _varlist = self.vars
        _varlist = [_col.lower() for _col in _varlist]

        self.vars = _intersection(set(_varlist), set(list(self.df)))

    def get_vars(self, df):
        return self.vars

class ProcessCategorical(ProcessFeatures):
    def __init__(self, df: pd.DataFrame, vars):
        self.vars = vars
        self.df = df
        # all vars are categoricals, so I can convert all to categorical
        self.df_categorical = self.df[self.vars]
        self.df_categorical = self.df_categorical.astype(str)

class Features(ABC):
    def __init__(self, df:pd.DataFrame, single_var_list:list):
        self.df = df
        self.single_var_list = single_var_list
        
        self._df = self.df[self.single_var_list]

class Dummies(Features):
    def features(self):
        return pd.get_dummies(data = self._df)
class Ordinals(Features):
    def features(self):
        le = MultiColumnLabelEncoder()
        return le.fit_transform(self._df)

# concatenate every dataframe which received transformation
class AllFeatures:
    def get_all_features(df:pd.DataFrame, varlist:list):
        # concatenar conjunto de Features, pode ser nominal, dummy, o que for, eh tudo derivado de Features
        # dataframe is the same but the varlist is different
        return pd.concat(feature_set(df = df, single_var_list= vars).features() for feature_set,vars in zip(Features.__subclasses__(),varlist))

# The node function
def process_categoricals(df: pd.DataFrame, vars, varlist):
    _process_categoricals = ProcessCategorical(df = df, vars = vars)

    # categorical dataframe:
    df_cat = _process_categoricals.df_categorical

    save = AllFeatures.get_all_features(df, varlist)

    # PARA DEBUGAR
    save.to_csv('../../../../data/test_SOLID')

    return save

if __name__ == '__main__':

    # tudo isso aqui seriam parametros
    df = pd.read_csv('../../../../data/01_raw/alldata.csv')

    vars = ['MS.SubClass','MS.Zoning','Street','Alley',
        'Land.Contour','Lot.Config','Neighborhood','Condition.1',
        'Condition.2','Bldg.Type','House.Style','Roof.Style',
        'Roof.Matl','Exterior.1st','Exterior.2nd','Mas.Vnr.Type',
        'Foundation','Heating','Central.Air','Garage.Type','Sale.Type','Sale.Condition']

    dummies = ['MS.SubClass','MS.Zoning','Street','Alley']

    ordinals = ['Land.Contour','Lot.Config','Neighborhood','Condition.1',
        'Condition.2','Bldg.Type','House.Style','Roof.Style',
        'Roof.Matl','Exterior.1st','Exterior.2nd','Mas.Vnr.Type',
        'Foundation','Heating','Central.Air','Garage.Type','Sale.Type','Sale.Condition']

    varlist = [dummies, ordinals]

    print(process_categoricals(df, vars = vars, varlist = varlist))








# def process_categoricals(df: pd.DataFrame, vars, dummies, ordinals):

#     _process_categoricals = ProcessCategorical(df = df, vars = vars)

#     # categorical dataframe:
#     df_cat = _process_categoricals.df_categorical

#     # agora soh precisamos juntar a lista de dummies e Ordinals, mas a lista eh diferente
#     dummie = Dummies()
#     dummie.features(df_cat, varlist = dummies)
#     # future inmplement intersection, set , something like this, exclusion
#     ordinals = Ordinals()
#     ordinals.features(df_cat, varlist = ordinals)




#     return print(_process_categoricals.df_categorical)

# if __name__ == '__main__':
#     import pandas as pd

#     df = pd.read_csv('../../../../data/01_raw/alldata.csv')

#     vars = ['MS.SubClass','MS.Zoning','Street','Alley',
#         'Land.Contour','Lot.Config','Neighborhood','Condition.1',
#         'Condition.2','Bldg.Type','House.Style','Roof.Style',
#         'Roof.Matl','Exterior.1st','Exterior.2nd','Mas.Vnr.Type',
#         'Foundation','Heating','Central.Air','Garage.Type','Sale.Type','Sale.Condition']

#     dummies = ['MS.SubClass','MS.Zoning','Street','Alley']

#     ordinals = ['Land.Contour','Lot.Config','Neighborhood','Condition.1',
#         'Condition.2','Bldg.Type','House.Style','Roof.Style',
#         'Roof.Matl','Exterior.1st','Exterior.2nd','Mas.Vnr.Type',
#         'Foundation','Heating','Central.Air','Garage.Type','Sale.Type','Sale.Condition']

#     process_categoricals(df = df, vars=vars, dummies = dummies, ordinals = ordinals)















# class ProcessNumeric(ProcessFeatures):
#     def __init__(self, df: pd.DataFrame, vars):
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



