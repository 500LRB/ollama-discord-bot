import discord
import asyncio
from ollama import AsyncClient
import time
import base64

intents = discord.Intents.all()
client = discord.Client(intents=intents)
model = 'llama3.2-vision'

pinged_messages = {}

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    

@client.event
async def on_message(message):
    if message.content == "!clear":
        pinged_messages[message.channel.id] = []
        message.send(f"message history cleared for channel id {message.channel.id}")

    elif client.user.mentioned_in(message):

        if message.attachments:
            image = []
            for chunk in range(0, len(message.attachments)):
                attachment = message.attachments[chunk]
                attachment_content = await message.attachments[chunk].read()
                print(message.attachments)
                print(attachment)
                print(attachment.content_type)
                if attachment.content_type.startswith("image/"):
                    image.append(base64.b64encode(attachment_content).decode("utf-8"))
                else:
                    return()
        else:
            image = []

        msg = message.content.replace(f"<@{client.user.id}>", "").strip()
        if message.channel.id not in pinged_messages:
            pinged_messages[message.channel.id] = []

        pinged_messages[message.channel.id].append(
            {
                "role": "user", 
                "content": f"{msg}",
                "images": image
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
                print(pinged_messages[message.channel.id])
                if len(response.message.content) > 4000:
                    chunks = [response.message.content[i:i+4000 ] for i in range(0, len(response.message.content), 4000 )]
                    print(f"chunks made {len(chunks)}")
                    for chunk in chunks: 
                        await message.reply(chunk)
                        await asyncio.sleep(0.05)
                else:
                    await message.reply(response.message.content)
        except Exception as e:
            print(f"Error: {e}")
            await message.reply("`something went wrong (please dm me to fix)`")

client.run("") #insert token here