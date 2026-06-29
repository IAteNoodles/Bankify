#A class to input a new record in the People table.
#First column is a 32 character ID, which is generated automatically using randombits
#Second column is the name
#Third column is the public key to the generated RSA key pair. This private key is not stored in the database, but is returned to the user. 
import os
from random import randbytes
import mariadb
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER_PEOPLE = os.getenv("DB_USER_PEOPLE")
DB_PASS_PEOPLE = os.getenv("DB_PASS_PEOPLE")
DB_DATABASE_NAME = os.getenv("DB_DATABASE_NAME")

connector = mariadb.connect(user=DB_USER_PEOPLE, host=DB_HOST, passwd=DB_PASS_PEOPLE, database=DB_DATABASE_NAME)
connection = connector.cursor()

def generate_keypair(name):
    #Generates a new key pair.
    from Crypto.PublicKey import RSA
    key = RSA.generate(2048)
    private_key = key.export_key() #Generate private key
    public_key = key.publickey().export_key() #Generate public_key
    #Create a file to store the private key.
    # Ensure the __KEYS directory exists or this will fail
    keys_dir = r"./__KEYS/"
    if not os.path.exists(keys_dir):
        try:
            os.makedirs(keys_dir)
            print(f"Created directory: {keys_dir}")
        except OSError as e:
            print(f"Error creating directory {keys_dir}: {e}")
            raise  # Re-raise if directory creation fails, as key cannot be saved.
            
    file_path = os.path.join(keys_dir, name + "private_key.pem")
    try:
        with open(file_path, "wb") as file:
            file.write(private_key)
        print(f"Successfully generated key pair. Private key saved to {file_path}")
    except IOError as e:
        print(f"Error writing private key to file {file_path}: {e}")
        raise # Re-raise if file writing fails
    return public_key.decode("utf-8") #Decode public and private keys

def generate(name: str):
    """
    
    Inserts a new record in the People table
    
    Args:
        name(str): The name of the person, must be unique.
        
    Returns:
        The ID of the person.
        
    """
    
    #Generate a random 32 character ID
    people_id = randbytes(32).hex()
    
    try:
        public_key = generate_keypair(name) #Generating a new key pair
    except ImportError:
        print("ERROR: PyCryptodome library not found. Please install it: pip install pycryptodome")
        raise
    except Exception as e:
        print(f"Error generating key pair for {name}: {e}")
        raise # Re-raise to indicate failure in key generation

    print(f"Attempting to add {name} to People table with ID {people_id}...")
    try:
        connection.execute(
            "INSERT INTO People (`ID`, `Name`, `Public Key`) VALUES (%s, %s, %s)",
            (people_id, name, public_key)
        )
        connector.commit()
        print("Successfully added record to People table.")
        # This console output can be used to verify against TUI output
        print(f"The generated People ID for '{name}' is: {people_id}") 
        print("Public key stored in the database. Private key file has been saved.")
        return people_id
    except mariadb.Error as e:
        print(f"Database error while inserting person '{name}' (ID: {people_id}): {e}")
        # This error will be caught by Staff.add_person and reported in the TUI
        raise 
    except Exception as e:
        print(f"An unexpected error occurred during database operation for '{name}' (ID: {people_id}): {e}")
        raise

if __name__ == "__main__":
    generate("ROOT@BANK")