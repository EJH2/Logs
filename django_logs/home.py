import json
import pytz

from datetime import datetime

embed = json.dumps({
    "description": "Heck, even attachments are included...",
    "color": 1362241,
    "timestamp": datetime.now(tz=pytz.UTC).isoformat(),
    "thumbnail": {
        "url": "https://cdn.discordapp.com/embed/avatars/2.png"
    },
    "image": {
        "url": "https://cdn.discordapp.com/embed/avatars/3.png"
    },
    "author": {
        "name": "Embeds too!",
        "url": "https://discordapp.com",
        "icon_url": "https://cdn.discordapp.com/embed/avatars/4.png"},
    "fields": [
        {
            "name": "🤔",
            "value": "is there anything this can't do?"
        },
        {
            "name": "😱",
            "value": "not really..."
        },
        {
            "name": "🙄",
            "value": "if you find something we don't support, feel free to message <@EJH2#0330 (125370065624236033)"
                     "> on [Discord](https://discordapp.com)!"
        },
        {
            "name": "How do I use this?",
            "value": "Simply go to [homepage]/view?url=yoururlhere",
            "inline": True
        },
        {
            "name": "What happens then?",
            "value": "You get your own `unique` log, looking just as cool as this!",
            "inline": True
        }
    ]
})

content = f"""[]
[Discord Log Viewer#0000 (0000000000000000)]
[EJH2#0330 (125370065624236033)]
[]
[]

[0000-00-00 00:00:00] (125370065624236033) Discord Log Viewer#0000 : Welcome to **Discord Log Viewer!**

Format virtually any log file into an aesthetically pleasing and readable format. Currently, we support:
<:yes:487035217752752129> Emojis :sunglasses:
<:yes:487035217752752129> *Italics* 
<:yes:487035217752752129> **Bold**
<:yes:487035217752752129> __Underline__
<:yes:487035217752752129> ~~Strikethrough~~
<:yes:487035217752752129> `Inline code`
<:yes:487035217752752129> ||Spoilers||
<:yes:487035217752752129> ||***__~~`A combination of all of them`~~__***||
<:yes:487035217752752129> ```diff
+ Multi-line code

# Supported log types:
+ Auttaja
+ CapnBot
+ GearBot
+ GiraffeDuck
+ Logger
+ Rosalina Bottings
+ Rowboat
    - A1RPL4NE
    - Aperture
    - Flygbåt
    - Heimdallr
    - Jetski
    - LMG Showboat
    - Rawgoat
    - Speedboat
+ SajuukBot
+ Vortex
``` | Attach: https://cdn.discordapp.com/attachments/352443826473795585/557413456442163200/0.png, https://cdn.discordapp.com/attachments/352443826473795585/557034119939358751/gitignore | RichEmbed: {embed}"""
