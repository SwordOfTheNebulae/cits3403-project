from django import forms

from .models import *


class Login(forms.Form):
    username = forms.CharField(
        label="nickname",
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control required", 'placeholder': 'nickname'}),

    )
    password = forms.CharField(
        label="password",
        widget=forms.PasswordInput(attrs={"class": "form-control required", 'placeholder': 'password'}),
    )


class Edit(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email", "password"]
        labels = {
            "password": "password",
            "name": "nickname",
            "email": "email",
        }
        widgets = {
            "password": forms.PasswordInput(attrs={"class": "form-control"}),
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

        def clean_name(self):
            name = self.cleaned_data.get("name")
            result = User.objects.filter(name=name)
            if result:
                raise forms.ValidationError("Name already exists")
            return name


class RegisterForm(forms.Form):
    username = forms.CharField(
        label="nickname(cannot be repeated)",
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control", 'placeholder': 'nickname(cannot be repeated)'}),
    )
    email = forms.EmailField(
        label="email", widget=forms.EmailInput(attrs={"class": "form-control", 'placeholder': 'email'})
    )
    password1 = forms.CharField(
        label="password",
        max_length=128,
        widget=forms.PasswordInput(attrs={"class": "form-control", 'placeholder': 'password'}),
    )
    password2 = forms.CharField(
        label="confirm password",
        widget=forms.PasswordInput(attrs={"class": "form-control", 'placeholder': 'confirm password'}),
    )

    def clean_username(self):
        username = self.cleaned_data.get("username")

        if len(username) < 6:
            raise forms.ValidationError(
                "Your username must be at least 6 characters long."
            )
        elif len(username) > 50:
            raise forms.ValidationError("Your username is too long.")
        else:
            filter_result = User.objects.filter(username=username)
            if len(filter_result) > 0:
                raise forms.ValidationError("Your username already exists.")
        return username

    def clean_name(self):
        name = self.cleaned_data.get("name")
        filter_result = User.objects.filter(name=name)
        if len(filter_result) > 0:
            raise forms.ValidationError("Your name already exists.")
        return name

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        if len(password1) < 6:
            raise forms.ValidationError("Your password is too short.")
        elif len(password1) > 20:
            raise forms.ValidationError("Your password is too long.")
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Password mismatch. Please enter again.")
        return password2
