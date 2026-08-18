from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model.

    This model is shared across the application.
    """

    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
    )

    is_verified = models.BooleanField(
        default=False,
    )

    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
    )

    last_login_ip = models.GenericIPAddressField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "accounts_user"

    def __str__(self):
        return self.username


class SchoolStudent(models.Model):
    """
    Student information for the School Management System.
    """

    student_id = models.CharField(
        max_length=50,
        unique=True,
    )

    name = models.CharField(
        max_length=150,
    )

    student_class = models.CharField(
        max_length=50,
    )

    joining_date = models.DateField()

    email = models.EmailField(
        blank=True,
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
    )

    father_name = models.CharField(
        max_length=150,
        blank=True,
    )

    mother_name = models.CharField(
        max_length=150,
        blank=True,
    )

    address = models.TextField(
        blank=True,
    )

    date_of_birth = models.DateField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "School Student"
        verbose_name_plural = "School Students"

    def __str__(self):
        return f"{self.name} ({self.student_id})"


class SchoolTeacher(models.Model):
    """
    Teacher information for the School Management System.
    """

    teacher_id = models.CharField(
        max_length=50,
        unique=True,
    )

    name = models.CharField(
        max_length=150,
    )

    email = models.EmailField()

    department = models.CharField(
        max_length=100,
    )

    subject = models.CharField(
        max_length=100,
    )

    joining_date = models.DateField()

    phone = models.CharField(
        max_length=20,
        blank=True,
    )

    qualification = models.CharField(
        max_length=150,
        blank=True,
    )

    address = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "School Teacher"
        verbose_name_plural = "School Teachers"

    def __str__(self):
        return f"{self.name} ({self.teacher_id})"
