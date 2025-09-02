import pandas as pd

data = {
  "height": [120, 180, 190],
  "weight": [50, 40, 45]
}

#load data into a DataFrame object:
df = pd.DataFrame(data, index = ["day1", "day2", "day3"])

print(df) 
print("second row :  ", df.loc["day1"], sep = "\n")
print("second row :  ", df.loc[["day2", "day3"]], sep = "\n")