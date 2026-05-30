import pandas as pd

df = pd.read_csv("USER_DATA.csv")

df.to_parquet(
    "USER_DATA.parquet",
    engine="pyarrow",
    index=False
)

print("Conversion complete")