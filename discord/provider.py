from allauth.socialaccount.providers.discord import provider


class DiscordAccount(provider.DiscordAccount):

    def get_avatar_url(self):
        user_id = self.account.extra_data.get('id')
        avatar_hash = self.account.extra_data.get('avatar')
        if not avatar_hash:
            return f'https://cdn.discordapp.com/embed/avatars/{int(self.account.extra_data["discriminator"]) % 5}.png'
        ending = 'gif' if avatar_hash.startswith('a_') else 'png'
        return f'https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.{ending}'


class DiscordProvider(provider.DiscordProvider):
    account_class = DiscordAccount

    def extract_common_fields(self, data):
        return dict(
            email=data.get('email'),
            username=data.get('username'),
            first_name=data.get('username'),
            last_name=data.get('discriminator'),
        )


provider_classes = [DiscordProvider]
