# This class is used to access the staff apis.
# This class is filled with only the base apis. Other features maybe added in future.
import mariadb
import datetime
from Users import User
from Accounts import Account
from People import generate as generate_person_record # Added import
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

class Staff:

    def __init__(self, staff_id, password):
        from hashlib import sha3_512 as sha3
        # Fetch Password and Type from Staff table
        connection.execute("SELECT `Password`, `Type` FROM Staff WHERE ID = %s", (staff_id,))
        result = connection.fetchone()
        if not result:
            raise ValueError("Invalid staff ID or password - ID not found")
        
        db_hash, staff_type_from_db = result[0], result[1]
        
        hash_input = sha3(password.encode()).hexdigest()
        
        if db_hash != hash_input:
            raise ValueError("Invalid staff ID or password - Password mismatch")

        self.user_id = staff_id
        # Storing plain password here is a security risk, consider removing if not essential for other methods
        # self.password = password 
        
        self.type = staff_type_from_db # Set type from the database
        print(f"Logged in as staff with ID {self.user_id} and type {self.type}")
        

    def get_type(self): 
        return self.type
    
    def add_user(self, people_id: str, user_id: str, hashed_passwd: str) -> tuple[bool, str]:
        """
        Inserts a user into the user table with the hashed password.
        Returns a tuple: (success_status, message).
        success_status (bool): True if user added successfully, False otherwise.
        message (str): A message indicating success or the reason for failure.
        """
        try:
            # Check if the people_id is in the database.
            connection.execute("SELECT ID FROM People WHERE ID = %s", (people_id,))
            if connection.fetchone() is None:
                return False, f"Person with People ID '{people_id}' does not exist."
            
            # Check if there is a user with the given User ID already
            connection.execute("SELECT ID FROM User WHERE ID = %s", (user_id,))
            if connection.fetchone() is not None:
                return False, f"User with User ID '{user_id}' already exists."

            # Add user
            connection.execute(
                "INSERT INTO User (`People ID`, `ID`, `Password`) VALUES (%s, %s, %s)",
                (people_id, user_id, hashed_passwd)
            )
            connector.commit()
            return True, f"User '{user_id}' added successfully for People ID '{people_id}'."
        except mariadb.Error as e:
            return False, f"Database error: {e}"
        except Exception as e:
            return False, f"An unexpected error occurred: {e}"

    def get_applications(self, status: int | None = None):
        """
        Retrieves account applications from the database.

        Args:
            status (int, optional): Filter applications by status.
                                    0 = Rejected, 1 = Approved (and processed), 2 = Pending.
                                    If None, all applications are fetched.

        Returns:
            list: A list of tuples, where each tuple represents an application
                  (ID, User_ID, Account_ID, Hashed Password, Creation Time, Status).
        """
        query = "SELECT ID, `User_ID`, `Account_ID`, `Hash`, `CreationTime`, `Status` FROM Account_Application"
        params = []
        if status is not None:
            query += " WHERE Status = %s"
            params.append(status)
        
        connection.execute(query, tuple(params))
        applications = connection.fetchall()
        return applications

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
        connection.execute("SELECT `ID`, `User_ID`, `Account_ID`, `Hash`, `CreationTime`, `Status` FROM Account_Application WHERE ID = '%s'" % application_id)
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
            
            # Update status in Account_Application table to 1 (Approved)
            print("Updating application status to approved...")
            connection.execute(
                "UPDATE Account_Application SET Status = 1 WHERE ID = '%s'" % application_id
            )
            # delete_application() # Original call, commented out to keep the record with status 1
            # print("Deleting application...") 
            # print("Application deleted.")
            print("Application status updated to approved.")
            connector.commit()
            return True
        else:
            # If no, the application is rejected.
            # Update the status in Account_Application table to 0 (Rejected)
            print("Rejecting application...")
            connection.execute(
                "UPDATE Account_Application SET Status = 0 WHERE ID = '%s'" % application_id
            )
            print("Application status updated to rejected.")
            connector.commit()
            return True

    def add_person(self, name: str) -> tuple[bool, str]:
        """
        Adds a new person to the system using People.generate_person_record.
        Returns a tuple: (success_status, message_or_person_id).
        success_status (bool): True if person added successfully, False otherwise.
        message_or_person_id (str): The new person_id if successful, or an error message if not.
        """
        try:
            # Check if a person with the same name already exists to avoid duplicate names if that's a business rule.
            # This check should ideally be in People.py or handled by a unique constraint in the DB.
            connection.execute("SELECT ID FROM People WHERE Name = %s", (name,))
            if connection.fetchone() is not None:
                return False, f"A person with the name '{name}' already exists."

            # Call the imported generate_person_record function from People.py
            person_id = generate_person_record(name) # This now directly calls People.generate
            if person_id:
                # The People.generate function now prints the ID to console upon generation.
                # We return it here for the TUI.
                return True, person_id
            else:
                # This case should ideally not be reached if People.generate raises exceptions on failure.
                return False, "Failed to generate person ID, but no specific error was raised."

        except mariadb.Error as e:
            # Handle database errors that might occur during the name check or if generate_person_record raises one
            return False, f"Database error: {e}"
        except ImportError as e: # Specifically catch if Crypto is missing
            return False, f"Missing required library for key generation: {e}. Please install pycryptodome."
        except Exception as e:
            # Catch any other exceptions from generate_person_record (like key generation issues)
            return False, f"An error occurred while adding person: {e}"

class Manager(Staff):
    def __init__(self, user_id, password):
        super().__init__(user_id, password)
        # Password and type are now set by Staff.__init__
        # Verify that the fetched type is appropriate for a Manager
        # Type 1 for Manager, Type 2 for Admin (Admin is also a Manager)
        if self.type < 1: 
            raise ValueError(f"Staff member {user_id} (Type: {self.type}) is not authorized as a Manager.")
        # self.type is already correctly set by super().__init__
        # No need to explicitly set self.type = 1 here unless you want to override Admin's type, which is unlikely.

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
        super().__init__(user_id, password)
        # Password and type are now set by Manager.__init__ (which calls Staff.__init__)
        # Verify that the fetched type is appropriate for an Admin
        # Type 2 for Admin
        if self.type != 2:
            raise ValueError(f"Staff member {user_id} (Type: {self.type}) is not authorized as an Admin.")
        # self.type is already correctly set by super().__init__

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
