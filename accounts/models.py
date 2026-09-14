from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

    @property
    def full_name(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name or self.email
