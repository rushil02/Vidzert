__author__ = 'Pranav'

from django import forms
from models import Ticket, Message


class TicketAuthenticatedUserForm(forms.ModelForm):

    class Meta:
        model = Ticket
        fields = ['title', 'ticket_type']

    def clean(self):
        return self.cleaned_data or None


class MessageForm(forms.ModelForm):

    class Meta:
        model = Message
        fields = ['message_text', 'message_image']

    def clean(self):
        if (self.cleaned_data['message_text'] == '' or self.cleaned_data['message_text'] is None) and (self.cleaned_data['message_image'] == '' or self.cleaned_data['message_image'] is None):
            raise forms.ValidationError('No text and image')
        else:
            return self.cleaned_data or None


class TicketAnonymousUserForm(forms.ModelForm):

    class Meta:
        model = Ticket
        fields = ['title', 'ticket_type', 'submitter_email']

    def clean(self):
        return self.cleaned_data or None


class TicketStatusForm(forms.Form):
    ticket_ref_no = forms.CharField(max_length=15)

    def clean(self):
        ref_no = self.cleaned_data['ticket_ref_no']
        if "TIC" not in ref_no:
            raise forms.ValidationError("Invalid Reference Number")
        ticket = Ticket.objects.filter(ref_no=ref_no).count()
        if ticket == 0:
            raise forms.ValidationError("Invalid Reference Number")
        return self.cleaned_data or None


class TicketAdminForm(forms.ModelForm):

    class Meta:
        model = Ticket
        fields = ['status']
