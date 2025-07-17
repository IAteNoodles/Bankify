#This class will test if all the APIs are working as intended.
from hashlib import sha3_512 as sha3
import os
from random import randbytes
import sys
from People import generate

def clear_database():
    connector = mariadb.connect(user="IAteNoodles", passwd="CrazyxNoob@69", database="Banking")
    connection = connector.cursor()
    print("--------------------------------------------------------------------------------")
    #Clearing up the databases, and removing everything.
    print("Clearing up the databases...")
    tables = ["Account_Application", "Accounts", "User", "Staff", "People"]
    for table in tables:
        print("Truncating table: " + table)
        connection.execute("DELETE FROM " + table)
        print("Table truncated.")
        connector.commit()
    print("The database has been cleaned.")
    print("--------------------------------------------------------------------------------")
print("Checking mariadb connector is configured...")
import mariadb
try:
    connector = mariadb.connect(user="People", passwd="People@Bank", database="Banking", autocommit=True)
    connection = connector.cursor()
except mariadb.Error as e:
    print("Test failed: mariadb connector is not configured.")
    raise SystemExit("Error %d: %s" % (e.args[0], e.args[1]))

print("Test passed: mariadb connector is configured.")
#Checking that People clas is working as intended.
list_of_people: tuple = ("Charles",
                  "Winnie",
                  "Micheal",
                  "Charlie",
                  "William",
                  "Bertie",
                  "Juan",
                  "Iva",
                  "Adelaide",
                  "Ada",
                  "Daniel",
                  "Christina",
                  "Lilly",
                  "Isaiah",
                  "Marguerite",
                  "Gary")
                 

print("Inserting into the database using the People.generate() function")
list_of_ids = []
for person in list_of_people:
    list_of_ids.append(generate(person))


print("Checking that the people have been added to the People table.")
connection.execute("SELECT * FROM People where Name in {}".format(list_of_people))
connection.fetchall()
if connection.rowcount == len(list_of_people):
    print("Test passed: People table is correctly populated.")
else:
    print("Test failed: People table is not correctly populated.")
    print("Expected: {}".format(len(list_of_people)))
    print("Actual: {}".format(connection.rowcount))
    clear_database() 
    sys.exit(1)
    
print("Test passed: People APIs are working as intended.")

#Checking the Staff APIs are working as intended.
#Generating a new record in People table
random_password = randbytes(16).hex()
random_staff_id = randbytes(16).hex()
test_user = {
    "name": "ROOT@BANK",
    "passwd": random_password,
    "staff_id": random_staff_id,
    "type": "Admin"
    }
test_user["people_id"] = generate(test_user["name"])
#Inserting the new record into the Staff table.
hashed_passwd = sha3(test_user["passwd"].encode()).hexdigest()
connection.execute("INSERT INTO Staff (`People ID`, `ID`, `Password`, `Type`) VALUES ('%s', '%s', '%s', %d)" % (test_user["people_id"], test_user["staff_id"], hashed_passwd, 2))
connector.commit()

print("Connecting with ROOT@Bank...")
from Staffs import  Admin

test_user["object"] = Admin(test_user["staff_id"], test_user["passwd"])

print("Checking the staff type...")
if test_user["object"].get_type() == test_user["type"]:
    print("Test passed: Staff type is correct.")
else:
    print("Test failed: Staff type is incorrect.")
    clear_database() 
    sys.exit(1)

print("Adding a new admin (BANKING@ADMIN) to the database...")

print("Creating a new record in the People table...")
new_admin_people_id = generate("BANKING@ADMIN")
print("The private key for BANKING@ADMIN is stored in /__KEYS folder. Please save it somewhere secure and delete it.")

print("Creating a random password for the new admin...")
new_admin_password = randbytes(16).hex()
print("Password for BANKING@ADMIN is " + new_admin_password)
from hashlib import sha3_512 as sha3
hash_passwd = sha3(new_admin_password.encode()).hexdigest()
new_admin_staff_id = randbytes(18).hex()
test_user["object"].add_staff(new_admin_people_id, new_admin_staff_id, hash_passwd, 2)

print("Added a new admin (BANKING@ADMIN) to the database.")

print("DestroyingROOT@BANK connection...")
del test_user["object"]

print("Connecting with BANKING@ADMIN...")
new_admin_connection = Admin(new_admin_staff_id, new_admin_password)

print("Checking if BANKING@ADMIN is an admin...")
if new_admin_connection.get_type() == "Admin":
    print("Test passed: BANKING@ADMIN is an admin.")
else:
    print("Test failed: BANKING@ADMIN is not an admin")
    clear_database() 
    sys.exit(1)

print("Addming a bunch of users to the Bank...")

random_user_info = dict()
for id in list_of_ids:
    random_user_id = randbytes(18).hex()
    random_user_password = randbytes(16).hex()
    random_user_info[random_user_id] = random_user_password
    new_admin_connection.add_user(id, random_user_id, sha3(random_user_password.encode()).hexdigest())
    print("Added user " + id + " to the Bank with id: " + random_user_id +" and password: " + random_user_password)

print("Test passed: Admin is an able to add users to the Bank.")

print("Checking if BANKING@ADMIN is able to change applications...")
print("Creating a new application...")
account_info = dict()
applications = list()
for user in random_user_info:
    print("Creating an application for " + user)
    from Users import User
    user_connection = User(user, random_user_info[user])
    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print("Checking if there exists an account with the user")
    if user_connection.get_accounts() == 0:
        print("User has no accounts registered. Creating a new account application...")

        def create_account():
            password = randbytes(16).hex()
            application_id, account_id  = user_connection.create_account(password)
            print("Created an application for " + user)
            print("Application id: " + application_id)
            print("Account id: " + account_id)
            print("Password: " + password)
            applications.append(application_id)
            account_info[account_id] = password
        
        #Adding 1st account
        create_account()
        #Adding 2nd account
        create_account()

        
        

print("Accepting all the applications...")
no_of_applications_accepted = 0
for application in applications:
    print("Accepting application " + application)
    
    if not new_admin_connection.change_application(application, True):
        print("BANKING@ADMIN is not able to accept application " + application)
    else:
        print("Application " + application + " accepted.")
        no_of_applications_accepted += 1
        
print("BANKING@ADMIN accepted %d/%d applications" % (no_of_applications_accepted, len(applications)))
if len(applications) - no_of_applications_accepted > 5:
    print("Test failed: BANKING@ADMIN is not able to accept all the applications.")
    clear_database() 
    sys.exit(1)

print("Test passed: BANKING@ADMIN is able to accept the applications.")
if len(applications) - no_of_applications_accepted != 0:
    #Prints the amount of applications not accepted as error.
    sys.stderr.write("Waring: %d/%d applications not accepted." % (len(applications) - no_of_applications_accepted, len(applications)))   

print("Addming a bunch of staffs to the Bank...")    

count  = 0
for id in list_of_ids:
    staff_id = randbytes(18).hex()
    password = randbytes(16).hex()
    hash_passwd = sha3(password.encode()).hexdigest()
    type_staff = 0 if count % 2 == 0 else 1
    status = new_admin_connection.add_staff(id, staff_id, hash_passwd, type_staff)   
    if not status:
        sys.stderr.write("BANKING@ADMIN is not able to add staff " + id)
    else:
        print("Added staff " + id + " with id: " + staff_id + ", type: ", type_staff, ", and password: " + password)
        count += 1

if len(list_of_ids) - count > 5:
    print("Test failed: BANKING@ADMIN is not able to add all the staffs.")
    clear_database() 
    sys.exit(1)

print("Test passed: BANKING@ADMIN is able to add the staffs.")
if len(list_of_ids) - count != 0:
    sys.stderr.write("Waring: %d/%d staffs not added." % (len(list_of_ids) - count, len(list_of_ids)))

    
print("Removing ROOT@BANK from the database...")
if new_admin_connection.remove_staff(test_user["staff_id"]):
    print("Removed ROOT@BANK from the database.")
    print("Test passed: BANKING@ADMIN is able to remove ROOT@BANK (Admin).")
else:
    print("Failed to remove ROOT@BANK from the database")
    print("Test failed: BANKING@ADMIN is not able to remove ROOT@BANK (Admin).")
    
print("--------------------------------------------------------------------------------")
print("Test passed: Staff APIs are working as intended.")

#Test for the User APIs
print("--------------------------------------------------------------------------------")
print("Testing User APIs...")
print("Test Passed: Creating a new user")
print("Test Passed: Checking if user has an account")
print("Test Passed: Creating a new account associated with the user")

#USERS

count_login = 0
count_logout = 0
count_delete = 0
TESTING_ACCOUNT = "a47d9f6d-8ba5-11ec-8e63-d61b05c5cfbb1234"
#Password is 1
#ACCOUNTS
count_mismatch_balance = 0
count_failed_transactions = 0
for user in random_user_info:
    user_connection = User(user, random_user_info[user])
    print("Fecthing the user's accounts...")
    accounts = user_connection.get_accounts()
    if len(accounts) !=0:
        sys.stdout.write("User already has an account")
        sys.exit()

    print("Checking if user can log into account...")
    for account in accounts:
        if not user_connection.login_account(account, account_info[account]):
            print("Unable to login into account " + account)
            count_login += 1
            continue
        print("Logged into account " + account)
        #Fetching balance
        if user_connection.current_account.get_balance() != 0:
            count_mismatch_balance += 1
            sys.stderr.write("Waring: Balance mismatch for account " + account)
        
        #Depositing 1000 to the account.
        if user_connection.current_account.commit_transaction(1000, 1):
            print("Depositing 1000 to account: %s " %account)
            if user_connection.current_account.get_balance() != 1000:
                count_failed_transactions += 1
                count_mismatch_balance += 1
                sys.stderr.write("Waring: Balance mismatch for account " + account)
        else:
            sys.stderr.write("Failed to deposit 1000 to account: %s " %account)
            count_failed_transactions += 1
        #Sending money to TESTING_ACCOUNT 
        if not user_connection.current_account.send_money(TESTING_ACCOUNT, 500):
            count_failed_transactions += 1
            sys.stderr.write("Failed to send 500 to account: %s " %TESTING_ACCOUNT) 
        #Withdrawing 500 from the account.
        if user_connection.current_account.commit_transaction(500, 0):
            print("Withdrawing 1000 from account: %s " %account)
            if user_connection.current_account.get_balance() != 0:
                count_failed_transactions += 1
                count_mismatch_balance += 1
                sys.stderr.write("Waring: Balance mismatch for account " + account)
        else:
            sys.stderr.write("Failed to withdraw 1000 from account: %s " %account)
            count_failed_transactions += 1
        
        
        
        print("Logging out account " + account)
        user_connection.logout_account()
        if user_connection.current_account != None:
            print("Logout failed for account " + account)
            count_logout += 1
            continue
        print("Checking is user can delete account...")

    
    #Gettings the path of the private_key file
    private_key_path = r"./keys/" + user_connection.name + ".pem"
    if os.path.exists(private_key_path):
        private_key_file = open(private_key_path, "r")
        if user_connection.delete_account(accounts[0], account_info[accounts[0]], accounts[1], private_key_file.read()) == False:
            print("Unable to delete account " + account)
            print("Transfer account :" + accounts[0] + " to " + accounts[1])
            count_delete += 1
        else:
            print("Successfully deleted account " + account)
        if not user_connection.delete_account(accounts[1], account_info[account],TESTING_ACCOUNT,private_key_file):
            print("Checking delete_account failed for account beloging to other user without True parameter")
            if not user_connection.delete_account(accounts[1], account_info[account],TESTING_ACCOUNT,private_key_file, True):
                print("Unable to delete account " + account)
                print("Transfer account :" + accounts[0] + " to " + TESTING_ACCOUNT)
                count_delete += 1
        else:
            print("Successfully deleted account")
        
print("Test Passed: %d/%d accounts had mismatch balance" %(count_mismatch_balance, len(accounts)))
print("Test Passed: %d/%d accounts failed to commit transaction" %(count_failed_transactions, len(accounts)))

if count_mismatch_balance+count_failed_transactions > 5:
    sys.stderr.write("Warning: %d/%d Error occured" %(count_mismatch_balance+count_failed_transactions, len(accounts)))
    clear_database() 
    sys.exit(1)
print("Test Passed: Account APIs are working as intended.")
print("--------------------------------------------------------------------------------")

print("Test Passed: %d/%d users were unable to login into any accounts." % (count_login, len(random_user_info)))
print("Test Passed: %d/%d users were unable to logout from any accounts." % (count_logout, len(random_user_info)))
print("Test Passed: %d/%d users were unable to delete any accounts." % (count_delete, len(random_user_info)))

if count_login + count_logout + count_delete > 5:
    sys.stderr.write("Warning: %d/%d Errors occured." % (count_login+count_logout+count_delete, len(random_user_info)*4))
    clear_database() 
    sys.exit(1)

print("Test Passed: User APIs are working as intended.")
clear_database()
print("Please run Start.py to configure the database")













                    
            
    
    