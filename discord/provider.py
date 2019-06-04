from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider


class DiscordAccount(ProviderAccount):
    def to_str(self):
        default = super(DiscordAccount, self).to_str()
        return self.account.extra_data.get('username', default)


class DiscordProvider(OAuth2Provider):
    id = 'discord'
    name = 'Discord'
    account_class = DiscordAccount

    def extract_uid(self, data):
        return str(data['id'])

    def extract_common_fields(self, data):
        return dict(
            email=data.get('email'),
            username=data.get('username'),
            first_name=data.get('username'),
            last_name=data.get('discriminator'),
        )

    def get_default_scope(self):
        return ['email', 'identify']


provider_classes = [DiscordProvider]
