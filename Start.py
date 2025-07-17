import json
from random import randbytes


def start_server(USERNAME, PASSWORD, DATABASE_NAME):
    import mariadb
    connector = mariadb.connect(user=USERNAME, password=PASSWORD, database=DATABASE_NAME)
    connection = connector.cursor()
    print("Connected to %s database" % DATABASE_NAME)
    return connector,connection

def make_tables(connector, connection, DATABASE_NAME):
    connection.execute("DROP DATABASE IF EXISTS %s" % DATABASE_NAME)
    connection.execute("CREATE DATABASE %s" % DATABASE_NAME)
    connector.commit()
    connection.execute("USE %s" % DATABASE_NAME)
    print("Creating tables")
    print("------------------------------------------------------")
    #PEOPLE TABLE
    print("Creating People Table")

    connection.execute("""CREATE TABLE `People`   (
                      `ID` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
                      `Name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
                      `Public Key` varchar(450) COLLATE utf8mb4_unicode_ci NOT NULL,
                      PRIMARY KEY (`ID`)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")
    connector.commit()
    print("People Table Created")
    print("------------------------------------------------------")
    #STAFF TABLE
    print("Creating Staff Table")

    connection.execute("""CREATE TABLE `Staff`  (
                `People ID` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
                `ID` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
                `Password` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
                `Type` smallint(5) unsigned NOT NULL,
                PRIMARY KEY (`ID`),
                KEY `People_ID` (`People ID`),
                CONSTRAINT `People_ID` FOREIGN KEY (`People ID`) REFERENCES `People` (`ID`) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")
    connector.commit()
    print("Staff Table Created")
    print("------------------------------------------------------")
    #USER TABLE
    print("Creating User Table")
   
    connection.execute("""CREATE TABLE `User`  (
                          `People ID` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
                          `ID` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
                          `Password` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
                          PRIMARY KEY (`ID`),
                          KEY `User_FK` (`People ID`),
                          CONSTRAINT `User_FK` FOREIGN KEY (`People ID`) REFERENCES `People` (`ID`) ON DELETE CASCADE
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")
    connector.commit()
    print("User Table Created")
    print("------------------------------------------------------")
    print("Creating Account Table")

    connection.execute("""CREATE TABLE `Accounts`  (
                          `User ID` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
                          `ID` varchar(40) COLLATE utf8mb4_unicode_ci NOT NULL,
                          `Password` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
                          `Balance` decimal(10,0) NOT NULL DEFAULT 0,
                          PRIMARY KEY (`ID`),
                          KEY `Accounts_FK` (`User ID`),
                          CONSTRAINT `Accounts_FK` FOREIGN KEY (`User ID`) REFERENCES `User` (`ID`) ON DELETE CASCADE
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")
    connector.commit()
    print("Account Table Created")
    print("------------------------------------------------------")
    print("Createing Account_Application Table")

    connection.execute("""CREATE TABLE `Account_Application`  (
                          `ID` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
                          `User_ID` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
                          `Account_ID` varchar(40) COLLATE utf8mb4_unicode_ci NOT NULL,
                          `Hash` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
                          `CreationTime` datetime NOT NULL,
                          PRIMARY KEY (`ID`),
                          KEY `Account_Application_FK` (`User_ID`),
                          CONSTRAINT `Account_Application_FK` FOREIGN KEY (`User_ID`) REFERENCES `User` (`ID`) ON DELETE CASCADE
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")
    connector.commit()
    print("Account_Application Table Created")
    print("------------------------------------------------------")
    print("Tables created")
    
def populate(connector, connection):
    print("------------------------------------------------------")
    print("Populating People Tables")
    print("Checking People_Name.txt for names...")
    people_name=open(r"./config/People_Name.txt").readlines()
    people_data = dict()
    for name in people_name:
        print()
        from People import generate
        name = name.strip()
        print("Generating Public Key for %s" % name)
        people_data[name] = generate(name)
        print("Public Key for %s generated" % name)
        print("------------------------------------------------------")
    print("------------------------------------------------------")
    print("Populated People Table")
    connector.commit()
    print("------------------------------------------------------")
    print("Creating the root user...")
    root_user = generate(input("Enter a name for the root user:"))
    root_staff_id = randbytes(16).hex()
    from hashlib import sha3_512 as sha3
    root_password = input("Enter a password for the root user:")
    hashed_password = sha3(root_password.encode()).hexdigest()
    connection.execute("INSERT INTO Staff (`People ID`, `ID`, `Password`, `Type`) VALUES ('%s', '%s', '%s', %d)" % (root_user, root_staff_id, hashed_password,2))
    connector.commit()
    print("Added root user to the Staff table. Please make sure you remember the password.")
    from Staffs import Admin
    ROOT = Admin(root_staff_id, root_password)
    print("Populating User Table")
    print("------------------------------------------------------")
    print("Using the name available in People_Name.txt")
    for name in people_data:
        user_id = randbytes(16).hex()
        password = randbytes(16).hex()
        people_id = people_data[name]
        people_data[name]=[people_id,user_id,password]
        print(user_id, password)
        ROOT.add_user(people_id, user_id, sha3(password.encode()).hexdigest())
    print("Populated User Table")
    connector.commit()
    print("------------------------------------------------------")
    print("Populating Account Table")
    print("Using the name available in People_Name.txt")
    from Users import User
    #Creating account applications
    for name in people_data:
        user_data = people_data[name]
        user_connection = User(user_data[1], user_data[2])
        password = randbytes(16).hex()
        account_id, application_id = user_connection.create_account(password)
        people_data[name].append(account_id)
        people_data[name].append(password)
        people_data[name].append(application_id)
        print(people_data[name])
    connector.commit()
    #Verifying accounts
    for name in people_data:
        ROOT.change_application(people_data[name][5],True)
    print("Populated Account Table")
    connector.commit()
    data = dict()
    print("------------------------------------------------------")
    print("Populated Database over")
    temp = dict()
    for name in people_data:
        temp[name]={
            "People_ID":people_data[name][0],
            "User_ID":people_data[name][1],
            "User Password":people_data[name][2],
            "Account_ID":people_data[name][3],
            "Account Password":people_data[name][4],
        }
    data = json.dumps(temp, sort_keys=True, indent=5)
    open(r"./config/people_data.txt", "w").write(data)
    
    """
    Format for data:
        name = people_id,
        user_id,
        password,
        account_id,
        account_password
    """


if __name__ == "__main__":
    connector, connection = start_server("IAteNoodles","CrazyxNoob@69","Banking")#(input("Username: "), input("Password:"), input("Database: "))
    make_tables(connector, connection, "Banking")
    populate(connector, connection)
    
    
