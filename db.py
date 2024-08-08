import os
import psycopg2.pool

print("Starting database setup...")

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise Exception("DATABASE_URL environment variable not set")

# Create a connection pool with a min_size of 0 and a max_size of 80
print(f"Connecting to database with URL: {DATABASE_URL}")
pool = psycopg2.pool.SimpleConnectionPool(0, 80, DATABASE_URL)

# Get a connection from the pool
conn = pool.getconn()

# Create a cursor using the connection
cur = conn.cursor()

# Create the test_users table
print("Creating test_users table...")
cur.execute(
    """
    CREATE TABLE IF NOT EXISTS test_users (
        id SERIAL PRIMARY KEY,
        phone_number VARCHAR(15) NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        loved_one_name VARCHAR(100),
        loved_one_condition VARCHAR(255)
    )
    """
)

# Example operation: Adding a new user with loved one information
print("Inserting example data...")
cur.execute(
    """
    INSERT INTO test_users (phone_number, loved_one_name, loved_one_condition)
    VALUES (%s, %s, %s)
    RETURNING id
    """,
    ('+1234567890', 'John Doe', 'Recovering from surgery')
)
user_id = cur.fetchone()[0]

# Commit the changes to the database
conn.commit()

# Retrieve user and their loved one's information
cur.execute(
    """
    SELECT phone_number, loved_one_name, loved_one_condition
    FROM test_users
    WHERE id = %s
    """,
    (user_id,)
)

user_loved_one_info = cur.fetchone()

# Print the retrieved information
print("Inserted data:", user_loved_one_info)

# Clean up - delete the user
cur.execute(
    """
    DELETE FROM test_users
    WHERE id = %s
    """,
    (user_id,)
)

# Close the cursor and return the connection to the pool
cur.close()
print("Returning connection to the pool...")
pool.putconn(conn)

# When you are done using the pool, close it to release the resources
print("Closing connection pool...")
pool.closeall()

print("Database setup completed successfully.")