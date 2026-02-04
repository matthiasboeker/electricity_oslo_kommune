import pandas as pd
import numpy as np

def remove_negative_values(dataframe: pd.DataFrame):
    dataframe.loc[dataframe['forbruk_kwh'] < 0, 'forbruk_kwh'] = np.nan
    return dataframe

def remove_outliers_iqr(dataframe: pd.DataFrame, column_name: str):
    Q1 = dataframe[column_name].quantile(0.01)
    Q3 = dataframe[column_name].quantile(0.99)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    filtered_df = dataframe[(dataframe[column_name] >= lower_bound) & (dataframe[column_name] <= upper_bound)]
    return filtered_df

def clean_data_from_outliers(dataframe: pd.DataFrame):
    categoies = dataframe['kategori'].unique()
    cleaned_df = pd.DataFrame()
    for column_name in categoies:
        category_df = dataframe[dataframe['kategori'] == column_name]
        cleaned_df = pd.concat([cleaned_df, remove_outliers_iqr(category_df, "forbruk_kwh")])
    return cleaned_df