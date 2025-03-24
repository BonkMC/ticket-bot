from interactions import listen
from bot_instance import bot
import os
for i in os.listdir("commands"):
    if i.endswith(".py"):
        exec(f"from commands.{i.replace('.py', '')} import *")

@listen()
async def on_ready():
    print("Your bot has started.")

# Start the bot
bot.start()
