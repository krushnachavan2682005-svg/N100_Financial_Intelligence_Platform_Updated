import pandas as pd

df=pd.read_csv("D:/Tasks/N100_Financial_Intelligence_Platform/data/raw/n100_kaggle_top92_clean/standardized_tables/source_ratios.csv")
print(df.head())
def normalizer(df):
  df['year']=pd.to_datetime(df['year'],errors='coerce')
  df['year'] = df['year'].dt.year
  return df

# def normalize_columns(df):
#   df.columns=df.columns.str.strip()
#   return df
# print(normalize_columns(df).head())

def normalize_ticker(df):
  df['nse']=df['nse'].astype(str).str.strip().str.upper()
  return df
df = normalize_ticker(df)
print(df["nse"].head())