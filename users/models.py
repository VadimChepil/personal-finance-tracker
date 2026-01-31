from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class UserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)    

    def create_superuser(self, email, password=None, **extra_fields):
        # Automatically grant administrator rights
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    # Disable the standard username, use email instead
    username = None
    email = models.EmailField('email address', unique=True)

    # Tell Django to use email for authentication
    USERNAME_FIELD = 'email'
    # Empty - Django automatically queries USERNAME_FIELD and password
    REQUIRED_FIELDS = [] 

    objects = UserManager()