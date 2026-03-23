import pandas as pd, os

EXCEL_PATH = "data/raw/Sample-Superstore.xlsx"

sheets = {
    "Orders":  "data/raw/orders.csv",
    "Returns": "data/raw/returns.csv",
    "People":  "data/raw/people.csv",
}

for sheet_name, out_path in sheets.items():
    df = pd.read_excel(EXCEL_PATH, sheet_name=sheet_name)
    df.to_csv(out_path, index=False)
    print(f"wrote {out_path}  ({len(df):,} rows)")


