import discord
import os
from utils import init_tracking, add_entry


client = discord.Client()



@client.event
async def on_ready():
  print("We have logged in as {0.user}".format(client))

@client.event
async def on_message(message):
  if message.author == client.user:
    return

  if message.content.startswith("$hello"):
    await message.channel.send('Hello!\n')
  
  if message.content.startswith("$init"):
    await message.channel.send(init_tracking(message))
 
  if message.content.startswith("$paid"):
    await message.channel.send(add_entry(message))

if __name__=="__main__":
  client.run(os.getenv('TOKEN'))
