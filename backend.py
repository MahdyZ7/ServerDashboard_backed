#!/usr/bin/env python3
import subprocess
import mysql.connector
import logging
from typing import Dict
import os
from dotenv import load_dotenv
import time

load_dotenv()

# Database configuration
DB_CONFIG = {
	'host': 'localhost',
	'user': os.getenv("MYSQL_USER"),
	'password': os.getenv("MYSQL_PASSWORD"),
	'database': 'server_monitoring'
}


def init_db():
	"""Initialize the MySQL database."""
	create_table_query = '''
		CREATE TABLE IF NOT EXISTS server_metrics (
				id BIGINT AUTO_INCREMENT PRIMARY KEY,
				timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				server_name VARCHAR(255),
				architecture VARCHAR(255),
				operating_system VARCHAR(255),
				physical_cpus INT,
				virtual_cpus INT,
				ram_used VARCHAR(30),
				ram_total VARCHAR(30),
				ram_percentage INT,
				disk_used VARCHAR(30),
				disk_total VARCHAR(30),
				disk_percentage INT,
				cpu_load_1min DECIMAL(5,2),
				cpu_load_5min DECIMAL(5,2),
				cpu_load_15min DECIMAL(5,2),
				last_boot VARCHAR(255),
				tcp_connections INT,
				logged_users INT,
				active_vnc_users INT,
				active_ssh_users INT
		)
	'''

	create_table_query_2 = '''
		CREATE TABLE IF NOT EXISTS top_users (
			id BIGINT AUTO_INCREMENT PRIMARY KEY,
			timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			server_name VARCHAR(255),
			user VARCHAR(255),
			cpu DECIMAL(5,2),
			mem DECIMAL(5,2),
			disk DECIMAL(5,2)
		)
	'''
	conn = mysql.connector.connect(**DB_CONFIG)
	cursor = conn.cursor()
		
	cursor.execute(create_table_query)
	cursor.execute(create_table_query_2)
	conn.commit()


# Configure logging
logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s - %(levelname)s - %(message)s'
)

def server_online(server) -> bool:
	"""Check if the server is online."""
	try:
		# Run a simple command to check if the server is online
		command_string = ['ping', '-c', '1', '-w' , '5', server['host']]
		result = subprocess.run(command_string, capture_output=True, text=True, check=True)
		return True
	except subprocess.CalledProcessError:
		logging.error(f"Server {server['host']} is offline")
		return False


def run_monitoring_script(server) -> str:
	"""Execute the bash monitoring script and return its output."""
	try:
		# Get the directory of the current script
		current_dir = os.path.dirname(os.path.abspath(__file__))
		script_path = os.path.join(current_dir, 'BashGetInfo.sh')
		command_string = [script_path, server['host'], server['username'], server['password'], "mini_monitering.sh"]
		# Make sure the script is executable
		os.chmod(script_path, 0o755)
		
		# Run the script
		result = subprocess.run(command_string, 
							  capture_output=True, 
							  text=True, 
							  check=True)
		return result.stdout.strip()
	except subprocess.CalledProcessError as e:
		logging.error(f"Failed to run monitoring script: {e}")
		raise

def get_top_users(server) -> Dict:
	"""Get the top CPU and memory users on the server."""
	try:
		# Get the directory of the current script
		current_dir = os.path.dirname(os.path.abspath(__file__))
		script_path = os.path.join(current_dir, 'BashGetInfo.sh')
		command_string = [script_path, server['host'], server['username'], server['password'], "TopUsers.sh"]
		# Make sure the script is executable
		os.chmod(script_path, 0o755)
		
		# Run the script
		result = subprocess.run(command_string, 
							  capture_output=True, 
							  text=True, 
							  check=True)
		return parse_top_users(result.stdout)
	except subprocess.CalledProcessError as e:
		logging.error(f"Failed to get top users: {e}")
		raise

def parse_top_users(data: str) -> Dict:
	"""Parse the top users data from the monitoring script into a dictionary."""
	try:
		top_users = []
		for line in data.splitlines():
			if not line or line.strip() == '':
				continue
			user, cpu, mem, disk = line.split()
			top_users.append({
				'user': user,
				'cpu': float(cpu),
				'mem': float(mem),
				'disk': float(disk) if disk != 'nan' else 0
			})
		return top_users
	except Exception as e:
		logging.error(f"Failed to parse top users data: {e}")
		raise


def parse_monitoring_data(data: str) -> Dict:
	"""Parse the CSV output from the monitoring script into a dictionary."""
	try:
		# Split the CSV data
		(arch, os_info, pcpu, vcpu, ram_ratio, ram_perc, 
		disk_ratio, disk_perc, cpu_load_1min, cpu_load_5min, cpu_load_15min,
		last_boot, tcp, users, active_vnc_users, active_ssh_users) = data.split(',')

		# Parse RAM information
		ram_used, ram_total = ram_ratio.split('/')

		# Parse disk information
		disk_used, disk_total = disk_ratio.split('/')

		# Convert last_boot to datetime
		#last_boot_dt = datetime.strptime(last_boot, '%Y-%m-%d %H:%M')

		# Remove '%' from percentage values and convert to float
		disk_perc = int(disk_perc.strip('%'))
		ram_perc = int(ram_perc)

		return {
			'architecture': arch,
			'operating_system': os_info,
			'physical_cpus': int(pcpu),
			'virtual_cpus': int(vcpu),
			'ram_used': ram_used,
			'ram_total': ram_total,
			'ram_percentage': ram_perc,
			'disk_used': disk_used,
			'disk_total': disk_total,
			'disk_percentage': disk_perc,
			'cpu_load_1min': cpu_load_1min,
			'cpu_load_5min': cpu_load_5min,
			'cpu_load_15min': cpu_load_15min,
			'last_boot': last_boot,
			'tcp_connections': int(tcp),
			'logged_users': int(users),
			'active_vnc_users': int(active_vnc_users),
			'active_ssh_users': int(active_ssh_users)
		}
	except Exception as e:
		logging.error(f"Failed to parse monitoring data: {e}")
		raise

def store_metrics(metrics: Dict):
	"""Store the parsed metrics in the MySQL database."""
	insert_query = """
	INSERT INTO server_metrics (
		server_name, architecture, operating_system, physical_cpus, virtual_cpus,
		ram_used, ram_total, ram_percentage, disk_used, disk_total,
		disk_percentage, cpu_load_1min, cpu_load_5min, cpu_load_15min,
		last_boot, tcp_connections, logged_users, active_vnc_users, active_ssh_users
	) VALUES (
		%(server_name)s, %(architecture)s, %(operating_system)s, %(physical_cpus)s, %(virtual_cpus)s,
		%(ram_used)s, %(ram_total)s, %(ram_percentage)s, %(disk_used)s, %(disk_total)s,
		%(disk_percentage)s, %(cpu_load_1min)s, %(cpu_load_5min)s, %(cpu_load_15min)s,
		%(last_boot)s, %(tcp_connections)s, %(logged_users)s, %(active_vnc_users)s, %(active_ssh_users)s
	)
	"""
		
	try:
		conn = mysql.connector.connect(**DB_CONFIG)
		cursor = conn.cursor()
		
		cursor.execute(insert_query, metrics)
		conn.commit()
		
		logging.info("Successfully stored metrics in database")
		
	except mysql.connector.Error as e:
		logging.error(f"Database error: {e}")
		raise
	finally:
		if 'cursor' in locals():
			cursor.close()
		if 'conn' in locals():
			conn.close()

def store_top_users(server_name: str, top_users: Dict):
	"""Store the top users data in the MySQL database."""
	delete_query = """
	DELETE FROM top_users WHERE server_name = %s
	"""

	insert_query = """
	INSERT INTO top_users (
		server_name, user, cpu, mem, disk
	) VALUES (
		%(server_name)s, %(user)s, %(cpu)s, %(mem)s, %(disk)s
	)
	"""
	try:
		conn = mysql.connector.connect(**DB_CONFIG)
		cursor = conn.cursor()

		cursor.execute(delete_query, (server_name,))
		
		for user in top_users:
			user['server_name'] = server_name
			cursor.execute(insert_query, user)
		conn.commit()
		
		logging.info("Successfully stored top users in database")
		
	except mysql.connector.Error as e:
		logging.error(f"Database error: {e}")
		raise
	finally:
		if 'cursor' in locals():
			cursor.close()
		if 'conn' in locals():
			conn.close()

			
def readServerList():
	servers = []
	i = 1
	while True:
		server_name = os.getenv(f"SERVER{i}_NAME")
		if not server_name:
			break
		servers.append({
			   'name': server_name,
			   'host': os.getenv(f"SERVER{i}_HOST"),
			   'username': os.getenv(f"SERVER{i}_USERNAME"),
			   'password': os.getenv(f"SERVER{i}_PASSWORD")
		})
		i += 1
	return servers


		

def main():
	try:
		# Initialize the database
		init_db()
		while True:
			# Loop through the servers
			for server in readServerList():

				if not server_online(server):
					continue
				# Run monitoring script and get output
				monitoring_output = run_monitoring_script(server)
				top_users = get_top_users(server)
				# print (top_users)
				# Parse the monitoring data
				metrics = parse_monitoring_data(monitoring_output)
				metrics['server_name'] = server['name']
				# print(f"{server['name']}:\t{metrics}")
				# Store in database
				store_metrics(metrics)
				store_top_users(server['name'], top_users)
			# Wait for 5 minutes
			time.sleep(900)
		
	except Exception as e:
		logging.error(f"Error in main execution: {e}")
		raise

if __name__ == "__main__":
	main()