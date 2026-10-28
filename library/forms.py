from datetime import timedelta
from django import forms
from django.utils import timezone
from .models import BookCopy, Loan, Reader, Reservation

class ReaderForm(forms.ModelForm):
    class Meta:
        model = Reader
        fields = ["full_name", "email", "phone", "ticket_number", "active"]
        widgets = {k: forms.TextInput(attrs={"class": "form-control"}) for k in ["full_name", "email", "phone", "ticket_number"]}

class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ["copy", "reader", "due_at"]
        widgets = {"copy": forms.Select(attrs={"class": "form-select"}), "reader": forms.Select(attrs={"class": "form-select"}), "due_at": forms.DateInput(attrs={"class": "form-control", "type": "date"})}
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["copy"].queryset = BookCopy.objects.filter(status=BookCopy.Status.AVAILABLE).select_related("book")
        self.fields["reader"].queryset = Reader.objects.filter(active=True)
        if not self.is_bound:
            self.initial["due_at"] = timezone.localdate() + timedelta(days=14)

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["book", "reader"]
        widgets = {"book": forms.Select(attrs={"class": "form-select"}), "reader": forms.Select(attrs={"class": "form-select"})}

from django.contrib.auth.models import User

class SignUpForm(forms.Form):
    full_name = forms.CharField(label="ФИО", max_length=200, widget=forms.TextInput(attrs={"class":"form-control", "placeholder":"Иванов Иван Иванович"}))
    username = forms.CharField(label="Логин", max_length=150, widget=forms.TextInput(attrs={"class":"form-control"}))
    email = forms.EmailField(label="E-mail", required=False, widget=forms.EmailInput(attrs={"class":"form-control"}))
    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput(attrs={"class":"form-control"}))
    password2 = forms.CharField(label="Повторите пароль", widget=forms.PasswordInput(attrs={"class":"form-control"}))

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Пользователь с таким логином уже существует.")
        return username

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") and cleaned.get("password1") != cleaned.get("password2"):
            self.add_error("password2", "Пароли не совпадают.")
        return cleaned
