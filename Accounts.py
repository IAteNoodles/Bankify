#A class which can be used to access account apis.
#This class is filled with only the base apis. Other features maybe added in future.
from hashlib import new
import mariadb
connector = mariadb.connect(user='Account',host = "localhost", password='Account@Bank', database='Banking')
connection = connector.cursor()
class Account:
    def __init__(self, account_id, password):
        from hashlib import sha3_512 as sha3
        password = sha3(password.encode()).hexdigest()
        connection.execute("SELECT * FROM Accounts WHERE ID = %s AND Password = %s", (account_id, password))
        #Checks if there is a account with the given ID and password.
        
        if connection.fetchone() is None:
            raise ValueError("Invalid account ID or password")

        self.account_id = account_id
        self.hash = password    
        
        #Fetches account balance from the database.
        connection.execute("SELECT Balance FROM Accounts WHERE ID = '%s'" % self.account_id)
        self.balance = connection.fetchone()[0]
        self.connection = True
        
    def get_balance(self):
        """
        
        Fetches the account's balance from the database, and updates the balance attribute.
                
        Retuns: The current balance of the account.
        """
        connection.execute("SELECT Balance FROM Accounts WHERE ID = '%s'" % self.account_id)
        self.balance = connection.fetchone()[0]
        return self.balance
            
    
    def commit_transaction(self, amount, mode):
        """
        
        Commits a transaction to the account's account in the database.
        
        Args:
            amount(int): The amount.
            mode(int): The transaction mode. (Deposit:1 or Withdraw:0)
        
        Retuns:
            True if the transaction was successful, along with new balance.
            False if the transaction was unsuccessful, along with the error message.
        """
        #Check if the account has entered a valid mode.
        if mode == 1:
            balance = self.balance + amount
            if amount < 0:
                print("You cannot deposit a negative amount.")
                return False

        elif mode == 0:
            balance = self.balance - amount
        else:
            print("Invalid mode\nValid modes are: 0 for withdraw, 1 for deposit")
            return False
        
        #Check if the account has enough money to make the transaction.
        if balance < 0:
            print("Your account balance is: " + str(self.balance))
            print("After this transaction your balance would be: " + str(self.balance - amount))
            print("You do not have enough money to make this transaction.")
            return False, "Insufficient funds"
        
        #Commits the transaction to the database.
        connection.execute("UPDATE Accounts SET Balance = %s WHERE ID = '%s'" % (balance, self.account_id))
        connector.commit()
        self.balance = balance
        print("New balance: %s" % self.balance)
        return True, 
    
    def send_money(self, reciever, amount):
        """
        Sends money to the recipient.
        
        Args:
            reciever(str): The accound id of the recipient.
            amount(int): The amount to send.
            
        Returns:
            True if the transaction was successful, else false.
        """
        if self.get_balance() - amount < 0:
            return False
        
        connection.execute("SELECT Balance FROM Accounts WHERE ID = '%s'" % reciever)
        new_balance = connection.fetchone()[0] + amount
        #Send money to the recipient.
        connection.execute("UPDATE Accounts SET Balance = %s WHERE ID = '%s'" % (new_balance, reciever))
        #Update the sender's balance.
        connection.execute("UPDATE Accounts SET Balance = %s WHERE ID = '%s'" % (self.balance - amount, self.account_id))
        #Commit the transaction.
        connector.commit()
        #Update the sender's balance.
        self.get_balance()
        return True

    def get_card_list(self, includeExpired=False, **kwargs):
        """
        Retrieves all cards associated with the account.
        
        Args:
            includeExpired(bool): Whether to include expired cards.
            **kwargs: The search parameters.
            
        Returns:
            list: A list of cards.
        """
        query = "SELECT * FROM Cards WHERE Account = '%s'" % self.account_id
        if not includeExpired:
            query += " AND Expiry > NOW()"
        for key, value in kwargs.items():
            query += " AND " + key + " = " + value
        connection.execute(query)
        return connection.fetchall()
    
    def request_card(self, cardType, **kwargs):
        """
        Requests a new card.
        
        Args:
            cardType(str): The type of card.
            **kwargs: The card details.
            
        Returns:
            None
        """
        query = "INSERT INTO Cards (Account, Type, "
        values = "'%s', '%s', " % (self.account_id, cardType)
        for key, value in kwargs.items():
            query += key + ", "
            values += value + ", "
        query = query[:-2] + ") VALUES (" + values[:-2] + ")"
        connection.execute(query)
        connector.commit()
#---------------------------------------------------------------- END OF CLASS -----------------------------------------------------------------#
        
        
        
