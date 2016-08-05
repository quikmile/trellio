import binascii
from os import urandom


def unique_hex(byte_length=4):
    return binascii.hexlify(urandom(byte_length)).decode()
