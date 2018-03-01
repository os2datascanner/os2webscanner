from django.db import models

from authenticationmethods_model import AuthenticationMethods


class Authentication(models.Model):

    """Model for keeping authentication information."""

    # User login for websites, network drives etc.
    username = models.CharField(max_length=1024, unique=False, blank=True, default='',
                                verbose_name='Bruger navn')

    # One of the two encryption keys for decrypting the password
    iv = models.BinaryField(max_length=32, unique=False, blank=True,
                            verbose_name='InitialiseringsVektor')

    # The encrypted password
    ciphertext = models.BinaryField(max_length=1024, unique=False, blank=True,
                                    verbose_name='Password')

    models.ForeignKey(AuthenticationMethods,
                      null=True,
                      related_name='authentication_method',
                      verbose_name='Login Metode')
