import mysql.connector
from config.settings import DB_CONFIG


def create_connection():
    # Create and return a MySQL database connection
    # using merged configuration from config/settings.py
    return mysql.connector.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        # usinig [] instead of (), as this throws an error when variable not found
    )