import pandas as pd
from math import floor

df = pd.read_csv('test3.csv')
print(df.info())
print(set(df["Embarked"]))
for x in df.index:
    if not df.loc[x, "Embarked"] in ["S", "C", "Q"]:
        df.loc[x, "Embarked"] = "S"
print(set(df["Embarked"]))
df.to_csv("clean_wrong_correct.csv", index=False)