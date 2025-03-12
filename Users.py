#A class which can be used to access account apis.
#This class is filled with only the base apis. Other features maybe added in future.
from random import randbytes
import sys
import mariadb

from Accounts import Account
connector = mariadb.connect(user='User', host="localhost", password='User@Bank', database='Banking')
connection = connector.cursor()
class User:
    def __init__(self, user_id, password):
        from hashlib import sha3_512 as sha3
        password = sha3(password.encode()).hexdigest()
        connection.execute("SELECT * FROM User WHERE ID = '%s' AND Password = '%s'" % (user_id, password))
        temp = connection.fetchall()
        if temp is None:
            raise ValueError("Invalid user ID or password")
        
        self.user_id = user_id
        self.hash = password
        
        #Fetches the People ID from the Users table.
        connection.execute("SELECT `People ID` FROM User WHERE `ID` = '%s'" % self.user_id)
        self.people_id = connection.fetchone()[0]
        connection.execute("SELECT `Name` FROM People WHERE `ID` = '%s'" % self.people_id)
        self.name = connection.fetchone()[0]
        
        
        #Fetching the accounts linked to this user.
        connection.execute("SELECT `ID` FROM Accounts WHERE `User ID` = '%s'" % (user_id))
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
        password = sha3(password.encode()).hexdigest()
        #Generates a random account number.
        account_id = randbytes(20).hex()    
        
        #Generates a 16 character random string for application id.
        application_id = randbytes(8).hex()
        while(True):
                try:
                    connection.execute("INSERT INTO Account_Application (`ID`,`Account_ID`, `User_ID`, `Hash`, `CreationTime`) VALUES ('%s', '%s', '%s', '%s', NOW())" % (application_id, account_id, self.user_id, password))
                except mariadb.IntegrityError:
                    #Fails as the account number is already taken.
                    #Generates a new account number.
                    account_id = randbytes(20).hex()   
                finally:
                    break 
        connector.commit()
        print("Account application sent to the bank for approval.\nYour account number is: " + account_id)
        print("The application id for the account is: " + application_id)
        return account_id, application_id

    def delete_account(self, account, password, reciever, private_key, confirm = False):
        #"Please enter path of your private key:"))
        #Fetches the public key from the People table, and matches it with the private key.
        from Crypto.PublicKey import RSA
        temp=private_key.read()
        #Convert temp to bytes.
        temp=temp.encode('utf-8')
        private_key = RSA.import_key(temp)
        #Checks if the account even belongs to the user.
        if account not in self.accounts:
            return False
        #Checks if reciever belongs to the user.
        if reciever not in self.accounts and confirm == False:
            sys.stderr.write("Reciever does not belong to the user.")
            sys.stderr.write("THIS WILL TRANSFER ALL YOUR FUNDS TO THE RECIEVER")
            sys.stderr.write("Please add a True parameter to the function to confirm.")
            return False
        #Matches the public key with the private key.
        public_key = private_key.publickey().export_key()
        #TODO check if the private key is correct..
        
        connection.execute("SELECT `Public Key` FROM People WHERE `ID` = '%s'" % self.people_id)
        if connection.fetchone()[0] == public_key:
            print("Invalid private key.")
            print("Command Aborted...")
            return False
        
        #Transferring the money to the reciever.
        
        from Accounts import Account
        account_connection = Account(account, password)
        current_balance = account_connection.get_balance()
        sent = account_connection.send_money(reciever, current_balance)
        self.accounts.remove(account)
        self.accounts_no -= 1
        if sent:
            connection.execute("DELETE FROM Accounts WHERE ID = '%s'" % account)
            connector.commit()
            return True
        else:
            False
