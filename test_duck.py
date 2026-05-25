import duckdb
try:
    print(duckdb.execute("SELECT list_extract(str_split('fe80::1', '.'), 2)").fetchall())
except Exception as e:
    print("Error:", e)
