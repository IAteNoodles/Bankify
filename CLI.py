from CheckSQL import sql_injection_check as check
#The interface to interact with the apis.
def work_as_user(user_id, password):
    from Users import User
    #Creates a new user object.
    current_login_object=User(user_id, password)
    print("Welcome to the User Portal")
    print("Your the following user:" + current_login_object.user_id)
    while(True):
        print("Options avaliable to you are:")
        print("1. Log in to one of your accounts")    
        print("2. Create a new account")
        print("3. Delete a account")
        print("Anything else to log out")
        choice = int(check("Enter your choice: "))
        if choice == 1:
            
            #Checks if there is atleast one account associated with this user.
            if current_login_object.get_accounts() == 0:
                print("You have no account associated with you.\nTo log in, please make an account first")
                continue
            print("Accounts related to this user are:")
            index = 1
            #Provides a list of the accounts linked to this user.
            for account in current_login_object.accounts:
                print(index, ": " + account)
                index+=1
            
            #Asks the user to enter the account number to login.
            relative_account = int(check("Enter the account number to login: "))
            if relative_account > len(current_login_object.accounts) or relative_account < 1:
                return "Invalid account number"
            
            #Asks the user to enter the password to login.
            password = check("Enter the password to login: ")
            
            print("Logging in...")
            if current_login_object.login_account(current_login_object.accounts[relative_account-1],password) == False:
                return "Please make sure that you have an account. If you already have submitted an account, please wait for the application to be verified."
            print("Logged in to account: ", account)
            while(True):
                print("Your balance is: " + str(current_login_object.current_account.balance))
                print("Options avaliable to you are:")
                print("1. Withdraw money")
                print("2. Deposit money")
                print("3. Fetch balance")
                print("4. Transfer money")
                print("To log out of the current account press anything else.")
                choice = check("Enter your choice: ")
                if choice == "1":
                    amount = int(check("Enter the amount to withdraw: "))
                    current_login_object.current_account.commit_transaction(amount,0)
                elif choice == "2":
                    amount = int(check("Enter the amount to deposit: "))
                    current_login_object.current_account.commit_transaction(amount,1)
                elif choice == "3":
                    current_login_object.current_account.get_balance()
                elif choice == "4":
                    transfering_account_id = check("Enter the account id to transfer to: ")
                    amount = int(check("Enter the amount to transfer: "))
                    if current_login_object.current_account.send_money(transfering_account_id,amount):
                        print("Money transfered successfully")
                    else:
                        print("Error in transfering money")
                    
                else:
                    current_login_object.logout_account()
                    break
                
        elif choice == 2:
            current_login_object.create_account(check("Password: "))
        elif choice == 3:
            
            if current_login_object.get_accounts() == 0:
                return "You have no accounts associated with you."
            index=1
            accounts = []
            for account_id in current_login_object.accounts:
                accounts.append(account_id)
                print(index, ": ", account_id)
                index+=1
            relative_account = int(check("Enter the account number to delete: "))
            if relative_account > len(accounts) or index-1 < 2:
                print("Invalid account number. You need to have at least 2 accounts for this operation.")
                return "User didn't have enough accounts."
            choice=check("THIS WILL YOUR ACCOUNT, ARE YOU SURE YOU WANT TO DELETE THIS ACCOUNT? (y?)")
            if choice == "n":
                print("Command Aborted...")
            
            password = check("Password of the account: ")            
            print("ALL YOUR FUNDS WILL BE TRANSFERED TO THE FIRST ACCOUNT ASSOCIATED WITH YOU.")
            choice=check("Do you wish to change the account to transfer funds to? (n?)")
            if choice == "y":
                account_number=check("Account number to transfer funds to: ")
                account_id = accounts[account_number-1]
            else:
                account_id = accounts[1] if relative_account == 1 else accounts[0]
            print("Transferring funds from account: " + accounts[relative_account-1] + " to account: " + account_id + "...")
            private_key=open(input("Path to private key: ")) #SQL injection checking isn't required here as this statement has no interactions with the database.
            current_login_object.delete_account(accounts[relative_account-1], password, account_id, private_key)
            
        else:
            print("Logging out...")
            del current_login_object
            print("Goodbye! The user portal is now closed.")
            return
        
    
def work_as_staff(staff_id, password):
    
    #Imports the Staff, Manager and Admin classes.
    from Staffs import Staff, Manager, Admin
    import mariadb
    import os
    from dotenv import load_dotenv

    load_dotenv()

    DB_HOST = os.getenv("DB_HOST")
    DB_USER_STAFF = os.getenv("DB_USER_STAFF")
    DB_PASS_STAFF = os.getenv("DB_PASS_STAFF")
    DB_DATABASE_NAME = os.getenv("DB_DATABASE_NAME")
    
    connector = mariadb.connect(
    user=DB_USER_STAFF, host=DB_HOST, passwd=DB_PASS_STAFF, database=DB_DATABASE_NAME)
    connection = connector.cursor()
    #Checks the type of the staff and creates a new instance of the appropriate staff class.
    connection.execute("SELECT Type FROM Staff WHERE ID = '%s'" % staff_id)

    staff_type = connection.fetchone()[0]
    if staff_type == 0:
        current_login_object = Staff(staff_id, password)
    elif staff_type == 1:
        current_login_object = Manager(staff_id, password)
    elif staff_type == 2:
        current_login_object = Admin(staff_id, password)
    else:
        print("Invalid staff type")
        return "Exiting..."
    
    
    
    print("Welcome to the Staff Portal")
    print("Your the following staff:" + current_login_object.user_id + "of type:" + str(current_login_object.get_type()))
    print("Options avaliable to you are:")
    
    options = []
    options.append("1. Create a user")
    options.append("2. Change an application")
    
    #Checks if the current_login_object is instance of Manager.
    if current_login_object.type >=1:
        options.append("3. Add a staff")
        #Checks if the current_login_object is instance of Admin.
        if current_login_object.type==2:
            options.append("4. Remove a staff")
    
    
    while(True):
        
        print("You options are: ")
        for option in options:
            print(option)
        print("To log out of the current staff press anything else.")

        
        choice = check("Please enter your choice: ")
    
        #Uses if elif else to call the appropriate function.
        
        if choice == "1":
            #WORKS
            people_id = check("Enter the people ID: ") #Varchar(64)
            user_id = check("Please enter the user id: ") #Varchar(36) 
            hashed_passwd = check("Please enter the hashed password: ") #Varchar(128)
            current_login_object.add_user(people_id, user_id, hashed_passwd)
            
        elif choice == "2":
            #WORKS
            choice = check("Do you want to list every application opened at present? (y?)")
            if choice == "n":
                application_id = check("Please enter the application id: ")
            else:
                connection.execute("SELECT `ID`, `User_ID`, `CreationTime`  FROM Account_Application")
                applications = connection.fetchall()
                index = 1
                
                #Checks if there are any opened applications
                if len(applications) ==0:
                    print("There are no applications opened at present.")
                    continue
                
                for application_data in applications:
                    print(index,":")
                    print("\t\t","Application ID: ",application_data[0])
                    print("\t\t","User ID: ",application_data[1])
                    print("\t\t","Date of creation: ",application_data[2])
                    index += 1
                    
                application_id = check("Please enter the application id: ")
                accept = False if check("Do you want to accept this application? (Y/n?)") == "n" else True
            current_login_object.change_application(application_id, accept)
            
        elif choice == "3":
            #WORKS
            people_id = check("Enter the people ID: ") #Varchar(64)
            staff_id = check("Please enter the staff id: ") #Varchar(36) 
            hashed_passwd = check("Please enter the hashed password: ")
            staff_type = int(check("0: Staff, 1: Manager, 2: Admin:\nEnter the staff type: "))
            current_login_object.add_staff(people_id, staff_id, hashed_passwd, staff_type)
            
        elif choice == "4":
            #WORKS
            staff_id = check("Please enter the staff id: ")
            current_login_object.remove_staff(staff_id)
        
        else:
            print("Logging out...")
            del current_login_object
            print("Goodbye! The staff portal is now closed.")
            return 

         # ----------------------------------------------------------------END OF STAFF PORTAL---------------------------------------------------------------------------------
        
    
if __name__ == '__main__':
    print("Welcome to the Bank API")
    print("Enter the number of the function you want to use:")
    print("1: Help")
    print("2: Login")
    choice = int(check("Enter your choice: "))
    if choice == 1:
        from Help import get_help
        get_help()
        
    elif choice == 2:
        print("This is the User login page")
        print("Are you a user? (Y/n?)")
        choice = check("Enter your choice: ").lower()
        if choice == "n":
            print("This is the staff login page")
            staff_id = check("Enter your id: ") #Varchar(36) 
            password = check("Enter your password: ") #Varchar(128)
            work_as_staff(staff_id, password)
        else:
            user_id = check("Enter your id: ")
            password = check("Enter your password: ")
            from Users import User
            work_as_user(user_id, password)
