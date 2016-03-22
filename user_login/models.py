from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin
)

# Create your models here.


class MyUserManager(BaseUserManager):
    def _create_user(self, email, name, mobile, user_type, password):
        is_superuser = False
        is_staff = False
        if not email:
            raise ValueError('Users must have an email')
        if not name:
            raise ValueError('Users must have a name')
        if user_type in ('S', 'A'):
            is_staff = True
        if user_type is 'A':
            is_superuser = True
        user = self.model(
            email=self.normalize_email(email),
            name=name,
            mobile=mobile,
            user_type=user_type,
            is_staff=is_staff,
            is_active=True,
            is_superuser=is_superuser,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, name, user_type, mobile=None, password=None):
        return self._create_user(email, name, mobile, user_type, password)

    def create_superuser(self, email, name, password):
        return self._create_user(email, name, None, 'A', password)


class MyUser(AbstractBaseUser, PermissionsMixin):  # Login panel - 3 necessary details - name, email, password
    #  For transaction / Getting coupons
    email = models.EmailField(max_length=255, unique=True)  # To be verified at a later phase
    name = models.CharField(max_length=50)  # company name / Promoter's first name
    mobile = models.CharField(max_length=10, blank=True, null=True)

    USER_TYPE = (
        ('C', 'Client'),
        ('P', 'Promoter'),
        ('S', 'Staff'),
        ('A', 'Superuser'),
    )
    user_type = models.CharField(max_length=1, choices=USER_TYPE, verbose_name='User type')

    email_verified = models.BooleanField(default=False)
    mobile_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = MyUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']  # Fields necessary for making a user

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name

    def __unicode__(self):
        return self.email

    def get_user_type(self):
        return self.user_type

    def set_user_inactive(self):
        if self.is_active is True:
            self.is_active = False
            self.save()
            return True
        else:
            return False

    def username(self):
        return self.email

    def promoter_or_client(self):  # for explicit use in templates
        if self.user_type is 'P':
            return True
        elif self.user_type is 'C':
            return False
        else:
            return None
