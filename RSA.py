def __generate_new_private_key(bytes: int = 2048) -> tuple:
    """
    Generates a new private and public key pair.

    Args:
        bytes (int): The number of bytes to use for the key. Default is 2048.
    """
    from Crypto.PublicKey import RSA
    key = RSA.generate(bytes)
    private_key = key.export_key()
    public_key = key.publickey().export_key()
    return private_key, public_key

