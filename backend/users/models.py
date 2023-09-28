import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """User model"""
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)