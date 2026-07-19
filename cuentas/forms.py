from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import (
    password_validators_help_text_html,
    validate_password,
)
from django.core.exceptions import ValidationError


User = get_user_model()


class DirectPasswordChangeForm(forms.Form):
    username = forms.CharField(
        label="Usuario",
        max_length=150,
        widget=forms.TextInput(attrs={"autocomplete": "username"}),
    )
    current_password = forms.CharField(
        label="Contraseña actual",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
    new_password1 = forms.CharField(
        label="Nueva contraseña",
        strip=False,
        help_text=password_validators_help_text_html(),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    new_password2 = forms.CharField(
        label="Confirma la nueva contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def __init__(self, *args, request=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.authenticated_user = user if getattr(user, "is_authenticated", False) else None
        self.user = None
        if self.authenticated_user is not None:
            self.fields["username"].required = False
            self.fields["username"].initial = self.authenticated_user.get_username()
            self.fields["username"].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username", "").strip()
        current_password = cleaned_data.get("current_password")
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")

        if not current_password:
            return cleaned_data

        expected_user = self.authenticated_user
        username_to_validate = expected_user.get_username() if expected_user is not None else username
        user = authenticate(
            self.request,
            username=username_to_validate,
            password=current_password,
        )
        credentials_are_valid = user is not None and (
            expected_user is None or user.pk == expected_user.pk
        )

        if not credentials_are_valid:
            raise forms.ValidationError(
                "No pudimos validar el usuario y la contraseña actual. Revisa los datos e intenta de nuevo."
            )

        self.user = user
        if new_password1 and new_password2 and new_password1 != new_password2:
            self.add_error("new_password2", "Las contraseñas nuevas no coinciden.")
        if new_password1 and new_password1 == current_password:
            self.add_error("new_password1", "La nueva contraseña debe ser diferente a la actual.")
        if new_password1:
            try:
                validate_password(new_password1, user)
            except ValidationError as error:
                self.add_error("new_password1", error)
        return cleaned_data

    def save(self):
        self.user.set_password(self.cleaned_data["new_password1"])
        self.user.save(update_fields=["password"])
        return self.user


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(label="Nombre", max_length=150)
    email = forms.EmailField(label="Correo electrónico")
    company = forms.CharField(required=False, widget=forms.HiddenInput, label="Empresa")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "email", "username", "company")
        labels = {"username": "Usuario"}

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo.")
        return email

    def clean_company(self):
        value = self.cleaned_data.get("company", "").strip()
        if value:
            raise forms.ValidationError("No pudimos validar el formulario.")
        return value


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        labels = {
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "Correo electrónico",
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        exists = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists()
        if exists:
            raise forms.ValidationError("Este correo ya está asociado a otra cuenta.")
        return email
