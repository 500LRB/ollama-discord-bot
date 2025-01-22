import discord
import asyncio
from ollama import AsyncClient
import time

intents = discord.Intents.all()
client = discord.Client(intents=intents)

pinged_messages = {}

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    

@client.event
async def on_message(message):
    if client.user.mentioned_in(message) and not message.author.bot:
        msg = message.content.replace(f"<@{client.user.id}>", "").strip()
        if message.channel.id not in pinged_messages:
            pinged_messages[message.channel.id] = []

        pinged_messages[message.channel.id].append(
            {
                "role": "user", 
                "content": f"{msg}"
            })

        try:
            async with message.channel.typing():
                response = await AsyncClient().chat(
                    model='llama3.2', 
                    messages=pinged_messages[message.channel.id]
                )
                pinged_messages[message.channel.id].append(
                    {
                        "role": "assistant",
                        "content": response.message.content
                    })
                print(pinged_messages[message.channel.id])
                if len(response.message.content) > 2000:
                    chunks = [response.message.content[i:i+2000 ] for i in range(0, len(response.message.content), 2000 )]
                    print(f"chunks made {len(chunks)}")
                    for chunk in chunks: 
                        await message.reply(chunk)
                        await asyncio.sleep(0.05)
                else:
                    await message.reply(response.message.content)
        except Exception as e:
            print(f"Error: {e}")
            await message.reply("`something went wrong (please dm me to fix)`")

client.run("")