import django

from os2datascanner.projects.admin.adminapp.aescipher import encrypt, decrypt
from os2datascanner.projects.admin.adminapp.models.authentication_model import Authentication


class AESCipherTest(django.test.TestCase):

    def test_encrypt_decrypt(self):
        password_to_encrypt = 'hemmeligtpassword'
        iv, ciphertext = encrypt(password_to_encrypt)
        password_after_decrypt = decrypt(iv, ciphertext)
        self.assertEqual(password_to_encrypt, password_after_decrypt)

    def test_storing_and_retrieving_authentication_data(self):
        password_to_encrypt = 'top_secret'
        iv, ciphertext = encrypt(password_to_encrypt)
        Authentication.objects.create(
            username='jasper',
            iv=iv,
            ciphertext=ciphertext
        )
        stored_auth = Authentication.objects.filter()[:1].get()
        password_after_decrypt = decrypt(bytes(stored_auth.iv), bytes(stored_auth.ciphertext))
        self.assertEqual(password_to_encrypt, password_after_decrypt)
