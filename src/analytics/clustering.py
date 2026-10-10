import sqlite3
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

DB = "data/nifty100.db"
FEATURES = [
    "net_profit_margin_pct",
    "return_on_equity_pct",
    "debt_to_equity",
    "roce_pct",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
]

conn = sqlite3.connect(DB)
df = pd.read_sql_query(
    """
    SELECT f.* FROM financial_ratios f
    JOIN (SELECT company_id, MAX(year) AS y
          FROM financial_ratios GROUP BY company_id) m
      ON f.company_id = m.company_id AND f.year = m.y
    """,
    conn,
)

X = df[FEATURES].apply(pd.to_numeric, errors="coerce")
X = X.clip(-100, 100, axis=1)
X = X.fillna(X.median())
X = X.clip(X.quantile(0.05), X.quantile(0.95), axis=1)

X_scaled = StandardScaler().fit_transform(X)
df["cluster"] = KMeans(n_clusters=4, n_init=10, random_state=42).fit_predict(X_scaled)

df[FEATURES] = X
out = df[["company_id", "year", "cluster"] + FEATURES]
out.to_csv("output/clustering_results.csv", index=False)
out.to_sql("clusters", conn, if_exists="replace", index=False)
conn.close()

print("Clustering done:", len(out), "companies")
print(out.groupby("cluster")[FEATURES].mean().round(1))