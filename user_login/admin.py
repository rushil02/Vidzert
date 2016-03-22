from django.contrib import admin
from django import forms
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.conf import settings
from . import forms
from django.contrib.auth import get_user_model


class MyUserAdmin(UserAdmin):
    # The forms to add and change user instances
    form = forms.UserChangeForm
    add_form = forms.UserCreationForm

    readonly_fields = ('is_superuser',)
    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('email', 'name', 'mobile', 'user_type', 'is_superuser', 'is_staff', 'is_active')
    list_filter = ('is_superuser', 'is_active', 'user_type')
    fieldsets = (
        ('Personal info', {'fields': ('name', 'mobile')}),
        ('Permissions', {'fields': ('user_type',)}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide', 'extrapretty'),
            'fields': ('email', 'name', 'mobile', 'password1', 'password2', 'user_type')}
        ),
    )
    search_fields = ('email', 'name', 'mobile')
    ordering = ('email',)
    date_hierarchy = 'last_login'
    filter_horizontal = ()


admin.site.register(get_user_model(), MyUserAdmin)
