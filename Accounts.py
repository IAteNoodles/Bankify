#A class which can be used to access account apis.
#This class is filled with only the base apis. Other features maybe added in future.
from hashlib import new
import mariadb
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER_ACCOUNT = os.getenv("DB_USER_ACCOUNT")
DB_PASS_ACCOUNT = os.getenv("DB_PASS_ACCOUNT")
DB_DATABASE_NAME = os.getenv("DB_DATABASE_NAME")

connector = mariadb.connect(user=DB_USER_ACCOUNT, host=DB_HOST, password=DB_PASS_ACCOUNT, database=DB_DATABASE_NAME)
connection = connector.cursor()
class Account:
    def __init__(self, account_id, password):
        from hashlib import sha3_512 as sha3
        password_hash = sha3(password.encode()).hexdigest() # Renamed for clarity
        # Parameterized query
        connection.execute("SELECT * FROM Accounts WHERE ID = %s AND Password = %s", (account_id, password_hash))
        
        if connection.fetchone() is None:
            raise ValueError("Invalid account ID or password")

        self.account_id = account_id
        self.hash = password_hash    
        
        # Parameterized query
        connection.execute("SELECT Balance FROM Accounts WHERE ID = %s", (self.account_id,))
        balance_from_db = connection.fetchone()
        if balance_from_db is None:
            # This case should ideally not happen if __init__ succeeded with ID/password check
            # but indicates a problem if the account exists but has no balance record or was deleted concurrently.
            raise ValueError(f"Account {self.account_id} found but balance is missing.")
        self.balance = float(balance_from_db[0])
        self.connection = True # Assuming this indicates a successful login to the account object
        
    def get_balance(self):
        """
        Fetches the account's balance from the database, and updates the balance attribute.
        Returns: The current balance of the account (float).
        """
        # Parameterized query
        connection.execute("SELECT Balance FROM Accounts WHERE ID = %s", (self.account_id,))
        balance_from_db = connection.fetchone()
        if balance_from_db is None:
            # This could happen if the account was deleted after object creation
            raise ValueError(f"Account {self.account_id} not found when trying to get balance.")
        self.balance = float(balance_from_db[0])
        return self.balance
            
    
    def commit_transaction(self, amount: float, mode: int) -> tuple[bool, float | str]:
        """
        Commits a transaction to the account's account in the database.
        
        Args:
            amount(float): The amount.
            mode(int): The transaction mode. (Deposit:1 or Withdraw:0)
        
        Returns:
            tuple: (True, new_balance) if the transaction was successful.
                   (False, error_message_string) if the transaction was unsuccessful.
        """
        try:
            current_balance = float(self.get_balance()) # Refresh balance from DB
            transaction_amount = float(amount)

            if mode == 1: # Deposit
                if transaction_amount < 0:
                    return False, "You cannot deposit a negative amount."
                new_balance = current_balance + transaction_amount
            elif mode == 0: # Withdraw
                if transaction_amount < 0:
                    return False, "You cannot withdraw a negative amount."
                if current_balance - transaction_amount < 0:
                    return False, f"Insufficient funds. Current balance: {current_balance}, trying to withdraw: {transaction_amount}"
                new_balance = current_balance - transaction_amount
            else:
                return False, "Invalid mode. Valid modes are: 0 for withdraw, 1 for deposit."
            
            # Parameterized query
            connection.execute("UPDATE Accounts SET Balance = %s WHERE ID = %s", (new_balance, self.account_id))
            connector.commit() # Crucial: commit the change
            self.balance = new_balance # Update internal balance state
            print(f"Transaction successful. New balance for account {self.account_id}: {self.balance}")
            return True, self.balance
        except mariadb.Error as e:
            # Log error e if necessary
            return False, f"Database error during transaction: {e}"
        except ValueError as e: # Catch errors from get_balance if account disappears
            return False, str(e)
        except Exception as e:
            # Log error e if necessary
            return False, f"An unexpected error occurred during transaction: {e}"
    
    def send_money(self, receiver_account_id: str, amount: float) -> tuple[bool, float | str]:
        """
        Sends money to the recipient.
        
        Args:
            receiver_account_id(str): The account id of the recipient.
            amount(float): The amount to send.
            
        Returns:
            tuple: (True, new_sender_balance) if the transaction was successful.
                   (False, error_message_string) if unsuccessful.
        """
        try:
            current_sender_balance = float(self.get_balance()) # Refresh sender's balance from DB
            transfer_amount = float(amount)

            if transfer_amount <= 0:
                return False, "Transfer amount must be positive."

            if current_sender_balance - transfer_amount < 0:
                return False, f"Insufficient funds. Your balance: {current_sender_balance}, trying to send: {transfer_amount}"
            
            # Parameterized query for fetching receiver's balance
            connection.execute("SELECT Balance FROM Accounts WHERE ID = %s", (receiver_account_id,))
            recipient_balance_from_db = connection.fetchone()
            if recipient_balance_from_db is None:
                return False, f"Recipient account {receiver_account_id} not found."
            
            current_recipient_balance = float(recipient_balance_from_db[0])
            
            new_recipient_balance = current_recipient_balance + transfer_amount
            new_sender_balance = current_sender_balance - transfer_amount
            
            # Use a transaction block to ensure atomicity if supported and configured, 
            # or at least ensure both updates happen before commit.
            # For mariadb.connector, autocommit is often on by default unless a transaction is explicitly started.
            # We'll rely on a single commit after both updates.

            # Parameterized query for updating receiver
            connection.execute("UPDATE Accounts SET Balance = %s WHERE ID = %s", (new_recipient_balance, receiver_account_id))
            # Parameterized query for updating sender
            connection.execute("UPDATE Accounts SET Balance = %s WHERE ID = %s", (new_sender_balance, self.account_id))
            
            connector.commit() # Crucial: commit both changes together
            
            self.balance = new_sender_balance # Update sender's internal balance state
            print(f"Transfer successful. New balance for account {self.account_id}: {self.balance}")
            return True, self.balance
        except mariadb.Error as e:
            # Log error e if necessary
            # Consider a rollback here if a transaction was explicitly started
            return False, f"Database error during transfer: {e}"
        except ValueError as e: # Catch errors from get_balance if account disappears
            return False, str(e)
        except Exception as e:
            # Log error e if necessary
            return False, f"An unexpected error occurred during transfer: {e}"

#---------------------------------------------------------------- END OF CLASS -----------------------------------------------------------------#



