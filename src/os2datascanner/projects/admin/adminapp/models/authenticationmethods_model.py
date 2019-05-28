from django.db import models


class AuthenticationMethods(models.Model):

    """Model for keeping """

    methodname = models.CharField(max_length=1024, unique=True,
                                  verbose_name='Login method')
