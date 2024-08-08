import os
import psycopg2
from psycopg2 import sql

# Connect to the database
DATABASE_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Define tables and sequences to drop
items_to_drop = ["loved_ones", "loved_ones_id_seq", "users", "users_id_seq"]

# Drop each item if it exists
for item in items_to_drop:
    drop_item_query = sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(sql.Identifier(item))
    cur.execute(drop_item_query)

# Attempt to drop sequences alone as well, in case they aren't tied to table drops
for item in items_to_drop:
    if "seq" in item:
        drop_item_query = sql.SQL("DROP SEQUENCE IF EXISTS {} CASCADE").format(sql.Identifier(item))
        cur.execute(drop_item_query)

# Commit the transaction
conn.commit()

# Close the cursor and connection
cur.close()
conn.close()

print("All specified tables and sequences have been dropped.")