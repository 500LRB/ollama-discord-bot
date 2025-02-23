import discord
import asyncio
from ollama import AsyncClient
import base64
import os

intents = discord.Intents.all()
client = discord.Client(intents=intents)
model = 'llama3.2-vision' # the model you'd like to use for ollama
new_message_delay = 0.05 # in discord, if a message is over 2000 characters, this is for the delay of sending the split up text
enable_vision = True
respond_all = False #this makes it respond to EVERYTHING

pinged_messages = {}

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    

@client.event
async def on_message(message):
    if message.author is client.user: 
        return #doesnt respond to itself
    elif client.user is None: 
        return
    elif message.content == "!clear": #used to clear the channel memory/history
        async with message.channel.typing():
            if message.channel.id in pinged_messages:
                pinged_messages[message.channel.id] = []
                await message.channel.send(f"message history cleared for channel id {message.channel.id}")

    elif client.user.mentioned_in(message) or respond_all:
        msg = message.content.replace(f"<@{client.user.id}>", "").strip()
        image = []
        if message.channel.id not in pinged_messages:
            pinged_messages[message.channel.id] = []

        if message.attachments and enable_vision: #stuff used for the images
            for attachment in message.attachments: #some weird implementation i had to do to get discord.py to read multiple attachments
                attachment_content = await attachment.read()
                print(f"message has {len(message.attachments)} amount of attachments")
                
                if attachment.content_type.startswith("image/"):
                    image.append(base64.b64encode(attachment_content).decode("utf-8"))
                else:
                    print(f"unable to append attachment {attachment} as it isnt an image, instead is a {attachment.content_type}")

        pinged_messages[message.channel.id].append(
            {
                "role": "user", 
                "content": f"{msg}",
                "images": image if enable_vision else []
            })

        try:
            async with message.channel.typing():
                response = await AsyncClient().chat(
                    model=model, 
                    messages=pinged_messages[message.channel.id]
                )
                pinged_messages[message.channel.id].append(
                    {
                        "role": "assistant",
                        "content": response.message.content
                    })
                print(f"message: {msg} sent by {message.author}\nAI response: {response.message.content}")

                if len(response.message.content) > 2000: #sending messages and stuff
                    characters_left = 2000
                    message_split = response.message.content.split(' ')
                    last_i = 0
                    chunks = []
                    for i, word in enumerate(message_split):
                        if (len(word)+1) > characters_left:
                            words = ' '.join(message_split[last_i:i])
                            chunks.append(words)
                            characters_left = 2000 - len(word)
                            last_i = i
                        else:
                            characters_left -= (len(word) + 1)
                    chunks.append(' '.join(message_split[last_i:]))
                    print(f"chunks made for this message is {len(chunks)}")
                    for messages in chunks: 
                        await message.reply(messages)
                        await asyncio.sleep(new_message_delay)
                else:
                    await message.reply(response.message.content)

        except Exception as e:
            print(f"Error: {e}")
            await message.reply("`something went wrong (please dm me to fix)`")

client.run(os.environ['BOT_TOKEN'])