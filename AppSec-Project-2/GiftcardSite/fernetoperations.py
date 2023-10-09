from cryptography.fernet import Fernet, InvalidToken
from base64 import urlsafe_b64decode

# Validate an existing key
def is_fernet_key_valid(key):
    try:
        # Attempt to decode the key
        decoded_key = urlsafe_b64decode(key)

        # Check if the decoded key has the correct length (32 bytes)
        if len(decoded_key) != 32:
            return False

        # Create a Fernet object using the key
        fernet = Fernet(key)

        # Test encrypt/decrypt with a dummy value
        test_value = b'My validation check.'
        encrypted = fernet.encrypt(test_value)
        decrypted = fernet.decrypt(encrypted)

        # Check if the decrypted value matches the original test value
        return decrypted == test_value
    except (InvalidToken, ValueError):
        # Catch exceptions related to invalid keys or decoding issues
        return False

# Generate a new fernet key
def generate_fernet_key():
    # Generate a Fernet key and return it as a string
    return Fernet.generate_key().decode()

# Prompt the user to select an operation
option = input("Select Operation\n1: Generate a new fernet key\n2: Verify if an entered key is a valid fernet key\nInput: ")

# Generate a new Fernet key
if option == "1":
    generated_key = generate_fernet_key()
    print(f"\nThe key generated is {generated_key}\n")
# Validate an existing Fernet key
elif option == "2":
    key_to_validate = input("\nEnter the key you want to verify: ")
    result = is_fernet_key_valid(key_to_validate)
    if result:
        print("\nThe entered key is a Valid fernet key\n")
    else:
        print("\nThe entered key is an Invalid fernet key\n")
# Handle invalid operation selection
else:
    print("Wrong operation selected. Exiting.")
