# A Script that would set up the environment for the project
config_file = r'''config\config.json'''

# Parse the config file and get the database configuration
import json
with open(config_file) as f:
    data = json.load(f)

server_config = data['server']
database_config = data['database']
user_config = data['users']

# Create the database and user

# Import mariadb connector
import mariadb 

def connect_as_root(root_name, root_password, host, port = 3306):
    try:
        conn = mariadb.connect(
            user=root_name,
            password=root_password,
            host=host,
            port=port
        )
        return conn
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}\nPlease check the root username and password")
        return None

def create_database(conn, database_name):
    try:
        cur = conn.cursor()
        cur.execute(f"drop database if exists {database_name}")
        cur.execute(f"CREATE DATABASE {database_name}")
        print({f"Database {database_name} created successfully"})
    except mariadb.Error as e:
        print(f"Error creating database: {e}")

def create_user(conn, user_name, user_password, host, database_name):
    try:
        cur = conn.cursor()
        # Check if the user already exists
        cur.execute(f"SELECT COUNT(*) FROM mysql.user WHERE user = '{user_name}' AND host = '{host}'")
        user_exists = cur.fetchone()[0] > 0

        if user_exists:
            print(f"User {user_name}@{host} already exists. Dropping the user first.")
            cur.execute(f"DROP USER IF EXISTS '{user_name}'@'{host}'")

        # Create the user
        cur.execute(f"CREATE USER '{user_name}'@'{host}' IDENTIFIED BY '{user_password}'")
        cur.execute(f"GRANT ALL PRIVILEGES ON {database_name}.* TO '{user_name}'@'{host}'")
        cur.execute("FLUSH PRIVILEGES")
        print(f"User {user_name} created successfully")
    except mariadb.Error as e:
        print(f"Error creating user: {e}")

# Extract data from configs
database = database_config['name']

# Extract data from user config
users = dict()
users['People'] = user_config['People']
users['Staff'] = user_config['Staff']
users['Account'] = user_config['Account']
users['User'] = user_config['User']

# Connect as root
root_name = input("Enter the root username: ") if server_config['root_name'] is None else server_config['root_name']
root_password = input("Enter the root password: ") if server_config['root_password'] is None else server_config['root_password']
host = input("Enter the host: ") if server_config['host'] is None else server_config['host']
port = input("Enter the port: ") if server_config['port'] is None else server_config['port']

conn = connect_as_root(root_name, root_password, host, port)

if conn:
    # Create the database
    database_name = database_config['name']
    create_database(conn, database_name)

    # Create the users
    for user in users.values():
        user_name = user['username']
        user_password = user['password']
        create_user(conn, user_name, user_password, host, database)
    
    # Drop the database and users
    try:
        cur = conn.cursor()
        cur.execute(f"DROP DATABASE IF EXISTS {database_name}")
        cur.execute("DROP USER IF EXISTS 'People'@'%'")
        cur.execute("DROP USER IF EXISTS 'Staff'@'%'")
        cur.execute("DROP USER IF EXISTS 'Account'@'%'")
        cur.execute("DROP USER IF EXISTS 'User'@'%'")
        print("Database and users dropped successfully.")
    except mariadb.Error as e:
        print(f"Error dropping database or users: {e}")
    finally:
        cur.close()

    conn.close()
    
else:
    print("Unable to connect to the database")


# TODO
# Apply unit tests
# Initialise the environment with the database and users, so it can be used for production