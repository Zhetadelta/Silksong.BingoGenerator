import discord, os, json, network, random
from discord import app_commands, File, Embed
from typing import Optional
from board import CaravanGenerator, ByngosinkGenerator, DraftoutGenerator, GameType, GameName

CONFIG_PATH = os.path.join("config","settings.dat")

DEF_TAGLIMITS = {
        "craft" : 3,
        "flea" : 4,
        "expensive" : 2
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

ints = discord.Intents.default()
ints.members = True
client = newClient(intents = ints)

@client.event
async def on_ready():
    print(f"logged in as {client.user} with token {config()['token']} to {len(client.guilds)} servers")

@client.tree.error
async def on_app_command_error(interaction, error):
    try:
        await interaction.response.send_message(str(error), ephemeral=True)
    except:
        await interaction.followup.send(str(error), ephemeral=True)

def prog_options():
    opt = ["Act 1 Only", "No Clawline", "No Faydown (Default)", "Full Act 2", "Act 3 No Silk Soar", "Full Act 3", "Easier Mode", "Act 2 Only"]
    return [app_commands.Choice(name=i, value=i) for i in opt]

def mio_prog_options():
    opt = ["No Crucible (Default)", "No Vaults"]
    return [app_commands.Choice(name=i, value=i) for i in opt]

def size_options():
    return [app_commands.Choice(name=str(i), value=str(i)) for i in [5,6]]

def role_options():
    return [app_commands.Choice(name="Boop for Bing", value="1494131607118811257"),
            app_commands.Choice(name="Ring for Rando", value="1538693410964381716")]

def progStringToTags(progression):
    if progression is None or progression.value == "No Faydown (Default)":
        noTags = ['faydown','act3', 'silksoar']
    elif progression.value == "Act 1 Only":
        noTags = ["act2", "clawline", "faydown", 'act3', 'silksoar']
    elif progression.value == "No Clawline":
        noTags = ["clawline", "faydown", 'act3', 'silksoar']
    elif progression.value == "Full Act 2":
        noTags = ['act3', 'silksoar']
    elif progression.value == "Act 3 No Silk Soar":
        noTags = ['silksoar']
    elif progression.value == "Full Act 3":
        noTags = []
    elif progression.value == "Easier Mode":
        noTags = ["hard", "faydown", 'act3', 'silksoar']
    elif progression.value == "Act 2 Only":
        noTags = ["early", "dash", "cloak", "walljump", "widow", 'act3', 'silksoar']
    return noTags

def mioProgStringToTags(progression):
    if progression is None or progression.value == "No Crucible (Default)":
        noTags = []
    elif progression.value == "No Vaults":
        noTags = ["endgame", "vaults"]
    else:
        noTags = []
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
        
    thisBoard = CaravanGenerator("categorized_v3.json", int(size.value), noTags=noTags, 
                                     tagLimits=DEF_TAGLIMITS.copy(), patternBoard=pattern).export()

    await interaction.response.send_message(json.dumps(thisBoard), ephemeral=True)

@client.tree.command()
@app_commands.describe(preset="Tags to exclude based on preset categories.")
@app_commands.choices(preset=prog_options())
async def newotherside(interaction: discord.Interaction, preset: Optional[app_commands.Choice[str]] = None,
                       players: Optional[str] = "0"):
    """Generates a new board for byngosink's Get to the Other Side mode. Needs 100 goals!"""
    await interaction.response.defer(thinking=True)

    noTags = progStringToTags(preset)
    noTags.append("lockout")
    thisBoard = ByngosinkGenerator("categorized_v3.json", 10, noTags=noTags,
                                   gameType = GameType.GTTOS).export()
    session = network.byngosinkClient()
    n, url = session.newFixedRoom(thisBoard, "GTTOS10", gameName="Silksong", players=int(players))

    await interaction.followup.send(f"Room: {n} created at {url}")

@client.tree.command()
@app_commands.describe(preset="Tags to exclude based on preset categories.")
@app_commands.choices(preset=prog_options())
@app_commands.choices(size=size_options())
@app_commands.describe(size="The side length of the board. Default: 5")
async def newrosingy(interaction: discord.Interaction, preset: Optional[app_commands.Choice[str]] = None, size: Optional[app_commands.Choice[str]]=None):
    """Generates a new rosingy board. EXPERIMENTAL."""
    noTags = progStringToTags(preset)
    noTags.append("lockout")

    if size is None:
        size = app_commands.Choice(name="5", value="5")
    if int(size.value) == 5:
        session = network.bingosyncClient()
        baseName = "https://bingosync.com"
    elif int(size.value) == 6:
        session = network.caravanClient()
        baseName = "https://caravan.kobold60.com"

    thisBoard = CaravanGenerator("rosingy.json", int(size.value), noTags=noTags, tagLimits=DEF_TAGLIMITS.copy()).export()
    name, rId = session.newRoom(json.dumps(thisBoard), lockout=False)
    await interaction.response.send_message(f"Room: {name} created at {baseName}/{rId}")

@client.tree.command()
@app_commands.describe(preset="Tags to exclude based on preset categories.")
@app_commands.choices(preset=prog_options())
@app_commands.choices(size=size_options())
@app_commands.describe(players="Number of teams to create. Don't fill out to create your own teams.")
async def newbyngosink(interaction: discord.Interaction, pattern: bool = False, preset: Optional[app_commands.Choice[str]] = None, 
                  players: Optional[str] = "0",  size: Optional[app_commands.Choice[str]] = None):
    """Generates a new board and creates a byngosink room."""
    await interaction.response.defer(thinking=True)

    if size is None:
        size = app_commands.Choice(name="5", value="5")

    noTags = progStringToTags(preset)
    noTags.append("lockout") #exclude lockout-only goals
    try:
        players = int(players)
    except ValueError:
        players = 0
    
    thisBoard = ByngosinkGenerator("categorized_v3.json", int(size.value), noTags=noTags,
                                   patternBoard=pattern, tagLimits=DEF_TAGLIMITS.copy()).export()
    
    session = network.byngosinkClient()
    type = "Non-Lockout" if size.value == "5" else "Bingo6"
    n, rId = session.newFixedRoom(thisBoard, type, gameName="Silksong", players=players)
    await interaction.followup.send(f"Room: {n} created at {rId}")

@client.tree.command()
@app_commands.describe(preset="Tags to exclude based on preset categories.")
@app_commands.choices(preset=prog_options())
async def newbingosync(interaction: discord.Interaction, lockout: bool = False, pattern: bool = False, preset: Optional[app_commands.Choice[str]] = None):
    """Generates a new 5x5 board and creates a bingosync room with "fast" as the password."""
    await interaction.response.defer(thinking=True)

    noTags = progStringToTags(preset)
    if not lockout:
        noTags.append("lockout") 

    thisBoard = CaravanGenerator("categorized_v3.json", 5, noTags=noTags, tagLimits=DEF_TAGLIMITS.copy(),
                                 patternBoard=pattern).export()
    bsSession = network.bingosyncClient()
    n, rId = bsSession.newRoom(json.dumps(thisBoard), lockout=lockout)
    bsSession.close()
    await interaction.followup.send(f"Room: {n} created at https://bingosync.com/room/{rId}")

@client.tree.command()
@app_commands.describe(preset="Tags to exclude based on preset categories.")
@app_commands.choices(preset=prog_options())
async def newcaravan(interaction: discord.Interaction, lockout: bool = False, pattern: bool = False, preset: Optional[app_commands.Choice[str]] = None):
    """Generates a new 6x6 board and creates a caravan room with "fast" as the password."""
    await interaction.response.defer(thinking=True)

    noTags = progStringToTags(preset)
    if not lockout:
        noTags.append("lockout") #exclude lockout-only goals

    thisBoard = CaravanGenerator("categorized_v3.json", 6, noTags=noTags, tagLimits=DEF_TAGLIMITS.copy(),
                                 patternBoard=pattern).export()
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
    act1Tags = ["act2", "clawline", "faydown", 'act3', 'silksoar', "lockout"]
    act2Tags = ["early", "dash", "cloak", "walljump", "widow", 'act3', 'silksoar', "lockout"]

    act1Board = CaravanGenerator("categorized_v3.json", size, noTags=act1Tags, tagLimits=DEF_TAGLIMITS.copy()).export()
    act2Generator = CaravanGenerator("categorized_v3.json", size, noTags=act2Tags, tagLimits=DEF_TAGLIMITS.copy())
    act2Generator.linkBoards(act1Board)
    act2Board = act2Generator.export()

    n1, rId1 = session.newRoom(json.dumps(act1Board), lockout=False)
    n2, rId2 = session.newRoom(json.dumps(act2Board), lockout=False)
    session.close()
    await interaction.followup.send(f"Act 1 room: {n1} at {baseName}/room/{rId1}\nAct 2 room: {n2} at {baseName}/room/{rId2}")
    
@client.tree.command()
@app_commands.choices(size=size_options())
async def newtriplingy(interaction: discord.Interaction, size: Optional[app_commands.Choice[str]]=None):
    """Generates a set of triplingy rooms."""
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
    act1Tags = ["act2", "clawline", "faydown", 'act3', 'silksoar', "lockout"]
    act2Tags = ["early", "dash", "cloak", "walljump", "widow", 'act3', 'silksoar', "lockout"]
    act3Tags = ["early", "dash", "cloak", "walljump", "widow", "lockout", "act2", "clawline", "faydown"]

    act1Board = CaravanGenerator("categorized_v3.json", size, noTags=act1Tags, tagLimits=DEF_TAGLIMITS.copy()).export()
    act2Generator = CaravanGenerator("categorized_v3.json", size, noTags=act2Tags, tagLimits=DEF_TAGLIMITS.copy())
    act2Generator.linkBoards(act1Board)
    act2Board = act2Generator.export()
    act3Generator = CaravanGenerator("categorized_v3.json", 5, noTags=act3Tags, tagLimits=DEF_TAGLIMITS.copy())
    act3Generator.linkBoards(act1Board)
    act3Generator.linkBoards(act2Board)
    act3Board = act3Generator.export()

    n1, rId1 = session.newRoom(json.dumps(act1Board), lockout=False)
    n2, rId2 = session.newRoom(json.dumps(act2Board), lockout=False)
    if size == 6: #swap back to bingosync
        session.close()
        session = network.bingosyncClient()
    n3, rId3 = session.newRoom(json.dumps(act3Board), lockout=False)
    session.close()
    await interaction.followup.send(f"Act 1 room: {n1} at {baseName}/room/{rId1}\nAct 2 room: {n2} at {baseName}/room/{rId2}\nAct 3 room: {n3} at https://bingosync.com/room/{rId3}")

@client.tree.command()
@app_commands.choices(size=size_options())
@app_commands.choices(preset=mio_prog_options())
async def miobingo(interaction: discord.Interaction, preset: Optional[app_commands.Choice[str]]=None, size: Optional[app_commands.Choice[str]]=None):
    """All-in-one command for Mio Bingo. Password is 'fast'."""
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
    noTags = mioProgStringToTags(preset)

    thisBoard = CaravanGenerator("mio.json", size, noTags=noTags, gameName=GameName.Mio).export()
    n, rId = session.newRoom(json.dumps(thisBoard), game="mio")
    session.close()
    await interaction.followup.send(f"Room: {n} created at {baseName}/room/{rId} with password 'fast'.")


class DrafoutUI(discord.ui.View):
    def __init__(self, noTags, size, player1: discord.user, player2: discord.user, parentInteraction: discord.Interaction):
        super().__init__(timeout=1800) #30 minutes
        self.generator = DraftoutGenerator(noTags, size)
        self.p1 = player1
        self.p2 = player2
        self.totalSize = size**2
        self.active = self.p1
        self.color = int(discord.Colour.from_str(random.choice(network.TEAM_COLORS)))
        self.name = random.choice(network.ROOM_NAMES)
        self.currentOptions = self.generator.showGoals()
        self.parentInteract = parentInteraction
        self.init = False
        self.message = None

    def swapPlayer(self):
        if self.active == self.p1:
            self.active = self.p2
        else:
            self.active = self.p1

    @discord.ui.button(style=discord.ButtonStyle.blurple, label="Option 1")
    async def button1(self, interact : discord.Interaction, button : discord.ui.button):
        if interact.user.id != self.active.id:
            await interact.response.send_message("It's not your turn!", ephemeral=True)
            return 

        if not self.init:
            self.init = True
            await interact.response.defer(ephemeral=True)
            await self.rebuildMessage()
            return
        
        await interact.response.defer(ephemeral=True)
        if self.generator.addGoal(self.currentOptions[0]): #nonzero until all goals picked YAY PYTHON
            self.currentOptions = self.generator.showGoals()
            self.swapPlayer()
            await self.rebuildMessage()
        else:
            await interact.followup.send("All goals picked! Please wait while I make a room.")
            await self.postRoom()

    @discord.ui.button(style=discord.ButtonStyle.blurple, label="Option 2")
    async def button2(self, interact : discord.Interaction, button : discord.ui.button):
        if interact.user.id != self.active.id:
            await interact.response.send_message("It's not your turn!", ephemeral=True)
            return

        if not self.init:
            self.init = True
            await interact.response.defer(ephemeral=True)
            await self.rebuildMessage()
            return
        
        await interact.response.defer(ephemeral=True)
        if self.generator.addGoal(self.currentOptions[1]): #nonzero until all goals picked YAY PYTHON
            self.currentOptions = self.generator.showGoals()
            self.swapPlayer()
            await self.rebuildMessage()
        else:
            await interact.followup.send("All goals picked! Please wait while I make a room.")
            await self.postRoom()

    @discord.ui.button(style=discord.ButtonStyle.blurple, label="Option 3")
    async def button3(self, interact : discord.Interaction, button : discord.ui.button):
        if interact.user.id != self.active.id:
            await interact.response.send_message("It's not your turn!", ephemeral=True)
            return 

        if not self.init:
            self.init = True
            await interact.response.defer(ephemeral=True)
            await self.rebuildMessage()
            return
        
        await interact.response.defer(ephemeral=True)
        if self.generator.addGoal(self.currentOptions[2]): #nonzero until all goals picked YAY PYTHON
            self.currentOptions = self.generator.showGoals()
            self.swapPlayer()
            await self.rebuildMessage()
        else:
            await interact.followup.send("All goals picked! Please wait while I make a room.")
            await self.postRoom()

    async def rebuildMessage(self):
        if self.message is None:
            temp = await self.parentInteract.original_response()
            self.message = await temp.fetch()

        goalString = ""
        for goal in self.generator.getList():
            goalString += goal["name"]+"\n"

        embedDic = {
            "title" : self.name,
            "color" : self.color,
            "fields" : [
                    {
                        "name" : "Current goals:",
                        "value" : goalString,
                        "inline" : False
                        },
                    {
                        "name" : "**Currently picking:**",
                        "value" : self.active.display_name,
                        "inline" : False
                    },
                    {
                        "name" : "Option 1",
                        "value" : self.currentOptions[0]["name"]
                    },
                    {
                        "name" : "Option 2",
                        "value" : self.currentOptions[1]["name"]
                    },
                    {
                        "name" : "Option 3",
                        "value" : self.currentOptions[2]["name"]
                    }
                ]
        }

        await self.message.edit(embed=discord.Embed.from_dict(embedDic))

    async def postRoom(self):
        if self.totalSize == 25:
            session = network.bingosyncClient()
            baseName = "https://bingosync.com"
        elif self.totalSize == 36:
            session = network.caravanClient()
            baseName = "https://caravan.kobold60.com"
        formattedBoard = []
        for g in self.generator.getList():
            formattedBoard.append({"name": g["name"]})
        random.shuffle(formattedBoard)
        n, rId = session.newRoom(json.dumps(formattedBoard), roomName=self.name)
        session.close()
        await self.parentInteract.followup.send(f"Room: {n} created at {baseName}/room/{rId}")

@client.tree.command()
@app_commands.describe(preset="Tags to exclude based on preset categories.")
@app_commands.describe(opponent="Ping your opponent here!")
@app_commands.choices(preset=prog_options())
@app_commands.choices(size=size_options())
async def newdraftout(interaction: discord.Interaction, opponent:str, preset: Optional[app_commands.Choice[str]] = None, size: Optional[app_commands.Choice[str]]=None):
    """
    Draft goals into a lockout board.
    """
    opp = client.get_user(int(opponent.strip()[2:-1]))
    noTags = progStringToTags(preset)
    size = 5 if size is None else int(size.value)
    await interaction.response.send_message("Click any button to start!", view=DrafoutUI(noTags, size, interaction.user, opp, interaction))


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

@client.tree.command()
@app_commands.choices(roleid=role_options())
async def togglerole(interaction: discord.Interaction, roleid: app_commands.Choice[str]):
    """Adds (or removes) the Boop for Bing role."""
    try:
        user = interaction.user
        boopRoleid = int(roleid.value)
        boopRole = interaction.guild.get_role(boopRoleid)
        if boopRole not in user.roles:
            await user.add_roles(boopRole)
            await interaction.response.send_message("Role added!", ephemeral=True)
        else:
            await user.remove_roles(boopRole)
            await interaction.response.send_message("Role removed!", ephemeral=True)
    except:
        await interaction.response.send_message("You need to run this command on the Silksong Bingo server. If you did, then it broke.", ephemeral=True)


if __name__ == "__main__":
    client.run(config()["token"])