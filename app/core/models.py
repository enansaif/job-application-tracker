from uuid import uuid4
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.models import (
    BaseUserManager,
    AbstractBaseUser,
    PermissionsMixin,
)

APPLICATION_STATUS_CHOICES = [
    ('applied', 'Applied'),
    ('interviewing', 'Interviewing'),
    ('rejected', 'Rejected'),
    ('offer', 'Offer'),
    ('accepted', 'Accepted'),
]


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **kwargs):
        if not email:
            raise ValueError("Users must have an email address")
        try:
            validate_email(email)
        except ValidationError:
            raise ValueError('Email address is not valid')
        user = self.model(
            email=self.normalize_email(email=email),
            **kwargs
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **kwargs):
        user = self.create_user(email=email, password=password, **kwargs)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    public_id = models.UUIDField(default=uuid4, unique=True, editable=False)
    email = models.EmailField(max_length=255, unique=True, validators=[validate_email])
    name = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    objects = UserManager()
    USERNAME_FIELD = "email"

    def __str__(self):
        return self.email


class Country(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    class Meta:
        constraints = [
        models.UniqueConstraint(fields=['user', 'name'], name='unique_user_country')
    ]

    def __str__(self):
        return self.name


class Tag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    class Meta:
        constraints = [
        models.UniqueConstraint(fields=['user', 'name'], name='unique_user_tag')
    ]

    def __str__(self):
        return self.name


class Company(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    country = models.ForeignKey(Country, null=True, blank=True, on_delete=models.SET_NULL)
    link = models.URLField(null=True, blank=True)
    tags = models.ManyToManyField(Tag)
    class Meta:
        constraints = [
        models.UniqueConstraint(fields=['user', 'name'], name='unique_user_company')
    ]

    def __str__(self):
        return self.name


class Resume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='resumes/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField(Tag)

    def __str__(self):
        return f"Resume created @ {str(self.created_at)}"


class Application(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    country = models.ForeignKey(Country, null=True, blank=True, on_delete=models.SET_NULL)
    tags = models.ManyToManyField(Tag)
    resume = models.ForeignKey(Resume, null=True, blank=True, on_delete=models.SET_NULL)
    position = models.CharField(max_length=255)
    link = models.URLField(null=True, blank=True)
    note = models.TextField()
    status = models.CharField(max_length=32, choices=APPLICATION_STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.position} @ {self.company.name}"


class Interview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag)
    date = models.DateField()
    note = models.TextField()

    def __str__(self):
        return f"{self.application.company.name} on {str(self.date)}"

