#A class which can be used to access account apis.
#This class is filled with only the base apis. Other features maybe added in future.
from random import randbytes
import sys
import mariadb
import os
from dotenv import load_dotenv

load_dotenv()

from Accounts import Account

DB_HOST = os.getenv("DB_HOST")
DB_USER_USER = os.getenv("DB_USER_USER")
DB_PASS_USER = os.getenv("DB_PASS_USER")
DB_DATABASE_NAME = os.getenv("DB_DATABASE_NAME")

connector = mariadb.connect(user=DB_USER_USER, host=DB_HOST, password=DB_PASS_USER, database=DB_DATABASE_NAME)
connection = connector.cursor()
class User:
    def __init__(self, user_id, password):
        from hashlib import sha3_512 as sha3
        password_hashed = sha3(password.encode()).hexdigest()
        connection.execute("SELECT * FROM User WHERE ID = %s AND Password = %s", (user_id, password_hashed))
        temp = connection.fetchall()
        if not temp:
            raise ValueError("Invalid user ID or password")
        
        self.user_id = user_id
        self.hash = password_hashed
        
        connection.execute("SELECT `People ID` FROM User WHERE `ID` = %s", (self.user_id,))
        people_id_result = connection.fetchone()
        if not people_id_result:
            raise ValueError(f"User record for {self.user_id} is incomplete: missing People ID.")
        self.people_id = people_id_result[0]
        
        connection.execute("SELECT `Name` FROM People WHERE `ID` = %s", (self.people_id,))
        name_result = connection.fetchone()
        if not name_result:
            raise ValueError(f"People record not found for People ID: {self.people_id} associated with User: {self.user_id}.")
        self.name = name_result[0]
        
        connection.execute("SELECT `ID` FROM Accounts WHERE `User ID` = %s", (self.user_id,))
        self.accounts = connection.fetchall()
        
        #Making the list of accounts easier to access.
        temp_list = list()
        for account in self.accounts:
            temp_list.append(account[0])
        self.accounts = temp_list
        
        #Fetching the number of accounts linked to this user.
        self.accounts_no = connection.rowcount
        
        #Defaults to no account logged in.
        self.current_account= None
    
    def get_accounts(self):
        """
        Returns a list of all the accounts linked to this user.
        If the user has no accounts, returns an empty list.
        """
        if self.accounts_no == 0:
            return []
        return self.accounts

    def login_account(self, account, password):
        """
        Logs in to an account.
        
        Args:
            account(str): The account id to login to.
            password(str): The password of the account.
            
        Returns:
            bool: True if the account was logged in, else False.
        """
        
        # Checks if the account even belongs to the user.
        if account not in self.accounts:
            return False
        
        #Checks if the account and password are correct.
        
        self.current_account = Account(account, password) 
        if self.current_account.connection:
            return True    
        return False

        
    def logout_account(self):
        """
        Logs out of the current account.
        """
        print("Logging out...")
        self.current_account = None
        print("Logged out.")
        
    def create_account(self, password):
        """
        Creates an account application, which will be sent to the bank for approval.
        
        Args:
            password: The password to be used for the account.
        
        Returns:
            The account number of the account created along with the application id
        """
        
        print("Generating account application for you...")
        from hashlib import sha3_512 as sha3
        hashed_password = sha3(password.encode()).hexdigest()
        account_id = randbytes(20).hex()    
        application_id = randbytes(8).hex()
        
        while True:
            try:
                connection.execute(
                    "INSERT INTO Account_Application (`ID`, `Account_ID`, `User_ID`, `Hash`, `CreationTime`) VALUES (%s, %s, %s, %s, NOW())",
                    (application_id, account_id, self.user_id, hashed_password)
                )
                connector.commit()
                print("Account application sent to the bank for approval.\nYour account number is: " + account_id)
                print("The application id for the account is: " + application_id)
                return account_id, application_id
            except mariadb.IntegrityError as e:
                if 'PRIMARY' in str(e) and 'Account_Application.PRIMARY' in str(e):
                    print(f"Warning: Generated duplicate application ID {application_id}. Retrying with a new one.")
                    application_id = randbytes(8).hex()
                elif 'Account_ID_UNIQUE' in str(e) or ('Account_ID' in str(e) and 'Duplicate entry' in str(e)):
                    print(f"Warning: Generated duplicate account ID {account_id}. Retrying with a new one.")
                    account_id = randbytes(20).hex()
                else:
                    print(f"Database IntegrityError: {e}")
                    raise

    def delete_account(self, account, password, reciever, private_key, confirm = False):
        from Crypto.PublicKey import RSA
        temp=private_key.read()
        temp=temp.encode('utf-8')
        private_key = RSA.import_key(temp)
        if account not in self.accounts:
            return False
        if reciever not in self.accounts and confirm == False:
            sys.stderr.write("Reciever does not belong to the user.")
            sys.stderr.write("THIS WILL TRANSFER ALL YOUR FUNDS TO THE RECIEVER")
            sys.stderr.write("Please add a True parameter to the function to confirm.")
            return False
        public_key = private_key.publickey().export_key()
        
        connection.execute("SELECT `Public Key` FROM People WHERE `ID` = %s", (self.people_id,))
        db_public_key_result = connection.fetchone()

        if not db_public_key_result or db_public_key_result[0].encode('utf-8') != public_key:
            print("Invalid private key or public key mismatch.")
            print("Command Aborted...")
            return False
        
        from Accounts import Account
        account_connection = Account(account, password)
        current_balance = account_connection.get_balance()
        sent = account_connection.send_money(reciever, current_balance)
        
        if sent:
            self.accounts.remove(account)
            self.accounts_no -= 1
            connection.execute("DELETE FROM Accounts WHERE ID = %s AND `User ID` = %s", (account, self.user_id))
            connector.commit()
            return True
        else:
            print("Failed to send money, account deletion aborted.")
            return False
