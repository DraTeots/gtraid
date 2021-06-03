import discord

class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        print('Message from {0.author}: {0.content}'.format(message))

client = MyClient()
client.run('ODQ5MTEwNjcwNDY4NDQ4MjY2.YLWZ7w.cdjXV0uwQN6uuD7OQmW8nfMuUxI')
