# This class is used to access the staff apis.
# This class is filled with only the base apis. Other features maybe added in future.
import mariadb
connector = mariadb.connect(
    user="Staff", passwd="Staff@Bank", database="Banking")
connection = connector.cursor()

class Staff:

    def __init__(self, staff_id, password):
        from hashlib import sha3_512 as sha3
        connection.execute(
            "SELECT `Password` FROM Staff WHERE ID = '%s'" % staff_id)
        hash = sha3(password.encode()).hexdigest()
        db_hash = connection.fetchone()[0]
        # Checks if there is a user with the given ID and password.
        if db_hash != hash:
            raise ValueError("Invalid staff ID or password")

        self.user_id = staff_id
        self.password = password
        
        self.type = 0
        print("Logged in as staff with ID %s and type %s" %
              (self.user_id, self.type))
        return True
        

    def get_type(self): 
        return "Staff" if self.type == 0 else "Manager" if self.type == 1 else "Admin"
    
    def add_user(self, people_id ,user_id, hashed_passwd):
        """
        Inserts a user into the user table with the hashed password.
        """
        #Checks if the people_id is in the database.
        connection.execute("SELECT * FROM People WHERE ID = '%s'" % people_id)
        if connection.fetchone() is None:
            print("There is no record of the person with ID %s" % people_id)
            print("User not added.")
            return False
        #Checks if there is a user with the given ID
        connection.execute("SELECT * FROM User WHERE ID = '%s'" % user_id)
        if not connection.fetchone() is None:
            print("There is already a user with ID %s" % user_id)
            print("User not added.")
            return False
        print("Adding user...")
        connection.execute(
            "INSERT INTO User (`People ID`, `ID`, `Password`) VALUES ('%s', '%s', '%s')" % (people_id, user_id, hashed_passwd))
        connector.commit()
        print("Added user with ID %s" % user_id)
        return True

    def change_application(self, application_id: str, accept: bool):
        """

        Commits changes to the application.

        Args:
            application_id(int): The application ID.
            accept(bool): True if the application is accepted, False if rejected.

        Returns:
            True if the actions were executed successfully, else False.
        """

        # Fetches the application from the database and prints the details.
        connection.execute("SELECT * FROM Account_Application WHERE ID = '%s'" % application_id)
        details = connection.fetchone()
        if details is None:
            return False
        # Print the details of the application. 1st column is the application_id, 2nd is the user_id, 3rd is the account_id, 4th is the hash of the password, 5th is the time of the creation.
        print("Application ID: " + application_id)
        print("User ID: " + str(details[1]))
        print("Account ID: " + str(details[2]))
        print("Created at: " + str(details[4]))


        def delete_application():
            """
            Deletes the application.
            """
            connection.execute(
                "DELETE FROM Account_Application WHERE ID = '%s'" % (application_id))
            connector.commit()

        if accept:
            # If yes, the application is accepted.
            # Creates a new account in the Accounts table with the hashed password
            print("Accepting application...")
            print("Creating new account...")
            connection.execute(
                "INSERT INTO Accounts (`User ID`, `ID`, `Password`) VALUES ('%s', '%s', '%s')" % (details[1], details[2], details[3]))
            print("Account created.")
            delete_application()
            print("Deleting application...")
            print("Application deleted.")
            connector.commit()
            return True
        else:
            # If no, the application is rejected.
            delete_application()
            print("Rejecting application...")
            print("Application deleted.")
            connector.commit()
            return True


class Manager(Staff):
    def __init__(self, user_id, password):
        super(Manager, self).__init__(user_id, password)
        self.type = 1

    def add_staff(self, people_id, staff_id, hashed_passwd, staff_type):
        """
        Inserts a staff into the staff table with the hashed password.

        Args:
            people_id: The ID of the person.
            staff_id: ID of the staff.
            hashed_passwd: Hash of the staff's password.
            staff_type: Type of the staff (Admin: 2 | Manager:1 | Staff:0)
        """
        if staff_type > self.type:
            print("You are not authorized to add this staff")
            return False
        print("Adding staff...")
        connection.execute("INSERT INTO Staff (`People ID`, `ID`, `Password`, `Type`) VALUES ('%s', '%s', '%s', %s)" %
                           (people_id, staff_id, hashed_passwd, staff_type))
        connector.commit()
        print("Added staff with ID %s" % staff_id + " and type %s" % staff_type)
        return True

class Admin(Manager):
    def __init__(self, user_id, password):
        super(Admin, self).__init__(user_id, password)
        self.type = 2

    def remove_staff(self, staff_id):
        """
        Removes a staff from the staff table.

        Args:
            staff_id: ID of the staff.
        """
        connection.execute("SELECT `Type` FROM Staff WHERE ID = '%s'" % staff_id)
        if connection.fetchone()[0] > self.type:
            print("You are not authorized to remove this staff")
            return False
        print("This will remove staff with ID %s" % staff_id)
        print("Removing staff...")
        connection.execute("DELETE FROM Staff WHERE ID = '%s'" % staff_id)
        connector.commit()
        
        print("Removed staff with ID %s" % staff_id)
        return True
