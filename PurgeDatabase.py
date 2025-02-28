import mysql.connector
import logging
from typing import Dict
from dotenv import load_dotenv
import os
import time

DB_CONFIG = {
	'host': 'localhost',
	'user': os.getenv("MYSQL_USER"),
	'password': os.getenv("MYSQL_PASSWORD"),
	'database': 'server_monitoring'
}

def purge_database():
	"""Purge the MySQL database."""
	conn = mysql.connector.connect(**DB_CONFIG)
	cursor = conn.cursor()
	cursor.execute("DELETE FROM server_metrics WHERE timestamp < NOW() - INTERVAL 2 DAY")
	cursor.execute("DELETE FROM top_users WHERE timestamp < NOW() - INTERVAL 2 DAY")
	conn.commit()
	conn.close()
	logging.info("Successfully purged database")

if __name__ == "__main__":
	load_dotenv()
	logging.basicConfig(level=logging.INFO)
	purge_database()

