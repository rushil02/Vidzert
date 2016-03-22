from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from captcha.fields import CaptchaField
import re
from django.utils.translation import ugettext_lazy as _
from logs.models import BlackList, GrayList
from django.core.exceptions import ObjectDoesNotExist
from admin_custom.custom_errors import EmailValidationError


class UserCreationForm(forms.ModelForm):
    """
    A form that creates a user, with no privileges, from the given details.
    """
    error_messages = {
        'duplicate_email': _("A user with that email already exists"),
        'password_mismatch': _("The two password fields didn't match."),
    }
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'Password',
                                                                  'placeholder': 'Password', 'required': 'required'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'ConfirmPassword',
                                                                  'placeholder': 'Confirm Password',
                                                                  'required': 'required'}))

    class Meta:
        model = get_user_model()
        fields = ('email', 'name', 'mobile')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'id': 'FullName',
                                           'placeholder': 'First Name', 'required': 'required'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'id': 'Email',
                                             'placeholder': 'Email', 'required': 'required'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control', 'id': 'Mobile', 'placeholder': 'Mobile'}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"]
        try:
            get_user_model().objects.get(email=email)
        except get_user_model().DoesNotExist:
            email = get_email_gmail(email)
            return email
        raise forms.ValidationError(
            self.error_messages['duplicate_email'],
            code='duplicate_email'
        )

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        if len(password) < 8:
            raise forms.ValidationError(
                _('Password is too short. It should be of Minimum 8 Characters'),
                code='short_password',
            )

        if any(ch in password for ch in ' '):
            raise forms.ValidationError(
                _('Password cannot contain spaces'),
                code='password_has_spaces',
            )
        return password

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    def clean_mobile(self):
        if not self.cleaned_data['mobile']:
            return None
        else:
            return self.cleaned_data['mobile']

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(label=_("Password"))

    class Meta:
        model = get_user_model()
        fields = ('name', 'password', 'mobile', 'user_type', 'is_staff', 'is_active')

    def clean_password(self):
        return self.initial["password"]


class LoginForm(forms.Form):
    user_cache = None

    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control',
                                                                           'placeholder': 'Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password',
                                                                 'id': 'exampleInputPassword1'}), required=True)

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        if email and password:
            self.user_cache = authenticate(email=email, password=password)
            if not self.user_cache:
                raise forms.ValidationError("Sorry, that login was invalid. Please try again.")
            else:
                if not self.is_active():
                    raise forms.ValidationError("You have been blocked from the website due to malicious activity.")
                else:
                    return self.cleaned_data
        else:
            raise forms.ValidationError("Enter Email and Password")

    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            email = get_email_gmail(email)
        except EmailValidationError:
            raise forms.ValidationError(_("Enter valid email address"))
        else:
            return email

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache

    def is_active(self):
        if self.user_cache:
            if not self.user_cache.is_active:
                try:
                    BlackList.objects.get(user_id=self.user_cache)
                    GrayList.objects.get(user_id=self.user_cache)
                except ObjectDoesNotExist:
                    self.user_cache.is_active = True
                    self.user_cache.save()
                    return True
                else:
                    return False
            else:
                return True
        else:
            return False


class LoginFormCaptcha(LoginForm):
    captcha = CaptchaField()


class UserCreationFormCaptcha(UserCreationForm):
    captcha = CaptchaField()


class PasswordRecoveryForm(forms.Form):
    email = forms.EmailField(required=True)

    captcha = CaptchaField()

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            email = get_email_gmail(email)
        except EmailValidationError:
            raise forms.ValidationError(_("Enter valid email address"))
        else:
            try:
                user = get_user_model().objects.get(email=email)
            except get_user_model().DoesNotExist:
                return None
            else:
                return user


class PasswordResetForm(forms.Form):
    password1 = forms.CharField(
        label=_('New password'),
        widget=forms.PasswordInput,
    )
    password2 = forms.CharField(
        label=_('New password (confirm)'),
        widget=forms.PasswordInput,
    )

    captcha = CaptchaField()

    error_messages = {
        'password_mismatch': _("The two passwords didn't match."),
    }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(PasswordResetForm, self).__init__(*args, **kwargs)

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1', '')
        password2 = self.cleaned_data['password2']
        if not password1 == password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch')
        return password2

    def save(self, commit=True):
        self.user.set_password(self.cleaned_data['password1'])
        if commit:
            get_user_model().objects.filter(pk=self.user.pk).update(
                password=self.user.password,
            )
        return self.user


class MobileVerify(forms.Form):
    OTP = forms.CharField(required=True)
    captcha = CaptchaField()

    def __init__(self, *args, **kwargs):
        self.gen_code = kwargs.pop('gen_code')
        super(MobileVerify, self).__init__(*args, **kwargs)

    def clean_OTP(self):
        OTP = self.cleaned_data['OTP']
        if OTP == self.gen_code:
            return OTP
        else:
            raise forms.ValidationError(_("Invalid code"), code="Invalid OTP")


def get_email_gmail(email):
    regexStr = r'^([^@]+)@[^@]+$'
    domain = re.search("@[\w]+", email).group()
    complete_domain = re.search("@[\w.]+", email).group()
    matchobj = re.search(regexStr, email)
    if matchobj is not None:
        if domain == '@gmail':
            username = matchobj.group(1).replace(".", "")
            new_email = username + complete_domain
            return new_email
        else:
            return email
    else:
        raise EmailValidationError
