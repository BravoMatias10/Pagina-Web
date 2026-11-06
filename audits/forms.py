from django import forms
from .models import Review


class AuditForm(forms.Form):
    url = forms.URLField(
        label="Dirección del sitio",
        max_length=1000,
        widget=forms.URLInput(attrs={"placeholder": "https://ejemplo.cl"}),
    )
    authorization = forms.BooleanField(
        label="Declaro contar con autorización para revisar este sitio mediante solicitudes públicas y pasivas."
    )


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["status", "evidence"]
        labels = {
            "status": "Resultado manual",
            "evidence": "Evidencia y observaciones (sin datos sensibles)",
        }


class SendForm(forms.Form):
    recipient = forms.EmailField(label="Correo del destinatario")
    confirm = forms.BooleanField(
        label="Confirmo el destinatario y autorizo enviarle este informe."
    )


from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model


class RegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username",)
