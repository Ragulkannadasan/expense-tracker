import os
import mysql.connector
from mysql.connector import MySQLConnection


def get_mysql_connection() -> MySQLConnection:
	"""Create and return a MySQL connection using environment variables.

	Required env vars (with defaults for local dev):
	- DB_HOST (default: localhost)
	- DB_PORT (default: 3306)
	- DB_USER (default: root)
	- DB_PASSWORD (default: empty)
	- DB_NAME (default: expensespydb)
	"""
	config = {
		"host": os.environ.get("DB_HOST", "localhost"),
		"port": int(os.environ.get("DB_PORT", "3306")),
		"user": os.environ.get("DB_USER", "root"),
		"password": os.environ.get("DB_PASSWORD", ""),
		"database": os.environ.get("DB_NAME", "expensespydb"),
	}
	return mysql.connector.connect(**config)


def init_schema() -> None:
	"""Create database and tables if they don't exist."""
	# Create database if needed
	admin_conn = mysql.connector.connect(
		host=os.environ.get("DB_HOST", "localhost"),
		port=int(os.environ.get("DB_PORT", "3306")),
		user=os.environ.get("DB_USER", "root"),
		password=os.environ.get("DB_PASSWORD", ""),
	)
	with admin_conn:
		cur = admin_conn.cursor()
		db_name = os.environ.get("DB_NAME", "expensespydb")
		cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
		cur.close()

	# Now create tables
	with get_mysql_connection() as conn:
		cur = conn.cursor()
		cur.execute(
			"""
			CREATE TABLE IF NOT EXISTS regtb (
			  id BIGINT AUTO_INCREMENT PRIMARY KEY,
			  Name VARCHAR(250),
			  Gender VARCHAR(250),
			  Age VARCHAR(250),
			  Email VARCHAR(250),
			  Mobile VARCHAR(250),
			  Address VARCHAR(250),
			  Username VARCHAR(250) UNIQUE,
			  Password VARCHAR(250)
			)
			"""
		)
		cur.execute(
			"""
			CREATE TABLE IF NOT EXISTS limtb (
			  id BIGINT AUTO_INCREMENT PRIMARY KEY,
			  Username VARCHAR(250),
			  mon INT,
			  yea INT,
			  Amount VARCHAR(20)
			)
			"""
		)
		cur.execute(
			"""
			CREATE TABLE IF NOT EXISTS expensetb (
			  id BIGINT AUTO_INCREMENT PRIMARY KEY,
			  Username VARCHAR(250),
			  Type VARCHAR(250),
			  date DATE,
			  Amount DECIMAL(10,2),
			  Info VARCHAR(250),
			  Bill VARCHAR(500),
			  mon INT,
			  yea INT
			)
			"""
		)
		conn.commit()


