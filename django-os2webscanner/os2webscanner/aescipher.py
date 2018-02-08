import binascii
from Crypto.Util import Counter
from Crypto.Cipher import AES
from Crypto import Random

# AES supports multiple key sizes: 16 (AES128), 24 (AES192), or 32 (AES256).
key_bytes = 32


class AESCipher:
    def __init__(self):
        pass

    # Takes as input a 32-byte key and an arbitrary-length plaintext and returns a
    # pair (iv, ciphtertext). "iv" stands for initialization vector.
    def encrypt(self, key, plaintext):
        assert len(key) == key_bytes

        # Choose a random, 16-byte IV.
        iv = Random.new().read(AES.block_size)

        # Convert the IV to a Python integer.
        iv_int = int(binascii.hexlify(iv), 16)

        # Create a new Counter object with IV = iv_int.
        ctr = Counter.new(AES.block_size * 8, initial_value=iv_int)

        # Create AES-CTR cipher.
        aes = AES.new(key, AES.MODE_CTR, counter=ctr)

        # Encrypt and return IV and ciphertext.
        ciphertext = aes.encrypt(plaintext)
        return (iv, ciphertext)

    # Takes as input a 32-byte key, a 16-byte IV, and a ciphertext, and outputs the
    # corresponding plaintext.
    def decrypt(self, key, iv, ciphertext):
        assert len(key) == key_bytes

        # Initialize counter for decryption. iv should be the same as the output of
        # encrypt().
        iv_int = int(iv.encode('hex'), 16)
        ctr = Counter.new(AES.block_size * 8, initial_value=iv_int)

        # Create AES-CTR cipher.
        aes = AES.new(key, AES.MODE_CTR, counter=ctr)

        # Decrypt and return the plaintext.
        plaintext = aes.decrypt(ciphertext)
        return plaintext


def main():
    aes = AESCipher()
    # Nominal way to generate a fresh key. This calls the system's random number
    # generator (RNG).
    key1 = Random.new().read(key_bytes)
    iv, ciphertext = aes.encrypt(key1, 'danni#!')
    print iv
    print ciphertext
    decrypted = aes.decrypt(key1, iv, ciphertext)
    print decrypted


if __name__ == '__main__':
    main()
