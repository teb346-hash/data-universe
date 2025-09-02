import pandas as pd

df = pd.read_csv('test3.csv')
print(df.info())
print(set(df.duplicated()))
print("DUPLICATION:",  df.duplicated(), sep="\n")
df.drop_duplicates(inplace = True)
print(df.info())
print(set(df.duplicated()))
df.to_csv("no_duplicate.csv", index=False)