import requests, random, json
from time import sleep
from websockets.sync.client import connect

ROOM_NAMES = [
    "Abyssopelagic Zone",
    "Rose Garden",
    "Not a Human Hand",
    "Almost a Tundra",
    "Sentient Blobs",
    "Bing of the Hill with Multiverse Time Travel",
    "Skongin It",
    "Fa Ri Du La Ci Ma Ne",
    "POSHANKA",
    "Savage Beastfly",
    "Choral Chambers",
    "Wispfire Lantern",
    "OOSHKA NEEPLY",
    "Neepless",
    "Flea Route",
    "Cloakless",
    "Double Shanka",
    "Quad Shanka",
    "Looks to the Moon",
    "Silkshot Weaver",
    "Weavenest Absolom",
    "Yuri Stay Winning",
    "Daves Shard",
    "Start on Bind",
    "Bilewater Hidden Bench",
    "Running for Rosaries",
    "Fourth Chorus Skip Skip",
    "Hoker RNG",
    "Crustnut Powder",
    "Shaw and Other Things to Yell at Your Enemies",
    "Silk and Possibly Song",
    "Lacenet",
    "Architect Crest",
    "Bingy Bingus Bongus Blafoingus",
    "Beast Boost Uppie Strike",
    "Silkeater Noclip",
    "Archies Mossberry",
    "Key Route",
    "Silver Bells Loop",
    "Shawtoof",
    "Hang_08",
    "Lets Go Gambling",
    "Cog_08",
    "Dust_Maze_07",
    "Failure",
    "Triple GMS",
    "Early Second Skarrguard",
    "Git Gud",
    "Proper Substance Use",
    "Mrs Streamer",
    "I Suggest Forcefem",
    "Toxic Yuri Wins Again",
    "Zango Becomes Blueful",
    "Forcefemmed",
    "Sometimes Its Not Our Turn to Talk",
    "Fourth Chorus Skip Skip Skip",
    "Nyaaaaaa",
    "Pimpogos",
    "Save Me From Act 1",
    "Moss Grotto Reset",
    "I Need Shards For My Compass",
    "Debug Hotkey Check",
    "Hornt",
    "1999",
    "Krattball",
    "Webbed Bouce",
    "Skimaaaanama",
    "Heavy Brosary Necklace",
    "Lunaberry",
    "Cogwork Canyon",
    "15 Minutes and a Coffee",
    "Hornts in Boards",
    "BS2 is BS",
    "Canonically Plural Hornet",
    "V bbbbbbbbbbbbb      vv v    b bb"
]

TEAM_NAMES = [
    "Red Tools",
    "Blue Tools",
    "Yellow Tools",
    "Atla",
    "Cindril",
    "Karn",
    "Murglin",
    "Absolom",
    "Karmelita",
    "Clover",
    "Nyleth",
    "Pebb",
    "Forge Daughter",
    "Jubilana",
    "Twelfth Architect",
    "Silkspear",
    "Threadstorm",
    "Sharpdart",
    "Crosstitch",
    "Rune Rage",
    "Pale Nails",
    "Beastlings",
    "plasmium", #caravan teams
    "sherma",
    "gilly",
    "vespa",
    "magnetite",
    "huntress",
    "scrounge",
    "beastling",
    "Hornt", #silly starts
    "Soul",
    "Silk",
    "Darkness",
    "Yuri",
    "Yaoi"
]

TEAM_COLORS = [
    "#237e3d",
    "#c32a45",
    "#0d48b5",
    "#ddc700",
    "#cd560b",
    "#f5c06c",
    "#80c786",
    "#75b4d8",
    "#481572"
]

STANDARD_PAYLOAD = {
    "game_type": 18, #custom game
    "variant_type": 18, #custom game, both are required
    #The following can be adjusted on a case-by-case basis
    "seed": "",
    "hide_card" : 1,
    "custom_json" : None,
    "lockout_mode" : 1 #1 is no lockout
}

NEW_CARD_PAYLOAD = STANDARD_PAYLOAD.copy()
NEW_CARD_PAYLOAD.update({
    "nickname" : "Bingyflea",
    #update pretty much all of these
    "room_name" : "",
    "passphrase" : "fast"
})


class bingosyncClient():
    """
    Opens a bingosync session with the correct csrf cookies!! Very exciting.
    Implements api methods for bingosync as well probably.
    """
    roomId = None

    def __init__(self):
        self.bingosync = True
        self.session = requests.Session()
        #Using a session automatically persists cookies!
        #set user-agent header:
        self.session.headers.update({
            "User-Agent" : "Silksong.Bingogenerator/0.1",
            "Origin": "https://bingosync.com",
            "Host": "bingosync.com",
        })
        #Make a request to get them cookies
        r = self.session.get("https://bingosync.com/")

        self.csrfToken = self.session.cookies["csrftoken"]

    def newRoom(self, boardJSON, hideCard = True, lockout=False, roomName=None, passphrase="fast", seed = ""):
        """
        Opens a new room and sets the instance roomId.
        """ 
        formData = NEW_CARD_PAYLOAD.copy()
        #need to update the following
        formData.update({
            "hide_card" : 1 if hideCard else 0,
            "lockout_mode" : 2 if lockout else 1,
            "custom_json" : boardJSON,
            "passphrase" : passphrase,
            "seed": seed
        })
        if roomName is None:
            formData["room_name"] = random.choice(ROOM_NAMES)
        else:
            formData["room_name"] = roomName
        formData["csrfmiddlewaretoken"] = [self.csrfToken, self.csrfToken]
        if self.bingosync:
            baseUrl = "https://bingosync.com/"
        else:
            baseUrl = "https://caravan.kobold60.com/"
        response = self.session.post(baseUrl, data=formData, allow_redirects=False)
        if response.status_code == 302: #expected
            #save the room ID and then disconnect from it
            self.roomId = response.headers["location"].split("/")[2]
            self.session.get(f"{baseUrl}/room/{self.roomId}/disconnect")
            self.session.get(f"{baseUrl}")
        return formData["room_name"], self.roomId

    def updateCard(self, roomID, boardJSON, hideCard = True, lockout = False, roomName=None, passphrase="fast", seed = "", bingosync = True):
        """
        Updates a room's card with a new board.
        """
        formData = STANDARD_PAYLOAD.copy()
        #need to update the following
        formData.update({
            "room": roomID,
            "hide_card" : 1 if hideCard else 0,
            "lockout_mode" : 2 if lockout else 1,
            "custom_json" : boardJSON,
            "seed": seed
        })
        if self.bingosync:
            baseUrl = "https://bingosync.com/"
        else:
            baseUrl = "https://caravan.kobold60.com/"
        formData["csrfmiddlewaretoken"] = [self.csrfToken, self.csrfToken]
        response = self.session.post(f"{baseUrl}/api/new-card", data=formData)
        return response


    def close(self):
        """
        Closes the session.
        """
        self.session.close()

class caravanClient(bingosyncClient):
    def __init__(self):
        self.bingosync = False
        self.session = requests.Session()
        #Using a session automatically persists cookies!
        #set user-agent header:
        self.session.headers.update({
            "User-Agent" : "Silksong.Bingogenerator/0.1",
            "Origin": "https://caravan.kobold60.com/",
            "Host": "caravan.kobold60.com",
        })
        #Make a request to get them cookies
        r = self.session.get("https://caravan.kobold60.com/")

        self.csrfToken = self.session.cookies["csrftoken"]

class byngosinkClient(): #completely different format.
    def __init__(self) -> None:
        self.socketAddress = "wss://byngosink-ws.manicjamie.com:555/"
        #self.socketAddress = "ws://localhost:555/"
        self.baseURL = "https://byngosink.manicjamie.com/board.html?id="

    def newFixedRoom(self, boardList: list, gameType: str, roomName = None, gameName: str = "Silksong", players=0):
        """
        Opens a new room with fixed board and sets the instance roomId.
        """ 
        if roomName is None:
            roomName = random.choice(ROOM_NAMES)

        payload = {
            "verb":"OPEN_FIXED",
            "roomName": roomName,
            "game": gameName,
            "generator": "Fixed",
            "board": gameType,
            "goals": boardList
        }

        with connect(self.socketAddress) as socket:
            socket.send(json.dumps(payload))
            response = json.loads(socket.recv(10))
            roomId = response["roomId"]
            roomURL = self.baseURL+roomId

            if players > 0:
                #join bingyflea to make teams and then leave
                socket.send(json.dumps({"verb": "JOIN", "roomId": roomId, "username": "Bingyflea"}))
                r2 = json.loads(socket.recv(10))
                userId = r2["userId"]

                names, colors = (random.sample(TEAM_NAMES, k=players), random.sample(TEAM_COLORS, k=players))
                for i in range(players):
                    socket.send(json.dumps({"verb": "CREATE_TEAM",
                                            "roomId": roomId,
                                            "name": names[i],
                                            "colour": colors[i]}))
                    _ = socket.recv(10)
                    sleep(0.2)

                socket.send(json.dumps({"verb": "LEAVE_TEAM",
                                        "roomId": roomId}))
                _ = socket.recv(10) 
                sleep(0.2)
                socket.send(json.dumps({"verb": "EXIT",
                                        "userId": userId,
                                        "roomId": roomId}))
                _ = socket.recv(10)
                sleep(0.2)

        return (roomName, roomURL)


if __name__ == "__main__":
    c = byngosinkClient()
    board = ["Beast's Crest", "Vintage Nectar", "Cogwork Core Mask Shard", "Deep Docks Fleas [3]", "Blasted Steps Mask Shard", "Slab Mask Shard", "5 Red Tools", "3 Gather Quests", "Talk to Loam", "Crustnut", "Talk to Shakra in Bilewater", "High Halls Spool Fragment", "1 Crafting Kit", "Obtain 3 Beast Shards", "Meet Caravan at the Grand Gate [12]", "Obtain 5 Craftmetal", "Apostate Key", "Pimpillo & Voltvessels", "Skull Tyrant", "2 Wayfarer Quests", "Conductor's Melody", "Rosary Cannon", "Voltvyrm", "Buy From Grindle (No String)", "Moorwing", "Flintslate", "Witch Crest", "Sands of Karak Flea [1]", "2 Extra Masks", "Mt. Fay Mask Shard", "Defeat a Covetous Pilgrim", "Obtain 5 Memory Lockets", "Deep Docks Spool Fragments (2)", "Disgraced Chef Lugoli", "Pale Lake Craftmetal", "Talk to Styx & Huntress"]
    _, rId = c.newFixedRoom(board, gameType="Bingo6", players=5)
    print(rId)
