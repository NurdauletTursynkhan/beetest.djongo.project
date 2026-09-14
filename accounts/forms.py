from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from .models import User

class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, label="Имя")
    last_name = forms.CharField(max_length=150, label="Фамилия")
    email = forms.EmailField(label="Почта")

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с такой почтой уже существует.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"].lower().strip()
        user.email = self.cleaned_data["email"].lower().strip()
        if commit:
            user.save()
        return user

class LoginForm(forms.Form):
    email = forms.EmailField(label="Почта")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email", "").lower().strip()
        password = cleaned.get("password")
        if email and password:
            try:
                username = User.objects.get(email=email).username
            except User.DoesNotExist:
                username = None
            self.user = authenticate(username=username, password=password) if username else None
            if self.user is None:
                raise forms.ValidationError("Неверная почта или пароль.")
        return cleaned

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        labels = {
            "first_name": "Имя",
            "last_name": "Фамилия",
            "email": "Почта",
        }

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        qs = User.objects.filter(email=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Эта почта уже используется.")
        return email

class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(label="Старый пароль", widget=forms.PasswordInput)
    new_password1 = forms.CharField(label="Новый пароль", widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="Повторите новый пароль", widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_old_password(self):
        value = self.cleaned_data["old_password"]
        if not self.user.check_password(value):
            raise forms.ValidationError("Старый пароль указан неправильно.")
        return value

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password1")
        p2 = cleaned.get("new_password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Новые пароли не совпадают.")
        return cleaned
