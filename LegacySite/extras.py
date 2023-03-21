import json
from binascii import hexlify
from hashlib import sha256
from django.conf import settings
from os import urandom, system
import sys, os
from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from GiftcardSite.keys import FERNET_KEYS

SEED = settings.RANDOM_SEED

LEGACY_ROOT = os.path.dirname(os.path.abspath(__file__))

fernet_instances = [Fernet(key) for key in FERNET_KEYS]
multi_fernet = MultiFernet(fernet_instances)

if sys.platform == 'win32':
    CARD_PARSER = os.path.join(LEGACY_ROOT, '..', 'bins', 'giftcardreader_win.exe')
elif sys.platform == 'linux':
    CARD_PARSER = os.path.join(LEGACY_ROOT, '..', 'bins', 'giftcardreader_linux')
elif sys.platform == 'darwin':
    CARD_PARSER = os.path.join(LEGACY_ROOT, '..', 'bins', 'giftcardreader_mac')
else:
    raise Exception("Unsupported platform: {}".format(sys.platform))

# KG: Something seems fishy here. Why are we seeding here?
def generate_salt(length, debug=True):
    import random
    random.seed(SEED)
    return hexlify(random.randint(0, 2**length-1).to_bytes(length, byteorder='big'))

def hash_pword(salt, pword):
    assert(salt is not None and pword is not None)
    hasher = sha256()
    hasher.update(salt)
    hasher.update(pword.encode('utf-8'))
    return hasher.hexdigest()

def hash_card_file_data(card_file_data):
    assert(card_file_data is not None)
    hasher = sha256()
    hasher.update(card_file_data)
    return hasher.hexdigest()


def parse_salt_and_password(user):
    return user.password.split('$')

def check_password(user, password): 
    salt, password_record = parse_salt_and_password(user)
    verify = hash_pword(salt.encode('utf-8'), password)
    if verify == password_record:
        return True
    return False

def encrypt_card_file_data(card_file_data):
    encrypted_card_file_data = multi_fernet.encrypt(card_file_data.encode())
    return encrypted_card_file_data

def decrypt_card_file_data(encrypted_card_file_data):
    if not isinstance(encrypted_card_file_data, bytes):
        encrypted_card_file_data = encrypted_card_file_data.encode()
    try:
        decrypted_card_file_data = multi_fernet.decrypt(encrypted_card_file_data)
        return decrypted_card_file_data.decode()
    except (InvalidToken, TypeError):
        return None

def write_card_data(card_file_path, product, price, customer):
    data_dict = {}
    data_dict['merchant_id'] = product.product_name
    data_dict['customer_id'] = customer.username
    data_dict['total_value'] = price
    record = {'record_type':'amount_change', "amount_added":2000,}
    record['signature'] = urandom(16).hex()
    data_dict['records'] = [record,]
    with open(card_file_path, 'w') as card_file:
        card_file.write((encrypt_card_file_data(json.dumps(data_dict))).decode('utf-8'))

def parse_card_data(card_file_data, card_path_name):
    if isinstance(card_file_data, str):
        card_file_data = card_file_data.encode()
    # print(card_file_data)
    try:
        decrypted_card_file_data = decrypt_card_file_data(card_file_data)
        return decrypted_card_file_data
    except (InvalidToken, TypeError):
        pass
    with open(card_path_name, 'wb') as card_file:
        card_file.write(card_file_data)
    input_command = f"{CARD_PARSER} 2 {card_path_name} > tmp_file"
    print(f"running: {CARD_PARSER} 2 {card_path_name} > tmp_file")
    ret_val = system(input_command)
    if ret_val != 0:
        return card_file_data
    with open("tmp_file", 'rb') as tmp_file:
        return tmp_file.read()
    
def generate_card_file_path(card_fname, user_id, temp_dir, user_cards=None):
    if card_fname is None or card_fname == '' or not card_fname.isalnum():
        file_name = f'newcard_{user_id}_parser.gftcrd'
    else:
        file_name = f'{card_fname}_{user_id}_parser.gftcrd'

    if user_cards is not None:
        file_name = file_name.replace('_parser', f'_{user_cards}')

    return os.path.join(temp_dir, file_name)
