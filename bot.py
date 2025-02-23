import asyncio
import base64
import os
import discord
from ollama import AsyncClient

intents = discord.Intents.all()
intents.presences = False
client = discord.Client(intents=intents)

MODEL = 'qwen:0.5b'

# The message delay in-between splitten messages
# You can increase this to avoid rate-limits, even if theoretically, it can't happen
MESSAGE_DELAY = 0.1

MAX_MESSAGE_LENGTH = 2000

VISION_ENABLED = True

RESPOND_TO_ALL_MESSAGES = True

pinged_messages = {}

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

def split_messages(message: str):
    message_split = message.split(' ')

    last_i = 0
    characters_left = MAX_MESSAGE_LENGTH
    for i, word in enumerate(message_split):
        if (len(word)+1) > characters_left:
            yield ' '.join(message_split[last_i:i])
            characters_left = MAX_MESSAGE_LENGTH - len(word)
            last_i = i
        else:
            characters_left -= (len(word) + 1)

    yield ' '.join(message_split[last_i:])

@client.event
async def on_message(message: discord.Message):

    if client.user is None: return # shouldn't happen but pyright as always
    if message.author.id is client.user.id: return

    if message.content == "!clear":
        if message.channel.id in pinged_messages: pinged_messages[message.channel.id].clear()
        await message.reply(f"message history cleared for channel id {message.channel.id}")
        return

    if not client.user.mentioned_in(message) and not RESPOND_TO_ALL_MESSAGES: return

    images: list[str] = [
        base64.b64encode(await attachment.read()).decode()
        for attachment in message.attachments if attachment.content_type and attachment.content_type.startswith("image/")
    ]

    msg: str = message.content.replace(f"<@{client.user.id}>", "").strip()

    pinged_messages.setdefault(message.channel.id, [])

    pinged_messages[message.channel.id].append({
        "role": "user", 
        "content": msg,
        "images": images if VISION_ENABLED else []
    })

    try:
        async with message.channel.typing():
            response = await AsyncClient().chat(model=MODEL, messages=pinged_messages[message.channel.id])
            if not response.message.content: return # Average pyright user be like:

            pinged_messages[message.channel.id].append({
                "role": "assistant",
                "content": response.message.content
            })

            print(f"message: {msg} sent by {message.author}\nAI response: {response.message.content}")

            for message_to_send in split_messages(response.message.content): 
                    await message.reply(message_to_send)
                    await asyncio.sleep(MESSAGE_DELAY)

    except Exception as e:
        print(f"Error: {e}")
        await message.reply(f"`An error occured` ({e})")

client.run(os.environ['BOT_TOKEN'])
