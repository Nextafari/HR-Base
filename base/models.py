from django.db import models
from django.contrib.auth.models import (
    BaseUserManager,
    AbstractBaseUser,
    PermissionsMixin,
)

from base.utils import gen_staff_access_code


class UserManager(BaseUserManager):
    def create_user(
        self,
        email,
        name,
        password=None,
        **extra_fields,
    ):
        """
        Create and save a User with credentials provided.
        """
        user = self.model(
            email=self.normalize_email(email),
            name=name,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email,
        name,
        password=None,
        **extra_fields,
    ):
        """
        Creates and saves a superuser with the credentials provided.
        """
        user = self.create_user(
            email=self.normalize_email(email),
            name=name,
            password=password,
        )
        user.is_staff = True
        user.is_admin = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class UserRoles(models.TextChoices):
    USER = "user", "USER"
    ORG_ADMIN = "org_admin", "ORG ADMIN"
    ORG_STAFF = "org_staff", "ORG STAFF"
    ORG_HR = "org_hr", "ORG HR"


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    role = models.CharField(
        max_length=150, default=UserRoles.USER, choices=UserRoles.choices
    )
    last_login = models.DateTimeField(verbose_name="last login", auto_now=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    # This overwrites django's default user model's username to a
    # username of choice
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    def __str__(self):
        return f"{self.name}"

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True


class Staff(models.Model):
    user = models.ForeignKey(
        to="User", related_name="user_staff", on_delete=models.CASCADE
    )
    organization = models.ForeignKey(
        to="Organization", related_name="org_staff", on_delete=models.CASCADE
    )
    date_joined = models.DateTimeField(auto_now_add=True)
    exit_date = models.DateTimeField(blank=True, null=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Staff"

    def __str__(self):
        return "Staff: %s" % (self.user.name)


class Organization(models.Model):
    name = models.CharField(max_length=200)
    valuation = models.FloatField(default=0.00)
    location = models.CharField(max_length=300)
    admin = models.ForeignKey(
        to="User", related_name="user_org", on_delete=models.CASCADE
    )
    staff_access_code = models.CharField(max_length=3, default=gen_staff_access_code)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Job(models.Model):
    created_by = models.ForeignKey(
        to="User", related_name="user_job", on_delete=models.CASCADE
    )
    org_id = models.ForeignKey(
        to="Organization", related_name="org_job", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=300)
    description = models.CharField(max_length=500)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    is_open = models.BooleanField(default=True)

    def __str__(self):
        return "Job from: %s" % (self.org_id.name)


class Application(models.Model):
    applicant_id = models.ForeignKey(
        to="User", related_name="user_application", on_delete=models.CASCADE
    )
    job = models.ForeignKey(to="Job", on_delete=models.CASCADE)
    skill_description = models.CharField(max_length=500)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s's application" % (self.applicant_id.name)
