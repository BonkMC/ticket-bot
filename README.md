# Bot Template
Template for making a discord bot in interactions.py.

# Using and Adding to this template
Create a new Python file in the commands folder to create a command. It will automatically be registered, but you should use example.py for reference. 
To create a role check, refer to the example in bot_instance.py.
Print color and discord bot colors are in utils.

# Running the template
Make sure you have the required packages listed in data/requirements.py.
Run bot.py to start the bot.

### Configuring your bot token
In your user home directory, create a folder called ```.pyconfig```. Create a file called ```secrets.ini```, and fill it with the following, replacing BOT_TOKEN with your bot's token:
```
[main]
bot_token=BOT_TOKEN
```
