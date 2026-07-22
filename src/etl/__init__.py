import pathlib 
import pandas as pd

raw_path=pathlib.Path("D:/Tasks/N100_Financial_Intelligence_Platform/data/raw/n100_kaggle_top92_clean/standardized_tables")

for file in raw_path.glob("*.csv"):
    print(f"\n=== {file.name} ===")
    df = pd.read_csv(file)

    print(df.head())
    print(df.dtypes)
    print(df.isnull().sum())
    print(df.info())
    print(df.describe())
    print("Duplicate rows:", df.duplicated().sum())
def validate_loaded_tables(df):
    consist_null=df.isnull().sum().sum()
    duplicate_values= df.duplicated().sum().sum()
    if consist_null==0 and duplicate_values==0:
        return "PASS"
    elif consist_null==0 or duplicate_values==0:
        return "WARNING"
    else:
        return "FAIL"


for file in raw_path.glob("*.csv"):
    df = pd.read_csv(file)
    print(f"\n=== {file.name} ===")
    print(validate_loaded_tables(df))