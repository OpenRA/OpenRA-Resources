from django import forms


class AddScreenshotForm(forms.Form):
	scfile      = forms.FileField()