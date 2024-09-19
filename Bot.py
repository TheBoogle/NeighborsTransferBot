import discord
from discord.ext import commands
import json
import requests

# Load Roblox API key and Discord token from a JSON file
with open('APIKey.json') as f:
	loaded = json.load(f)
	API_KEY = loaded["RobloxKey"]
	DISCORD_TOKEN = loaded["DiscordToken"]

# Initialize bot with necessary intents
intents = discord.Intents.default()
intents.message_content = True  # To capture content from messages
bot = commands.Bot(command_prefix="!", intents=intents)

# Roblox API interaction functions
def update_entry(universe, data_store, scope, entry_id, api_key, value, users, attributes):
	url = f'https://apis.roblox.com/cloud/v2/universes/{universe}/data-stores/{data_store}/scopes/{scope}/entries?id={entry_id}'
	headers = {'x-api-key': api_key}
	payload = {"value": value, "users": users, "attributes": attributes}
	response = requests.post(url, headers=headers, json=payload)
	return response.json()

def delete_entry(universe, data_store, scope, entry, api_key):
	url = f'https://apis.roblox.com/cloud/v2/universes/{universe}/data-stores/{data_store}/scopes/{scope}/entries/{entry}'
	headers = {'x-api-key': api_key}
	response = requests.delete(url, headers=headers)
	return response.json()

def get_entry(universe, data_store, scope, entry, api_key):
	url = f'https://apis.roblox.com/cloud/v2/universes/{universe}/data-stores/{data_store}/scopes/{scope}/entries/{entry}'
	headers = {'x-api-key': api_key}
	response = requests.get(url, headers=headers)
	return response.json()

def get_user_info(user, api_key):
	url = f'https://apis.roblox.com/cloud/v2/users/{user}'
	headers = {'x-api-key': api_key}
	response = requests.get(url, headers=headers)
	return response.json()

def transfer_regular_to_17(userid):
	profile = get_user_info(userid, API_KEY)
	if not profile or profile["about"] != "I WANT TO TRANSFER MY DATA":
		return "Player has not verified. Cancelling transfer. Set your about me on Roblox to 'I WANT TO TRANSFER MY DATA' to proceed."

	# Check if they already transferred in the past
	other_data = get_entry(4924789901, "PlayerData", "Version1", userid, API_KEY)
	if other_data and any(i[0] == "Transferred" for i in other_data["value"]):
		return "Already transferred"

	regular_data = get_entry(4452297356, "PlayerData", "Version1", "41372847", API_KEY)
	if not regular_data:
		return "No data found to transfer"

	# Modify data and transfer
	regular_data = regular_data["value"]
	regular_data.append(["Transferred", "True"])
	delete_entry(4924789901, "PlayerData", "Version1", userid, API_KEY)
	update_entry(4924789901, "PlayerData", "Version1", userid, API_KEY, regular_data, [], {})
	
	print(f"Transferred data for {userid}")

	return "Transfer successful"

# Create select menu for user interaction
class TransferMenu(discord.ui.Select):
	def __init__(self):
		options = [
			discord.SelectOption(label="Transfer Data to 17+", description="Transfer my data to Neighbors 17+, I understand this is non-reversible."),
			discord.SelectOption(label="Cancel", description="Cancel the operation.")
		]
		super().__init__(placeholder="Choose an action...", min_values=1, max_values=1, options=options)

	async def callback(self, interaction: discord.Interaction):
		if self.values[0] == "Transfer Data to 17+":
			# Ask the user for their Roblox ID with an ephemeral message (visible only to them)
			await interaction.response.send_message("Please enter your Roblox ID:", ephemeral=True)
			msg = await bot.wait_for("message", check=lambda msg: msg.author == interaction.user)
			
			# Capture the user's Roblox ID from the message
			roblox_id = msg.content
			result = transfer_regular_to_17(roblox_id)
			
			# delete the message
			await msg.delete()
			
			await interaction.followup.send(result, ephemeral=True)  # Send the follow-up as ephemeral
		elif self.values[0] == "Cancel":
			await interaction.response.send_message("Operation cancelled.", ephemeral=True)

# Create a view for the select menu
class TransferView(discord.ui.View):
	def __init__(self):
		super().__init__()
		self.add_item(TransferMenu())

# Slash command with ephemeral responses
@bot.slash_command(name="neighborstransfer", description="Transfer your progress from Neighbors to Neighbors 17+. (NON REVERSIBLE)")
async def neighborstransfer(ctx):
	   await ctx.respond("# WARNING! \nThis is non-reversible, you will not be able to restore your 17+ data and it will be completely overwritten by your regular data!\n Make sure you truly want to do this\n**You must set your about me on Roblox to** `I WANT TO TRANSFER MY DATA`\nYou can only do this once per account!\n# Make sure to disconnect from Neighbors before doing this!\n\nPlease choose an action:", view=TransferView(), ephemeral=True)


# Event listener when bot is ready
@bot.event
async def on_ready():
	print(f'Logged in as {bot.user}')

# Start the bot with the loaded token
bot.run(DISCORD_TOKEN)
