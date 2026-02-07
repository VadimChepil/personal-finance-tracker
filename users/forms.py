from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError

from .models import User


class SignUpForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Введіть ваш email"}),
        error_messages={
            "required": "Будь ласка, введіть email",
            "invalid": "Введіть коректний email",
        },
    )

    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Введіть пароль"}),
        error_messages={
            "required": "Будь ласка, введіть пароль",
        },
    )

    password2 = forms.CharField(
        label="Підтвердження пароля",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Повторіть пароль"}),
        error_messages={
            "required": "Будь ласка, підтвердіть пароль",
        },
    )

    class Meta:
        model = User
        fields = ("email",)

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError("Користувач з таким email вже існує")
        return email

    def clean_password1(self):
        password = self.cleaned_data.get("password1")

        if not password:
            raise ValidationError("Будь ласка, введіть пароль")

        if len(password) < 8:
            raise ValidationError("Пароль має бути не менше 8 символів.")

        if password.isdigit() or password.isalpha():
            raise ValidationError("Пароль має містити літери та цифри.")

        return password

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if not password2:
            raise ValidationError("Будь ласка, підтвердіть пароль")

        if password1 and password2 and password1 != password2:
            raise ValidationError("Паролі не співпадають")

        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data["password1"]
        user.set_password(password)

        if commit:
            user.save()
        return user


class SignInForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Введіть ваш email"}),
        error_messages={
            "required": "Будь ласка, введіть email",
            "invalid": "Введіть коректний email",
        },
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Введіть пароль"}),
        error_messages={
            "required": "Будь ласка, введіть пароль",
        },
    )

    error_messages = {
        "invalid_login": "Будь ласка, введіть правильні email та пароль.",
        "inactive": "Цей обліковий запис неактивний.",
    }
