from django import forms

class UploadMapForm(forms.Form):
    info        = forms.CharField(max_length=400, required=False)
    file        = forms.FileField()

class AuthenticationForm(forms.Form):
    username    = forms.CharField(max_length=20)
    password    = forms.CharField(max_length=32, widget=forms.PasswordInput)
