import pandas as pd

pd.options.display.max_rows = 9999999
df = pd.read_csv('titanic.csv')
print(df.head()) 
print(df.loc[range(0, 7)])
print(df)

df1 = pd.read_json('test.json')
print(df1.head(1))
print(df1.tail(2))
print(df1.info())
print("titanic db info : ", df.info())