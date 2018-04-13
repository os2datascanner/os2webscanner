import unittest
from ..aescipher import encrypt, decrypt


class AESCipherTest(unittest.TestCase):

    def test_encrypt_decrypt(self):
        password_to_encrypt = 'hemmeligtpassword'
        iv, ciphertext = encrypt(password_to_encrypt)
        password_after_decrypt = decrypt(iv, ciphertext)
        self.assertEqual(password_to_encrypt, password_after_decrypt)


def main():
    """Run the unit tests."""
    unittest.main()


if __name__ == '__main__':
    main()