from django.db import models

from ..aescipher import encrypt, decrypt
from .authenticationmethods_model import AuthenticationMethods


class Authentication(models.Model):

    """Model for keeping authentication information."""

    # User login for websites, network drives etc.
    username = models.CharField(max_length=1024, unique=False, blank=True, default='',
                                verbose_name='Brugernavn')

    # One of the two encryption keys for decrypting the password
    iv = models.BinaryField(max_length=32, unique=False, blank=True,
                            verbose_name='InitialiseringsVektor')

    # The encrypted password
    ciphertext = models.BinaryField(max_length=1024, unique=False, blank=True,
                                    verbose_name='Password')

    domain = models.CharField(max_length=2024, unique=False, blank=True, default='',
                              verbose_name='Brugerdomæne')

    models.ForeignKey(AuthenticationMethods,
                      null=True,
                      related_name='authentication_method',
                      verbose_name='Login Metode')

    def get_password(self):
        return decrypt(bytes(self.iv), bytes(self.ciphertext))

    def set_password(self, password):
        self.iv, self.ciphertext = encrypt(password)
