from app.database.connection import pool

connection = pool.getconn()

print("Connected to PostgreSQL successfully!")

connection.close()
