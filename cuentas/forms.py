from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm


User = get_user_model()


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
