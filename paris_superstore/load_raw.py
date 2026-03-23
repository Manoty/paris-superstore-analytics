import duckdb, os

DB_PATH = "dev.duckdb"
RAW_DIR = "data/raw"

TABLES = {
    "raw_orders":  "orders.csv",
    "raw_returns": "returns.csv",
    "raw_people":  "people.csv",
}

con = duckdb.connect(DB_PATH)

for table_name, filename in TABLES.items():
    filepath = os.path.join(RAW_DIR, filename)
    if not os.path.exists(filepath):
        print(f"MISSING: {filepath}")
        continue
    con.execute(f"drop table if exists {table_name}")
    con.execute(f"create table {table_name} as select * from read_csv_auto('{filepath}', header=true)")
    count = con.execute(f"select count(*) from {table_name}").fetchone()[0]
    print(f"loaded {table_name}: {count:,} rows")

con.close()
print("\nDone. Run `dbt run` next.")
