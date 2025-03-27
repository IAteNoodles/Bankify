"""
People Management Module

This module handles the logic for managing people in the database. It includes functionality
for generating unique IDs, creating RSA key pairs, and verifying public/private key pairs.

Classes:
    People: Represents a person in the database and provides methods for managing their data.

Environment Variables:
    PRIVATE_KEY_DIR: Directory where private keys are stored.
    DB_USER: Database username.
    DB_PASSWORD: Database password.
    DB_HOST: Database host.
    DB_NAME: Database name.
"""

import os
import mariadb
from dotenv import load_dotenv
from Crypto.PublicKey import RSA
from random import randbytes
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S", handlers=[logging.FileHandler("People.log"), logging.StreamHandler()])

# Directory for storing private keys
PRIVATE_KEY_DIR = os.getenv("PRIVATE_KEY_DIR")


class People:
    """
    Represents a person in the database.

    This class provides functionality for creating a new person, generating RSA key pairs,
    and verifying the integrity of public/private keys.

    Attributes:
        connection (mariadb.connections.Connection): The database connection object.
        id (str): The unique ID of the person.
    """

    def __init__(self, connection: mariadb.connections.Connection, generate_id: bool = False, **kwargs):
        """
        Initializes a People object.

        Args:
            connection (mariadb.connections.Connection): The database connection object.
            generate_id (bool): Whether to generate a new ID and key pair for the person.
            **kwargs: Additional keyword arguments. Must include:
                - name (str): The name of the person (required if generate_id is True).
                - ID (str): The unique ID of the person (required if generate_id is False).

        Raises:
            FileNotFoundError: If the private key file is not found.
            ValueError: If the public key does not match the private key.
        """
        self.connection = connection

        if generate_id:
            self.id, private_key = self.__generate_user__(kwargs["name"])
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO People (`ID`, `Name`, `Public Key`) VALUES (%s, %s, %s)",
                    (self.id, kwargs["name"], private_key)
                )
                self.connection.commit()
        else:
            self.id = kwargs["ID"]
            private_key_path = os.path.join(PRIVATE_KEY_DIR, kwargs["name"] + ".pem")
            if not os.path.exists(private_key_path):
                raise FileNotFoundError("Private key not found.")
            with open(private_key_path, "rb") as private_key_file:
                private_key = private_key_file.read()

            with self.connection.cursor() as cursor:
                cursor.execute("SELECT `Public Key` FROM People WHERE `ID` = %s LIMIT 1", (self.id,))
                __PUBLIC_KEY = cursor.fetchone()[0]

            private_key_obj = RSA.import_key(private_key)
            if private_key_obj.public_key().export_key().decode("utf-8") != __PUBLIC_KEY:
                raise ValueError("Public key does not match private key.")
            logging.info("Public key matches private key.")

    def __generate_user__(self, name: str):
        """
        Generates a new user with a unique ID and RSA key pair.

        This method creates a private key file in the directory specified by the
        PRIVATE_KEY_DIR environment variable.

        Args:
            name (str): The name of the person.

        Returns:
            tuple: A tuple containing:
                - str: The unique ID of the person.
                - str: The public key of the person.

        Raises:
            OSError: If the private key directory cannot be created.
        """
        os.makedirs(PRIVATE_KEY_DIR, exist_ok=True)
        key = RSA.generate(2048)
        private_key = key.export_key()
        public_key = key.publickey().export_key()

        private_key_path = os.path.join(PRIVATE_KEY_DIR, name + ".pem")
        with open(private_key_path, "wb") as private_key_file:
            private_key_file.write(private_key)

        logging.info("Successfully generated key pair.")
        return randbytes(32).hex(), public_key.decode("utf-8")

    def __renew_key__(self):
        """
        Renews the public key of the person and updates it in the database
        """
        with self.connection.cursor() as cursor:
            private_key = RSA.generate(2048).export_key()
            public_key = RSA.import_key(private_key).publickey().export_key()
            cursor.execute("UPDATE People SET `Public Key` = %s WHERE `ID` = %s", (public_key, self.id))
            self.connection.commit()

    def __delattr__(self):
        """
        Deletes the entry of the person from the database and closes the connection.

        Raises:
            ValueError: If the person does not exist in the database.
        """
        with self.connection.cursor() as cursor:
            
            # Throws an error if the person does not exist in the database
            cursor.execute("SELECT * FROM People WHERE `ID` = %s", (self.id,))
            if not cursor.fetchone():
                raise ValueError("Person does not exist in the database.")
            cursor.execute("DELETE FROM People WHERE `ID` = %s", (self.id,))
            self.connection.commit()
        self.connection.close()
                   
# Example usage
if __name__ == "__main__":
    """
    Example usage of the People class.

    This script demonstrates how to create a new person in the database or verify an
    existing person's public/private key pair.
    """
    connection = mariadb.connect(
        user=os.getenv("DB_USER"),
        host=os.getenv("DB_HOST"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

    # Create a new person
    new_People = People(connection=connection, generate_id=True, name="Noodles")
    ID = new_People.id

    # Verify an existing person
    People(connection=connection, ID=new_People.id, name="Noodles")