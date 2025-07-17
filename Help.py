#This module contains the help text for the program, and the APIs.

def get_help():
    
    print("----------------------------------------------------------------------------------------------------------------------", end="\n")
    
    print("CLI.py: \nThe main command line interface for the APIs. It has an interactive CLI:")
    
    print("----------------------------------------------------------------------------------------------------------------------", end="\n")
    
    print("People.py: \nThis module contains the API for inserting people into the People table.")
    print("generate(name: str): \nThis function inserts a new record into the People table and returns the ID.")
    
    print("----------------------------------------------------------------------------------------------------------------------", end="\n")
    
    print("Staff.py: \nThis module contains the API for inserting staff into the Staff table")
    print("The module contains three classes: Admin, Manager, and Staff.")
    
    print("""Staff class is the base class for the other classes and has the following functions:
          
        __init__(self, staff_id, password): Initializes the object with the user_id and password, and sets the object attributes accordingly. Returns True, if the initialization was successful else False
            user_id(str): The staff ID.
            password(str): The password of the staff.
            ----NOTE----: Raises ValueError if login fails
            
        get_type(self): Returns the type of the user.
        
        add_user(self, people_id, user_id, hashed_passwd): Adds a user to the database, and returns True if the user was added successfully else False.
            people_id(str): The people ID of the user. Use the ID generated from People.py VARCHAR(64)
            user_id(str): The ID of the user. VARCHAR(36)
            hashed_pass(str): SHA3-512 Hash of the password provided by the user. VARCHAR(128)
            
        change_application(self, application_id): Commits changes to the application (Accept/Reject). After commiting the changes the application is deleted. Returns True if the operation was successful else False.
            application_id(str): The ID of the application which was provided to the user while creating the application. VARCHAR(16)""")
    
    print("----------------------------------------------------------------------------------------------------------------------", end="\n")
    
    print("""Manager class inherits from Staff class and has the following new functions:
          
          add_staff(self, people_id, staff_id, hashed_passwd, staff_type): Adds a staff to the database. Returns True if the operation was successful else False.
            people_id(str): The people ID of the staff. Use the ID generated from People.py VARCHAR(64)
            staff_id(str): The ID of the staff. VARCHAR(36)
            hashed_pass(str): SHA3-512 Hash of the password provided by the staff. VARCHAR(128)
            staff_type(int): The type of the staff. 0 for Staff, 1 for Manager, 2 for Admin.""")
    
    print("----------------------------------------------------------------------------------------------------------------------", end="\n")
    
    print("""Admin class inherits from Manager class and has the following new functions:
          
          remove_staff(self,staff_id): Removes a staff from the database. Returns True if the operation was successful else False.
            staff_id(str): The ID of the staff. VARCHAR(36)""")
    
    print("----------------------------------------------------------------------------------------------------------------------", end="\n")
    
    print("Users.py: \nThis module contains the APIs which can be used by the users to interact with their accounts")
    
    print("""It contains the following functions:
          
        __init__(self, user_id, password): Initializes the object with the user_id and password, and sets the object attributes accordingly.
            user_id(str): The ID of the user. VARCHAR(36)
            password(str): The password of the user. 
            ----NOTE----: Raises ValueError if login fails
        
        get_accounts(self): Returns a list of all the accounts of the user.
        
        login_account(self, account, password): Logs in the user for the current session. Returns True if logged in else False.
            account(str): The account id of the account. VARCHAR(36)
            password(str): The password of the account. 
            
        logout_account(self): Logs out the user from the current session.
        
        create_account(self, password): Creates a new account in the database.
            password(str): The password of the user.
            ----RETURNS: The ID of the account. VARCHAR(36), ID of the application. VARCHAR(16)----
        
        delete_account(self, account, password, reciever, private_key, confirm=False): Deletes the user's account from the database. Returns True if the operation was successful else False.   
            account(str): The account id of the account. VARCHAR(36)
            password(str): The password of the account to be deleted.
            reciever(str): The recipient which will receive the funds. VARCHAR(36)
            private_key(TextIOWrapper): The private key of the user.
            confirm(bool): This is False by default and must be True, if reciever does not belong to the same user.""")
    
    print("----------------------------------------------------------------------------------------------------------------------", end="\n")
    
    print("Accounts.py: \nThis module contains the APIs which are called when some changes are to be made in the account.")
    
    print("""It contains the following functions:
          
        __init__(self, account_id, password): Initializes the object with the account_id and password, and sets the object attributes accordingly.
            account_id(str): The account id of the account. VARCHAR(36)
            password(str): The password of the account. 
            ----NOTE----: Raises ValueError if login fails.
            
        get_balance(self): Returns the balance of the account.
        
        commit_transaction(self, amount, mode): Commits the transaction to the database. Returns True if the transaction was successful else False.
          amount(int): The amount to be added/subtracted from the account.
          moude(int): The mode of the transaction. 0 for deposit, 1 for withdrawal. 
          
        send_money(self, reciever, amount): Sends the given amount to the reciever. Returns True if the transaction was successful else False.
          reciever(str): The recipient which will receive the funds. VARCHAR(36)  
          amount(int): The amount to be sent from the account.""")
    print("----------------------------------------------------------------------------------------------------------------------", end="\n")
    print("CheckSQL.py: \nThis module contains the API which screens the SQL queries for security.")
    print("It contains the following function:")
    print("""check_sql(sql_query): Checks the SQL query for security. Returns True if the query is safe else raises PossibleSQLInjectionException.
          sql_query(str): The SQL query to be checked.""")
    print("----------------------------------------------------------------------------------------------------------------------", end="\n")
    print("This marks the end of the help page.")
    
if __name__ == '__main__':
    print("This module contains the help text for the program, and the APIs.")
    print("HELP PAGES FOR BANKING MANAGEMENT SYSTEM")
    print("Written by: Abhijit Kumar Singh")
    print("Github Repository: https://github.com/IAteNoodles/Banking_API.git")
    print("Check Readme.md for more information")
    print("Readme is available at: https://github.com/IAteNoodles/Banking_API/blob/master/README.md")
    get_help()
    
    
            
            
