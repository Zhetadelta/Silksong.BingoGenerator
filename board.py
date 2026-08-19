import os, json, random
from network import ROOM_NAMES
from enum import Enum
from math import sqrt

#file paths and names
ASSETS_PATH = "assets"
COMPUTED_SUBDIR = "generated"
GOALS_FILENAME = "silksong-v6.json"
CAT_FILENAME = "categorized_v3.json"

#Lockout.live formatting
BOARD_TYPES = [
    'cloak', 'walljump', 'act2', 'dash', 'early', 'clawline', 
    'faydown', 'craft', 'hardsave', 'melody', 'flea', "key", 'tool', 'expensive', 'act3', 'silksoar']

LL_PROGRESSION = {
    "early" : "e",
    "dash" : "e",
    "cloak" : "e",
    "walljump" : "m",
    "widow" : "m",
    "act2" : "l",
    "clawline" : "l",
    "faydown" : "n"
}

LL_EXCLUDE = ["act3", "silksoar", "silly", "missable", "itemsync"]

LL_LIMITS = {
            "board" : {
                "early" : 20,
                "dash"  : 20,
                "cloak" : 30,
                "walljump" : 30,
                "act2" : 30,
                "clawline" : 40,
                "faydown" : 50,
                "hardsave" : 20,
                "craft" : 40,
                "flea" : 25,
                "key" : 20,
                "tool" : 30,
                "melody" : 20,
                "expensive" : 10
            },
            "line" : {
                "quest" : 60,
                "locket" : 60,
                "upgrade" : 80,
                "fight" : 60,
                "npc" : 40,
                "location" : 60,
                "collection" : 60,
                "relic" : 60
            }
        }

#Default excluded tags
DEF_NOTAGS = ["silly", "itemsync"]

GameType = Enum('GameType', [('Bingo',1),('GTTOS',2),('Rando',3),('Pattern',4)])
FOW_TYPES = [GameType.GTTOS]

GameName = Enum('GameName', [('Silksong',1),('Mio',2)])
orderedProgs = {
    GameName.Silksong : ['early','dash','cloak','walljump', 'widow', 'act2', 'clawline','faydown', 'act3', 'silksoar'],
    GameName.Mio : ["early","hairpin","1skill","vaults"]
}

class Generator():
    """Base class for generators."""
    def __init__(self, goalFilename, size, noTags = [], tagLimits = None, 
                 gameName = GameName.Silksong, gameType = GameType.Bingo):
        self.size = size
        self.noTags = noTags
        self.noTags += DEF_NOTAGS
        self.tagLimits = tagLimits
        if gameType == GameType.Pattern:
            self.noTags.append("blocking")
        self.gameName = gameName
        self.gameType = gameType
        with open(os.path.join(ASSETS_PATH, goalFilename)) as f: 
            goalsDic = json.load(f)
        self.goalSet, self.exclusionSet = self.getAllGoals(goalsDic)
        self.baseSet = self.goalSet.copy()
        
    def totalCount(self):
        return self.size ** 2

    def forceIndices(self):
        """
        Pick locations for goals which force max progression.
        Returns a list of indices.
        """
        mSize = self.size-1
        #first pick two (zero indexed) squares on the diagonals. row, col
        i = random.randrange(self.size)
        j = random.randrange(self.size)
        while j == i or abs(j-mSize) == i:
            j = random.randrange(self.size) #enforce different rows and columns
        rows = [k for k in range(self.size) if k not in [i, j]]
        rows.append(i)
        rows.append(j)
        cols = [l for l in range(self.size) if l not in [i, abs(j-mSize)]]
        random.shuffle(cols)
        cols.append(i)
        cols.append(abs(j-mSize))
        locations = zip(rows, cols)
        return sorted([c+(r*self.size) for r,c in locations])

    def linkBoards(self, goalList):
        """Apply exclusions from a previously generated list of (bingosync formatted) goal names."""
        for goal in goalList:
            exclusions = self.findExclusions(goal["name"])
            if exclusions: #exclusions is false if limit > 1 or no exclusions found
                for excludedGoal in exclusions:
                    self.removeGoalByName(excludedGoal)

    def getAllGoals(self, goalsDic):
        """
        Splits the dictionary passed into Goals and Exclusions and returns the parts. Filters based on the Generator's attributes.
        Returns list of Goal dictionaries and list of Exclusive lists.
        """
        #can't modify list during iteration so keep track of removables here
        remGoals = []

        for g in goalsDic["goals"]: #add weight=1 to all non-weighted goals for later
            if "weight" not in g.keys():
                g["weight"] = 1
            if self.gameType == GameType.Rando: #remove progression field since it doesn't matter
                goalTags = g["types"]
            else:
                #check if we should exclude the goal based on options passed
                goalTags = g["types"] + g["progression"]
            for tag in goalTags:
                if tag in self.noTags:
                    remGoals.append(g)
                    break
        for g in remGoals:
            if g in goalsDic["goals"]: #in case goal got added to remList twice; don't want to error out due to typo or w/e
                goalsDic["goals"].remove(g)
        return goalsDic["goals"], [u for u in goalsDic["exclusions"]]

    def findExclusions(self, goalName):
        """
        Given a goal name, returns the exclusions relevant to this goal or False if none.
        """
        exclus = []
        for exclusionGroup in self.exclusionSet:
            if goalName in exclusionGroup["unique"]:
                if self.gameType is not GameType.Pattern:
                    if "pattern" in exclusionGroup.keys() and exclusionGroup["pattern"]: #pattern-only exclusion
                        continue #skip this one
                if "limit" not in exclusionGroup.keys() or exclusionGroup["limit"] == 1: #no limit or limit reached
                    exclus = exclus + exclusionGroup["unique"]
                else:
                    exclusionGroup["limit"] = exclusionGroup["limit"] - 1
        return exclus if exclus != [] else False

    def removeGoalByName(self, toRemove):
        listCopy = self.goalSet.copy()
        for goal in self.goalSet:
            if goal["name"] == toRemove:
                listCopy.remove(goal) #can't change mutable types during iteration
                break
        self.goalSet = listCopy

    def getGoalProgression(self, goalName):
        """Get progression level of a goal from its name."""
        for goal in self.baseSet:
            if goal["name"] == goalName or ("fow" in goal.keys() and goal["fow"] == goalName):
                return goal["progression"][0]

    def board(self):
        """
        Generates a list of goals from the Generator's goalSet. Goals will have a name and optionally exclusions.
        Returns a list of goal names. Modifies the Generator's goalSet.
        """
        goals = []
        goalsNeeded = self.totalCount()
        

        orderedProg = orderedProgs[self.gameName]
        indices = self.forceIndices()
        if self.gameType != GameType.Rando:
            forceCount = len(indices)
        else:
            forceCount = 0
        forcedGoals = []
        maxProg = "early"
        for prog in orderedProg:
            if prog not in self.noTags:
                maxProg = prog
        goalsNeeded -= forceCount

        while goalsNeeded > 0:
            if len(self.goalSet) == 0: #critical failure
                raise EOFError("Out of goals! Try again.")

            newGoal = random.choices(self.goalSet, weights=[g["weight"] for g in self.goalSet])[0]
            goalTags = newGoal["types"] + newGoal["progression"]

            #process generator limits and forcing requirements
            skip = False

            if self.tagLimits is not None: #tag limit handling
                for tag in goalTags:
                    if tag in self.tagLimits.keys(): #tag has a limit
                        if self.tagLimits[tag] == 0: #limit has been reached
                            self.removeGoalByName(newGoal["name"])
                            skip = True #remove goal from list and redraw

            if goalsNeeded == 1 and len(forcedGoals) < forceCount and newGoal["progression"][0] != maxProg: 
                #need more max prog goals; unlikely to hit this code path but just in case.
                skip = True
            if skip:
                continue

            ### GOAL IS LOCKED IN AT THIS POINT. DO NOT REDRAW

            if self.gameType in FOW_TYPES and "fow" in newGoal.keys():
                goalName = newGoal["fow"]
            elif self.gameType == GameType.Rando and "rando" in newGoal.keys():
                goalName = random.choice([newGoal["name"], newGoal["rando"]])
            else:
                goalName = newGoal["name"]

            #put it in the right bin
            if len(forcedGoals) < forceCount and newGoal["progression"][0] == maxProg:
                forcedGoals.append(goalName)
            else:
                goals.append(goalName)
                goalsNeeded -= 1

            #process set exclusions
            exclusions = self.findExclusions(newGoal["name"])
            if exclusions: #exclusions is false if no exclusions found
                for excludedGoal in exclusions:
                    self.removeGoalByName(excludedGoal)

            #decrement tag limits
            if self.tagLimits is not None:
                for tag in goalTags:
                    if tag in self.tagLimits.keys(): #tag has a limit
                        self.tagLimits[tag] = self.tagLimits[tag] - 1 #decrement tag limit

            #remove goal from list to not get chosen twice
            try:
                self.removeGoalByName(newGoal["name"])
            except ValueError: #what
                pass

        if self.gameType == GameType.GTTOS: #otherside formatting
            goals += forcedGoals #combine them
            goals.sort(key=lambda goal: orderedProg.index(self.getGoalProgression(goal))) #sort by progression order

            arrangedBoard = ["placeholder"] * self.totalCount() #r1c1 is 0, r3c7 is 26, r10c10 is 99
            for setIndex in range(self.size):
                currentSet = goals[(setIndex*self.size) : (setIndex*self.size)+self.size]
                order = random.sample(range(self.size), k=self.size) 
                for i, goal in enumerate(currentSet):
                    arrangedBoard[(order[i]*self.size)+setIndex] = goal
            assert "placeholder" not in arrangedBoard
            return arrangedBoard

        else: #default setting
            random.shuffle(goals) #mix em all up when we're done

            for i, index in enumerate(indices):
                goals.insert(index, forcedGoals[i])
            return goals

class ByngosinkGenerator(Generator):
    """Formats a generated board for Byngosink upload."""
    def export(self):
        return self.board()

class CaravanGenerator(Generator):
    """Formats a generated board for Caravan/Bingosync upload."""
    def export(self):
        return [{"name" : g} for g in self.board()]

class GeneratorFormatter(Generator):
    """Class with functions to export files. Don't use to generate boards."""
    def __init__(self, goalFilename):
        super().__init__(goalFilename, 5, noTags = [], tagLimits = [], gameType=GameType.Bingo)

    def board(self):
        raise NotImplementedError

    def bingosyncFormat(self):
        """
        Outputs a list of goals formatted for bingosync.
        """
        goalsList = []
        for goalDic in self.goalSet:
            if "range" in goalDic.keys():
                for x in goalDic["range"]:
                    goalsList.append({"name": goalDic["name"].replace("{{X}}", str(x))})
            else:
                goalsList.append({"name": goalDic["name"]})
        return goalsList

    def readableFormat(self):
        """
        Outputs a list of goals in nice, readable formatting.
        """
        linesList = []
        for goalDic in self.goalSet:
            if "range" in goalDic.keys():
                for x in goalDic["range"]:
                    boldName = f"**{goalDic['name'].replace('{{X}}', str(x))}**"
                    progression = goalDic["progression"]
                    types = goalDic["types"]
                    linesList.append(f"{boldName} | Progression level: {progression} | Other tags: {types}\n\n")
            else:
                boldName=f"**{goalDic['name']}**"
                progression = goalDic["progression"]
                types = goalDic["types"]
                linesList.append(f"{boldName} | Progression level: {progression} | Other tags: {types}\n\n")
        return linesList

    def lockoutFormat(self):
        """
        Outputs a list of goals formatted for Lockout.Live.
        """
        out = {
            "game_name" : "Hollow Knight: Silksong",
            "schema_version" : 3,
            "schema_mode" : "strict",
            "set_name" : "Default Silksong Set",
            "tag_names" : [],
            "limits" : LL_LIMITS
        }
        goalsList = []
        for goalDic in self.goalSet:
            try:
                r = goalDic["range"]
            except KeyError:
                r = []
            totTypes = goalDic["progression"] + goalDic["types"]

            skip = False
            for t in totTypes: #yeah we iterate over this twice, whatever
                if t in LL_EXCLUDE: 
                    skip = True
                    break
            if skip:
                continue #if goal should be excluded, exclude it

            bTypes = []
            lTypes = []
            for t in totTypes:
                if t == "widow":    #the difference between widow and walljump progression was causing balance issues
                    t = "walljump"  #get outta here

                if t not in out["limits"]["board"].keys() and t not in out["limits"]["line"].keys():
                    out["limits"]["line"][t] = 100
                if t in BOARD_TYPES:
                    bTypes.append(t)
                else:
                    lTypes.append(t)

            if "fow" in goalDic.keys():
                goalName = goalDic["fow"]
            else:
                goalName = goalDic["name"]

            newDic = {
                "goal" : goalName,
                "progression" : [LL_PROGRESSION[goalDic["progression"][0]]],
                "range": r,
                "individual_limit": 1,
                "board_categories": bTypes,
                "line_categories" : lTypes,
                "tooltip": "",
                "icons" : [],
            }
            goalsList.append(newDic)
        out["objectives"] = goalsList
        return out

class DraftoutGenerator(Generator):
    def __init__(self, noTags, size, goalsetPath=CAT_FILENAME, **kwargs):
        super.__init__(goalsetPath,size,noTags)
        self.goals = []
        self.goalsRemaining = size**2
        self.presentProgs = [tag for tag in orderedProgs[GameName.Silksong] if tag not in noTags] #ordered tags that arent excluded
        
    def showGoals(self, count=3):
        """Present 3 goals."""
        selectedProg = random.choice(self.presentProgs)
        while len([g for g in self.goalSet if g["progression"][0] == selectedProg]) < 3:
            self.presentProgs.remove(selectedProg)
            selectedProg = random.choice(self.presentProgs)
        out = []
        while len(out) < count:
            newGoal = random.choices(self.goalSet, weights=[g["weight"] for g in self.goalSet])[0] #list comprehension to extract weights
            while newGoal["progression"][0] != selectedProg or newGoal in out:
                newGoal = random.choices(self.goalSet, weights=[g["weight"] for g in self.goalSet])[0]
            out.append(newGoal)
        return out
    
    def addGoal(self, goal):
        """Adds goal to list and returns number of goals remaining."""
        self.goals.append(goal)
        self.goalsRemaining -= 1
        exclusions = self.findExclusions(goal["name"])
        if exclusions: #exclusions is false if no exclusions found
            for excludedGoal in exclusions:
                self.goalSet = self.removeGoalByName(excludedGoal)
        self.goalSet = self.removeGoalByName(goal["name"])
        return self.goalsRemaining
    
    def getList(self):
        return self.goals

if __name__ == "__main__":
    ####dump the current format for lockout.live
    with open(os.path.join(ASSETS_PATH,COMPUTED_SUBDIR,"silksong_lockoutlive.json"), "w") as f:
        json.dump(GeneratorFormatter("categorized_v3.json").lockoutFormat(), f, indent=4)

    ####dump the current format for bingosync
    with open(os.path.join(ASSETS_PATH,COMPUTED_SUBDIR,"silksong_bingosync.json"), "w") as f:
        json.dump(GeneratorFormatter("categorized_v3.json").bingosyncFormat(), f, indent=4)
    #print("File dumped.")

    ####Generate sophont-readable list of goals
    with open(os.path.join(ASSETS_PATH,COMPUTED_SUBDIR,"silksong_readable.md"), "w") as f:
        f.writelines(GeneratorFormatter("categorized_v3.json").readableFormat())

    with open(os.path.join(ASSETS_PATH,COMPUTED_SUBDIR,"mio_readable.md"), "w") as f:
        f.writelines(GeneratorFormatter("mio.json").readableFormat())

    with open(os.path.join(ASSETS_PATH,COMPUTED_SUBDIR,"silksong_rando_readable.md"), "w") as f:
        f.writelines(GeneratorFormatter("silksong_rando.json").readableFormat())

    print(ByngosinkGenerator("categorized_v3.json", 5, noTags=["faydown", "act3", "silksoar"], gameType=GameType.GTTOS).export())
    print(CaravanGenerator("mio.json",5,gameName=GameName.Mio).export())