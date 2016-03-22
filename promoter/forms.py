__author__ = 'Rushil'

from django import forms
from django.utils.translation import ugettext, ugettext_lazy as _
from models import PromoterProfile


class ProfileForm(forms.ModelForm):

    class Meta:
        model = PromoterProfile
        exclude = ['promoter_id', 'promoter_category_profile']
        widgets = {

            'last_name': forms.TextInput(
                attrs={'class': 'form-control', 'id': 'last_name', 'placeholder': 'Name', 'required': 'true'}),

            'dob': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control', 'id': 'dob', 'placeholder': 'Date of Birth', 'required': 'true'}),

            'gender': forms.Select(
                attrs={'class': 'form-control', 'id': 'gender', 'required': 'true'}, choices=PromoterProfile.GENDER),

            'area_city': forms.TextInput(
                attrs={'class': 'form-control', 'id': 'area_city', 'placeholder': 'City', 'required': 'true'}),

            'area_state': forms.Select(
                attrs={'class': 'form-control', 'id': 'area_state', 'placeholder': 'State', 'required': 'true'}),

            'PAN': forms.TextInput(
                attrs={'class': 'form-control', 'id': 'PAN', 'placeholder': 'PAN', 'required': 'true'}),

        }

    def clean_PAN(self):
        PAN = self.cleaned_data['PAN']
        if PAN == "":
            return None
        elif not len(PAN) == 10:
            raise forms.ValidationError("PAN should be 10 digits")
        return PAN or None
