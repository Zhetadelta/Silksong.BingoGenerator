import discord, board, os, json, network, random
from discord import app_commands
from typing import Optional

CONFIG_PATH = os.path.join("config","settings.dat")

BOARD_KWARGS = { #sensible defaults for new boards
    "tagLimits" : {
        "craft" : 3,
        "flea" : 3
    }
}

def config():
    if not os.path.exists(os.path.dirname(CONFIG_PATH)):
        os.makedirs(os.path.dirname(CONFIG_PATH))

    if not os.path.exists(CONFIG_PATH):
        #generate default config
        config_dic = {
                "token" : "",
                "owners" : [
                    0000
                    ],
                "command_servers" : [
                    0000
                    ]
            }
        with open(CONFIG_PATH, "w") as config_file:
            json.dump(config_dic, config_file, indent=4)
            print("please fill in bot token and any bot admin discord ids to the new config.json file!")
            quit()
    else:
        with open(CONFIG_PATH) as config_file:
            return json.load(config_file)

class newClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        

    async def setup_hook(self):
        for guild_id in config()["command_servers"]:
            try:
                guild = discord.Object(id=guild_id)
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
            except:
                pass
        await self.tree.sync()

client = newClient(intents = discord.Intents.default())

@client.event
async def on_ready():
    print(f"logged in as {client.user} with token {config()['token']} to {len(client.guilds)} servers")

@client.tree.error
async def on_app_command_error(interaction, error):
    try:
        await interaction.response.send_message(f"The following error was encountered: {str(error.__cause__)}. Let Abyss know!", ephemeral=True)
    except:
        await interaction.followup.send(f"The following error was encountered: {str(error.__cause__)}. Let Abyss know!", ephemeral=True)

def prog_options():
    opt = ["Act 1 Only", "No Clawline", "No Faydown", "Easier Mode", "Act 2 Only"]
    return [app_commands.Choice(name=i, value=i) for i in opt]

def size_options():
    return [app_commands.Choice(name=str(i), value=str(i)) for i in [5,6]]

def progStringToTags(progression):
    if progression is None:
        noTags = []
    elif progression.value == "Act 1 Only":
        noTags = ["act2", "clawline", "faydown"]
    elif progression.value == "No Clawline":
        noTags = ["clawline", "faydown"]
    elif progression.value == "No Faydown":
        noTags = ["faydown"]
    elif progression.value == "Easier Mode":
        noTags = ["hard", "faydown"]
    elif progression.value == "Act 2 Only":
        noTags = ["early", "dash", "cloak", "walljump", "widow"]
    return noTags

@client.tree.command()
@app_commands.describe(preset="Tags to exclude based on preset categories.")
@app_commands.choices(preset=prog_options())
@app_commands.choices(size=size_options())
async def newboard(interaction: discord.Interaction, lockout: bool = False, preset: Optional[app_commands.Choice[str]] = None, pattern: bool = False, size: Optional[app_commands.Choice[str]]=None):
    """Generates a new board for bingo."""
    noTags = progStringToTags(preset)
    if not lockout:
        noTags.append("lockout")
    if size is None:
        size = app_commands.Choice(name="5", value="5")
    thisBoard = board.bingosyncBoard(noTags=noTags, **BOARD_KWARGS, noBlocking = pattern, size=int(size.value)**2)
    await interaction.response.send_message(json.dumps(thisBoard), ephemeral=True)

@client.tree.command()
@app_commands.describe(preset="Tags to exclude based on preset categories.")
@app_commands.choices(preset=prog_options())
async def newroom(interaction: discord.Interaction, lockout: bool = False, pattern: bool = False, preset: Optional[app_commands.Choice[str]] = None):
    """Generates a new board and creates a bingosync room."""
    await interaction.response.defer(thinking=True)

    noTags = progStringToTags(preset)
    if not lockout:
        noTags.append("lockout") #exclude lockout-only goals
    thisBoard = board.bingosyncBoard(noTags=noTags, **BOARD_KWARGS, noBlocking = pattern)
    bsSession = network.bingosyncClient()
    n, rId = bsSession.newRoom(json.dumps(thisBoard), lockout=lockout)
    bsSession.close()
    await interaction.followup.send(f"Room: {n} created at https://bingosync.com/room/{rId}")

@client.tree.command()
@app_commands.describe(preset="Tags to exclude based on preset categories.")
@app_commands.choices(preset=prog_options())
async def newcaravan(interaction: discord.Interaction, lockout: bool = False, pattern: bool = False, preset: Optional[app_commands.Choice[str]] = None):
    """Generates a new 6x6 board and creates a caravan room."""
    await interaction.response.defer(thinking=True)

    noTags = progStringToTags(preset)
    if not lockout:
        noTags.append("lockout") #exclude lockout-only goals
    thisBoard = board.bingosyncBoard(noTags=noTags, **BOARD_KWARGS, noBlocking = pattern, size=36)
    bsSession = network.caravanClient()
    n, rId = bsSession.newRoom(json.dumps(thisBoard), lockout=lockout)
    bsSession.close()
    await interaction.followup.send(f"Room: {n} created at https://caravan.kobold60.com/room/{rId}")

@client.tree.command()
@app_commands.choices(size=size_options())
async def newdoublingy(interaction: discord.Interaction, size: Optional[app_commands.Choice[str]]=None):
    """Generates a pair of doublingy rooms."""
    await interaction.response.defer(thinking=True)
    if size is None:
        size = app_commands.Choice(name="5", value="5")
    size = int(size.value)
    if size == 5:
        session = network.bingosyncClient()
        baseName = "https://bingosync.com"
    elif size == 6:
        session = network.caravanClient()
        baseName = "https://caravan.kobold60.com"
    act1Tags = ["act2", "clawline", "faydown", "lockout"]
    act2Tags = ["early", "dash", "cloak", "walljump", "widow", "lockout"]
    act1Board, act2Board = board.linkedBoards(noTags=(act1Tags, act2Tags), size=size)
    n1, rId1 = session.newRoom(json.dumps(act1Board), lockout=False)
    n2, rId2 = session.newRoom(json.dumps(act2Board), lockout=False)
    session.close()
    await interaction.followup.send(f"Act 1 room: {n1} at {baseName}/room/{rId1}\nAct 2 room: {n2} at {baseName}/room/{rId2}")

@client.tree.command()
@app_commands.describe(tags="Comma-seperated tags to exclude from board generation")
async def advancedboard(interaction: discord.Interaction, tags: str):
    """Generates a new board with specific tags excluded."""
    noTags = [t.strip() for t in tags.split(",")]
    thisBoard = board.bingosyncBoard(noTags=noTags)
    await interaction.response.send_message(json.dumps(thisBoard), ephemeral=True)

@client.tree.command()
@app_commands.describe(hands="Comma-seperated list of names.")
@app_commands.describe(brains="Comma-seperated list of names.")
async def handbrainteams(interaction: discord.Interaction, hands: str, brains: str):
    """Splits hands and brains into teams."""
    handsList = hands.split(",")
    random.shuffle(handsList)
    brainsList = brains.split(",")
    random.shuffle(brainsList)
    teams = zip(handsList, brainsList)
    out = "The teams are:\n"
    for hand, brain in teams:
        out = out + f"{hand}, {brain}\n"
    await interaction.response.send_message(out)

@client.tree.command()
@app_commands.describe(hands="Comma-seperated list of names.")
@app_commands.describe(artists="Comma-seperated list of names.")
@app_commands.describe(interpreters="Comma-seperated list of names.")
async def pictionaryteams(interaction: discord.Interaction, hands: str, artists: str, interpreters: str):
    """Splits the players into pictionary teams."""
    handsList = hands.split(",")
    random.shuffle(handsList)
    brainsList = interpreters.split(",")
    random.shuffle(brainsList)
    artList = artists.split(",")
    random.shuffle(artList)
    teams = zip(handsList, brainsList, artList)
    out = "The teams are:\n"
    for hand, brain, art in teams:
        out = out + f"{hand}, {brain}, {art}\n"
    await interaction.response.send_message(out)

@client.tree.command()
@app_commands.describe(players="Comma-seperated list of names.")
@app_commands.describe(teamsize="Players per team")
async def teams(interaction: discord.Interaction, players: str, teamsize: int):
    """Splits players into teams."""
    playerList = players.split(",")
    random.shuffle(playerList)
    #check for sanity
    if len(playerList) % teamsize != 0:
        await interaction.response.send_message("That many players cannot be divided into teams of that size.", ephemeral=True)
    out = "The teams are:\n"
    for i in range(0, len(playerList), teamsize):
        team = playerList[i:i+teamsize]
        out = out + f"{team}\n"
    await interaction.response.send_message(out)

if __name__ == "__main__":
    client.run(config()["token"])