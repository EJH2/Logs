import pendulum

from natural.date import duration

embed_grid_values = [['1 / 13'], ['1 / 7', '7 / 13'], ['1 / 5', '5 / 9', '9 / 13']]


class LiteLogRenderer:
    def __init__(self, data):
        self.uuid = data['uuid']
        self.page = data.get('page')
        self._messages = self.page.object_list if self.page else data['messages']
        self.messages = [Message(**m) for m in self._messages]

    @property
    def message_groups(self):
        groups = []

        if not self.messages:
            return groups

        curr = MessageGroup(self.messages[0].author)

        for index, message in enumerate(self.messages):
            next_index = index + 1 if index + 1 < len(self.messages) else index
            next_message = self.messages[next_index]

            curr.messages.append(message)

            if message.is_different_from(next_message):
                groups.append(curr)
                curr = MessageGroup(next_message.author)

        groups.append(curr)
        return groups


class LogRenderer(LiteLogRenderer):
    def __init__(self, data):
        super().__init__(data)
        self.created = data.get('created')
        self.total_messages = data['total_messages']
        self.users = data['users']
        self.user_id = data['user_id']
        self.raw_content = data['raw_content']
        self.raw_type = data['raw_type']
        self.type = data['type']
        self.chunked = data.get('chunked')
        self.is_preview = data.get('is_preview')
        self.delete_token = data.get('delete_token')

    @property
    def human_created(self):
        return duration(self.created, now=pendulum.now()) if self.created else None

    @property
    def export_created(self):
        return self.created.strftime('%Y-%m-%d %H:%M:%S')


class MessageGroup:
    def __init__(self, author):
        self.author = author
        self.messages = []

    @property
    def timestamp(self):
        return self.messages[0].timestamp

    @property
    def human_timestamp(self):
        return self.messages[0].human_timestamp


class User:
    def __init__(self, data):
        self.id = data.get('id')
        self.username = data.get('username')
        self.discriminator = data.get('discriminator')
        self.avatar_url = data.get('avatar')
        self.bot = data.get('bot')
        self.color = data.get('color')

    @property
    def default_avatar_url(self):
        return "https://cdn.discordapp.com/embed/avatars/{}.png".format(
            (int(self.id) >> 22) % 5
        )

    def __str__(self):
        return f'{self.username}#{self.discriminator}'

    def __eq__(self, other):
        return other.__dict__ == self.__dict__


class Embed:
    def __init__(self, data):
        self.title = data.get('title')
        self.description = data.get('description')
        self.url = data.get('url')
        self.type = data.get('type', 'rich')
        self.author = data.get('author')
        self.provider = data.get('provider')
        self.timestamp_ = pendulum.parse(data['timestamp']) if data.get('timestamp') else None
        self.color = data.get('color')
        self.image = data.get('image')
        self.thumbnail = data.get('thumbnail')
        self.video = data.get('video')
        self.fields = data.get('fields')
        self.footer = data.get('footer')

        if self.fields:
            rows = []
            row = []
            for index, field in enumerate(self.fields):
                if not index:
                    row.append(field)
                    continue
                if not field['inline']:
                    if row:
                        rows.append(row)
                    row = [field]
                    rows.append(row)
                    row = []
                else:
                    if len(row) == 3:
                        rows.append(row)
                        row = []
                    row.append(field)
            if row:
                rows.append(row)

            for row in rows:
                grid = embed_grid_values[len(row) - 1]
                for index, value in enumerate(grid):
                    row[index]['grid_column'] = value

            for index, value in enumerate([field_ for row_ in rows for field_ in row_]):
                self.fields[index].update(value)

    @property
    def timestamp(self):
        return self.timestamp_.isoformat() if self.timestamp_ else None

    @property
    def human_timestamp(self):
        return duration(self.timestamp_, now=pendulum.now()) if self.timestamp_ else None


class Message:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.channel_id = kwargs.get('channel_id')
        self.guild_id = kwargs.get('guild_id')
        self.author = User(kwargs.get('author'))
        self.timestamp_ = pendulum.parse(kwargs['timestamp']) if kwargs.get('timestamp') else None
        self.edited_timestamp_ = pendulum.parse(kwargs['edited_timestamp']) if kwargs.get('edited_timestamp') else None
        self.raw_content = kwargs.get('_content')
        self.content = kwargs.get('content')
        self.attachments = kwargs.get('attachments')
        self.embeds = [Embed(e) for e in kwargs.get('embeds')]

        self.error = False
        if not any([self.raw_content, self.attachments, self.embeds]):  # No content, attachments or embeds
            self.error = True
            self.content = '[No Message Content]'

    @property
    def timestamp(self):
        return self.timestamp_.isoformat() if self.timestamp_ else None

    @property
    def edited_timestamp(self):
        return self.edited_timestamp_.isoformat() if self.edited_timestamp_ else None

    @property
    def human_timestamp(self):
        return duration(self.timestamp_, now=pendulum.now()) if self.timestamp_ else None

    def is_different_from(self, other):
        if self.timestamp_ is not None:
            return (
                    (other.timestamp_ - self.timestamp_).total_seconds() > 420
                    or other.timestamp_.day != self.timestamp_.day
                    or other.author != self.author
            )
        return other.author != self.author
