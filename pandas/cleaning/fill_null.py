import pandas as pd
from math import floor

df = pd.read_csv('titanic.csv')
print(df.info())
print("mean age: ", floor(df["Age"].mean()))
print("mode age: ", df["Age"].mode().max())
print("median age: ", df["Age"].median())
median_age = int(df["Age"].median())
df.fillna({"Age" : median_age }, inplace=True)
# new_df = df.dropna()
print(df.info())
df.to_csv("clean_fill_null_titanic.csv", index=False)
