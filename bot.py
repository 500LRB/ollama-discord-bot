import asyncio
import base64
import os

import discord
from ollama import AsyncClient

client = discord.Client(intents=discord.Intents.all())

MODEL_TO_USE: str = 'qwen:0.5b'
MESSAGE_DELAY: float = 0.05
MESSAGE_LENGTH_LIMIT: int = 2000
ENABLED_VISION: bool = True

# we go crazy
pinged_messages: dict[int, list[dict[str, str | list[str]]]] = {}

def split_messages(message: str):
    message_split = message.split(' ')

    characters_left = MESSAGE_LENGTH_LIMIT

    last_i = 0
    for i, word in enumerate(message_split):
        if (len(word)+1) > characters_left:

            yield ' '.join(message_split[last_i:i])
            characters_left = MESSAGE_LENGTH_LIMIT - len(word)
            last_i = i

        else:
            characters_left -= (len(word) + 1)

    yield ' '.join(message_split[last_i:])


@client.event
async def on_message(message: discord.Message) -> None:
    if client.user is None: return
    if message.author is client.user: return

    if message.content == "!clear":
        pinged_messages[message.channel.id] = []
        await message.reply(f"message history cleared for <#{message.channel.id}>")
        return

    if not client.user.mentioned_in(message): return

    images: list[str] = [
        base64.b64encode(await attachment.read()).decode()
        for attachment in message.attachments if attachment.content_type and attachment.content_type.startswith("image/")
    ]

    message_clean = message.content.replace(f"<@{client.user.id}>", "").strip()

    pinged_messages.setdefault(message.channel.id, [])

    pinged_messages[message.channel.id].append({
        "role": "user",
        "content": message_clean,
        "images": images if ENABLED_VISION else []
    })

    try:
        async with message.channel.typing():
            response = await AsyncClient().chat(
                model = MODEL_TO_USE,
                messages = pinged_messages[message.channel.id]
            )

            if response.message.content is None: raise Exception('die')

            pinged_messages[message.channel.id].append({
                "role": "assistant",
                "content": response.message.content
            })

            print(f"message: {message_clean} sent by {message.author}\nAI response: {response.message.content}")

            for message_to_send in split_messages(response.message.content):
                await message.reply(message_to_send)
                await asyncio.sleep(MESSAGE_DELAY)

    except Exception as e:
        print(f"Error: {e}")
        await message.reply(f"`{e}`")

client.run(os.environ['BOT_TOKEN'])
