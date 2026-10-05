import sqlite3
import pandas as pd
import numpy as np

# 1. Generate sample resellers
resellers_df = pd.DataFrame({
    'reseller_id': [1, 2, 3, 4, 5],
    'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eva'],
    'state': ['KA', 'MH', 'DL', 'KA', 'TN'],
    'signup_date': ['2023-01-01', '2023-01-15', '2023-02-01', '2023-02-10', '2023-03-01']
})

# 2. Generate sample orders
orders_df = pd.DataFrame({
    'order_id': [101, 102, 103, 104, 105],
    'reseller_id': [1, 1, 2, 3, 4],
    'order_date': ['2023-01-10', '2023-01-20', '2023-02-05', '2023-02-12', '2023-03-05'],
    'gmv': [1500, 2300, 800, 1200, 3100]
})

# 3. Save CSV files in data/
resellers_df.to_csv('data/resellers.csv', index=False)
orders_df.to_csv('data/orders.csv', index=False)

# 4. Save to SQLite DB in data/
conn = sqlite3.connect('data/meesho_reseller.db')
resellers_df.to_sql('resellers', conn, if_exists='replace', index=False)
orders_df.to_sql('orders', conn, if_exists='replace', index=False)
conn.close()

print("Dataset successfully generated!")