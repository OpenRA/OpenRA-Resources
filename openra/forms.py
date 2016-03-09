from django import forms

class AuthenticationForm(forms.Form):
	username    = forms.CharField(max_length=20)
	password    = forms.CharField(max_length=32, widget=forms.PasswordInput)

class AddScreenshotForm(forms.Form):
	scfile      = forms.FileField()