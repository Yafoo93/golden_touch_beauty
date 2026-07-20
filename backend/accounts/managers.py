from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(
        self,
        email,
        phone_number,
        full_name,
        password=None,
        **extra_fields,
    ):
        if not email:
            raise ValueError("An email address is required.")

        if not phone_number:
            raise ValueError("A phone number is required.")

        if not full_name:
            raise ValueError("A full name is required.")

        email = self.normalize_email(email)
        phone_number = phone_number.strip()

        user = self.model(
            email=email,
            phone_number=phone_number,
            full_name=full_name.strip(),
            **extra_fields,
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(
        self,
        email,
        phone_number,
        full_name,
        password=None,
        **extra_fields,
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("A superuser must have is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("A superuser must have is_superuser=True.")

        return self.create_user(
            email=email,
            phone_number=phone_number,
            full_name=full_name,
            password=password,
            **extra_fields,
        )