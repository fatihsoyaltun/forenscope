from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    phone = models.CharField(max_length=20, blank=True, verbose_name='Telefon')
    department = models.CharField(max_length=128, blank=True, verbose_name='Departman')

    class Meta:
        verbose_name = 'Kullanıcı'
        verbose_name_plural = 'Kullanıcılar'

    def __str__(self):
        return self.get_full_name() or self.username
