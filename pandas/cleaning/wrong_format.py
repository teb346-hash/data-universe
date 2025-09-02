import pandas as pd
from math import floor

df = pd.read_csv('test2.csv')
s = df["Birthday"].astype("string").str.strip().str.replace(r"\.0$", "", regex=True)

# 2) Prepare an all-NaT datetime Series
dt = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")

# 3) Parse specific patterns

# a) 8 digits: YYYYMMDD (e.g., 18690423)
mask_yyyymmdd = s.str.fullmatch(r"\d{8}")
dt.loc[mask_yyyymmdd] = pd.to_datetime(s[mask_yyyymmdd], format="%Y%m%d", errors="coerce")

# b) Slash month/day/year: M/D/YYYY or MM/DD/YYYY (e.g., 4/21/1902, 10/22/1907)
mask_mdyyyy = s.str.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}")
dt.loc[mask_mdyyyy] = pd.to_datetime(s[mask_mdyyyy], format="%m/%d/%Y", errors="coerce")

# c) ISO-like with '-' or '/': YYYY-MM-DD or YYYY/MM/DD
mask_iso = s.str.fullmatch(r"\d{4}[-/]\d{2}[-/]\d{2}")
dt.loc[mask_iso] = pd.to_datetime(s[mask_iso], errors="coerce")

# d) Fallback: anything else, let pandas infer
rest = s[dt.isna()]
dt.loc[rest.index] = pd.to_datetime(rest, errors="coerce", infer_datetime_format=True)

# 4) Format uniformly as strings YYYY-MM-DD
df["Birthday"] = dt.dt.strftime("%Y-%m-%d")

# Optional: if you prefer blanks instead of NaN for unparseable values
# df["Birthday"] = df["Birthday"].fillna("")

print(df.head())
df.to_csv("date_correct.csv",  index=False)