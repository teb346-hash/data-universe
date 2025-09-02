import pandas as pd

df = pd.read_csv('exercise_calory.csv')
print(df.corr())