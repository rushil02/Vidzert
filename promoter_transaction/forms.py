from django import forms
from django.utils.translation import ugettext_lazy as _


class RechargeForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.promoter = kwargs.pop('promoter', None)
        subscriber_type = kwargs.pop('subscriber_type', None)
        self.upper_coin_limit = 500000
        self.lower_coin_limit = 1000
        super(RechargeForm, self).__init__(*args, **kwargs)

        if subscriber_type == 'PR':
            OPERATOR_CHOICES = (
                ('AT', 'AIRTEL'),
                ('BS', 'BSNL'),
                ('BSS', 'BSNL SPECIAL'),
                ('IDX', 'IDEA'),
                ('VF', 'VODAFONE'),
                ('RL', 'RELIANCE CDMA'),
                ('RG', 'RELIANCE GSM'),
                ('UN', 'UNINOR'),
                ('UNS', 'UNINOR SPECIAL'),
                ('MS', 'MTS'),
                ('AL', 'AIRCEL'),
                ('TD', 'TATA DOCOMO GSM'),
                ('TDS', 'TATA DOCOMO GSM SPECIAL'),
                ('TI', 'TATA INDICOM (CDMA)'),
                ('MTD', 'MTNL DELHI'),
                ('MTDS', 'MTNL DELHI SPECIAL'),
                ('MTM', 'MTNL MUMBAI'),
                ('MTMS', 'MTNL MUMBAI SPECIAL'),
                ('VD', 'VIDEOCON'),
                ('VDS', 'VIDEOCON SPECIAL'),
                ('VG', 'VIRGIN GSM'),
                ('VGS', 'VIRGIN GSM SPECIAL'),
                ('VC', 'VIRGIN CDMA'),
                ('T24', 'T24'),
                ('T24S', 'T24 SPECIAL'),
                ('TW', 'TATA WALKY'),
            )
            self.fields['operator'] = forms.ChoiceField(choices=OPERATOR_CHOICES, widget=forms.Select(), required=True)
        elif subscriber_type == 'PO':
            OPERATOR_CHOICES = (
                ('APOS', 'AIRTEL'),
                ('BPOS', 'BSNL'),
                ('IPOS', 'IDEA'),
                ('VPOS', 'VODAFONE'),
                ('RCPOS', 'RELIANCE CDMA'),
                ('RGPOS', 'RELIANCE GSM'),
                ('CPOS', 'AIRCEL'),
                ('DGPOS', 'TATA DOCOMO GSM'),
                ('DCPOS', 'TATA INDICOM (CDMA)'),
                )
            self.fields['operator'] = forms.ChoiceField(choices=OPERATOR_CHOICES, widget=forms.Select(), required=True)

    mobile_no = forms.RegexField(regex=r'^\+?1?\d{9,10}$', required=True,
                                 error_message=("Phone number must be entered in the format: '+999999999'. Up to 10 digits allowed."))
    coins = forms.IntegerField(required=True, min_value=1000, max_value=500000)

    def clean_coins(self):
        coins = self.cleaned_data['coins']
        if int(coins) < self.lower_coin_limit or int(coins) > self.upper_coin_limit:
            raise forms.ValidationError(_("You can recharge between 10rs to 5000rs"))
        promoter_coins = self.promoter.promoteraccount.current_coins
        if int(coins) < promoter_coins:
            raise forms.ValidationError(_("Dont have enough coins"))
        return self.clean_data['coins']


class PayTMForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.promoter = kwargs.pop('promoter', None)
        self.upper_coin_limit = 500000
        self.lower_coin_limit = 1000
        super(PayTMForm, self).__init__(*args, **kwargs)

    mobile_no = forms.RegexField(regex=r'^\+?1?\d{9,10}$', required=True,
                                 error_message=("Phone number must be entered in the format: '+999999999'. Up to 10 digits allowed."))
    coins = forms.IntegerField(required=True, min_value=1000, max_value=500000)

    def clean_coins(self):
        coins = self.cleaned_data['coins']
        if int(coins) < self.lower_coin_limit or int(coins) > self.upper_coin_limit:
            raise forms.ValidationError(_("You can recharge between 10rs to 5000rs"))
        promoter_coins = self.promoter.promoteraccount.current_coins
        if int(coins) < promoter_coins:
            raise forms.ValidationError(_("Dont have enough coins"))
        return self.clean_data['coins']