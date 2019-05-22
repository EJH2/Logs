import requests

from allauth.socialaccount.providers.discord.views import DiscordOAuth2Adapter as DiscordAdapter
from allauth.socialaccount.providers.oauth2.views import OAuth2CallbackView, OAuth2LoginView


class CustomDiscordOAuth2Adapter(DiscordAdapter):
    guilds_url = 'https://discordapp.com/api/users/@me/guilds'

    def complete_login(self, request, app, token, **kwargs):
        headers = {
            'Authorization': 'Bearer {0}'.format(token.token),
            'Content-Type': 'application/json',
        }
        extra_data = requests.get(self.profile_url, headers=headers).json()
        guild_data = requests.get(self.guilds_url, headers=headers).json()

        extra_data['guilds'] = guild_data

        return self.get_provider().sociallogin_from_response(
            request,
            extra_data
        )


oauth2_login = OAuth2LoginView.adapter_view(CustomDiscordOAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(CustomDiscordOAuth2Adapter)
