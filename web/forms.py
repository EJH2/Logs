import requests
from allauth.socialaccount.models import SocialAccount
from django import forms
from django.core.exceptions import ValidationError

from api.consts import form_types, form_expiry_times, form_privacy_types, expiry_times


def validate_url(value):
    """Check if url content type is text/plain"""
    if 'text/plain' not in requests.head(value).headers['content-type']:
        raise ValidationError('URL Content-Type must be text/plain!')
    return value


class LogCreateForm(forms.Form):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.auto_id = '%s'
        choices = self.fields['expires'].choices[:5]
        if not user or not user.is_authenticated:
            self.fields['expires'].choices = choices
            return
        if user.has_perm('api.extended_expiry'):
            choices = self.fields['expires'].choices[:6]
        if user.has_perm('api.no_expiry'):
            choices = self.fields['expires'].choices
        self.fields['expires'].choices = choices

        social_user = SocialAccount.objects.filter(user=user).first()
        if social_user and social_user.extra_data.get('guilds'):
            self.fields['guild'].choices = [
                ('', ' -- select a guild -- '), *[(g['id'], g['name']) for g in social_user.extra_data['guilds']]
            ]

    type = forms.ChoiceField(
        choices=[
            ('', ' -- select an option -- '),
            *((k, form_types[k]) for k in form_types)
        ]
    )
    url = forms.URLField(
        validators=[validate_url],
        required=False,
        widget=forms.URLInput(
            attrs={
                'onchange': 'clear_file()',
                'placeholder': 'Type URL'
            }
        )
    )
    file = forms.FileField(
        required=False,
        widget=forms.FileInput(
            attrs={
                'onchange': 'clear_url()'
            }
        )
    )
    privacy = forms.ChoiceField(
        initial='public',
        choices=form_privacy_types,
        widget=forms.RadioSelect
    )
    guild = forms.ChoiceField(
        choices=[],
        required=False
    )
    expires = forms.ChoiceField(
        choices=form_expiry_times,
    )

    def clean(self):
        cleaned_data = self.cleaned_data
        if not cleaned_data.get('url') and not cleaned_data.get('file'):
            self.add_error('url', 'You must specify either a URL or file to parse!')
        if cleaned_data.get('expires'):
            cleaned_data['expires'] = expiry_times[cleaned_data['expires']]
        if cleaned_data['privacy'] not in ['public', 'invite'] and not cleaned_data.get('guild'):
            self.add_error('guild', 'You must specify a guild to link to!')
        else:
            cleaned_data['guild'] = None
        return cleaned_data
