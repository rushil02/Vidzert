from django import forms
from models import ClientProfile


class ClientProfileForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'id': 'FullName', 'placeholder': 'Name', 'required': 'true'}))

    def __init__(self, *args, **kwargs):
        someval = kwargs.pop('name')
        super(ClientProfileForm, self).__init__(*args, **kwargs)
        self.fields['name'].initial = someval
        self.fields['contact2'].label = "Contact Number"

    class Meta:
        model = ClientProfile
        exclude = ['client_id']
        widgets = {

            'address': forms.Textarea(attrs={'class': 'form-control fullscreen', 'id': 'Address'}),

            'contact2': forms.TextInput(
                attrs={'class': 'form-control', 'id': 'Contact', 'placeholder': 'Contact Number', 'required': 'true'}),

            'website': forms.TextInput(
                attrs={'class': 'form-control', 'id': 'Website', 'placeholder': 'Website', 'required': 'true'}),

        }

    def clean_address(self):
        return self.cleaned_data['address'] or None

    def clean_contact2(self):
        return self.cleaned_data['contact2'] or None

    def clean_website(self):
        return self.cleaned_data['website'] or None
