import hashlib

def sha3_hash(input_string):
    """
    Calculates the SHA3-512 hash of the input string.

    Args:
        input_string (str): The string to be hashed.

    Returns:
        str: The SHA3-512 hash of the input string.
    """
    sha3_hasher = hashlib.sha3_512(input_string.encode())
    return sha3_hasher.hexdigest()

if __name__ == '__main__':
    text = input("Enter the text to hash: ")
    hashed_text = sha3_hash(text)
    print("SHA3-512 Hash:", hashed_text)