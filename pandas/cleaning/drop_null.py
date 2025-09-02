import pandas as pd

df = pd.read_csv('titanic.csv')
print(df.info())
new_df = df.dropna()
print(new_df.info())
new_df.to_csv("clean_null_titanic.csv", index=False)
