from django import forms

class UploadMapForm(forms.Form):
    info        = forms.CharField(max_length=400, required=False)
    file        = forms.FileField()
    if_cc       = (('cc_yes', 'Yes',), ('cc_no', 'No',))
    policy_cc	= forms.ChoiceField(widget=forms.RadioSelect, choices=if_cc)
    if_com      = (('com_yes', 'Yes',), ('com_no', 'No',))
    commercial	= forms.ChoiceField(widget=forms.RadioSelect, choices=if_com)
    if_adapt    = (('adapt_yes', 'Yes',), ('adapt_no', 'No'), ('adapt_alike', 'Yes, as long as others share alike',))
    adaptations = forms.ChoiceField(widget=forms.RadioSelect, choices=if_adapt)

class AuthenticationForm(forms.Form):
    username    = forms.CharField(max_length=20)
    password    = forms.CharField(max_length=32, widget=forms.PasswordInput)
