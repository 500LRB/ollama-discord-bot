import discord
import asyncio
from ollama import AsyncClient
import time
import base64

intents = discord.Intents.all()
client = discord.Client(intents=intents)
model = 'llama3.2-vision' # the model you'd like to use for ollama
new_message_delay = 0.05 # in discord, if a message is over 4000 characters, this is for the delay of sending the split up text
enable_vision = True

pinged_messages = {}

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    

@client.event
async def on_message(message):
    if message.content == "!clear": #used to clear the channel memory/history
        async with message.channel.typing():
            if message.channel.id in pinged_messages:
                pinged_messages[message.channel.id].clear()
            await message.reply(f"message history cleared for channel id {message.channel.id}")

    elif client.user.mentioned_in(message):

        if message.attachments and enable_vision: #stuff used for the images
            image = []
            for chunk in range(0, len(message.attachments)): #some weird implementation i had to do to get discord.py to read multiple attachments
                attachment = message.attachments[chunk]
                attachment_content = await message.attachments[chunk].read()

                print(f"message has {len(message.attachments)} amount of attachments")
                
                if attachment.content_type.startswith("image/"):
                    image.append(base64.b64encode(attachment_content).decode("utf-8"))
                else:
                    print(f"unable to append attachment {chunk} as it isnt an image, instead is a {attachment.content_type}")
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
                print(f"message: {msg} sent by {message.author}\n AI response: {response.message.content}")
                if len(response.message.content) > 4000:
                    chunks = [response.message.content[i:i+4000 ] for i in range(0, len(response.message.content), 4000 )]
                    print(f"chunks made for this message is {len(chunks)}")
                    for chunk in chunks: 
                        await message.reply(chunk)
                        await asyncio.sleep(new_message_delay)
                else:
                    await message.reply(response.message.content)
        except Exception as e:
            print(f"Error: {e}")
            await message.reply("`something went wrong (please dm me to fix)`")

client.run("") #insert token here