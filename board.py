import os, json, random
from network import ROOM_NAMES
from math import sqrt

#file paths and names
ASSETS_PATH = "assets"
COMPUTED_SUBDIR = "generated"
GOALS_FILENAME = "silksong-v6.json"
CAT_FILENAME = "categorized_v3.json"

#Lockout.live formatting
BOARD_TYPES = [
    'cloak', 'walljump', 'act2', 'dash', 'early', 'clawline', 
    'faydown', 'craft', 'hardsave', 'melody', 'flea', "key", 'tool', ]

#Ordered progression
orderedProg = ['early','dash','cloak','walljump', 'widow', 'act2', 'clawline','faydown']
maxWeightScale = 2.25
    
LL_LIMITS = {
            "board" : {
                "early" : 20,
                "dash"  : 20,
                "cloak" : 30,
                "walljump" : 25,
                "act2" : 30,
                "clawline" : 40,
                "faydown" : 50,
                "hardsave" : 20,
                "craft" : 40,
                "flea" : 15,
                "key" : 20,
                "tool" : 30,
                "melody" : 20
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

def getAllGoals(noTags=[], **kwargs):
    """
    Loads the file given in variables at the top of the script and returns the parts.
    Returns list of Goal dictionaries and list of Exclusive lists.
    """
    with open(os.path.join(ASSETS_PATH, CAT_FILENAME)) as f:
        catList = json.load(f)
    #can't modify list during iteration so keep track of removables here
    remGoals = []
    if 'noProg' not in kwargs or not kwargs['noProg']: #progression scaling
        presentTags = [tag for tag in orderedProg if tag not in noTags] #ordered tags that arent excluded
        linspace = [1 + x*(maxWeightScale-1)/(len(presentTags)-1) for x in range(len(presentTags))]
        def weightScale(progString, types):
            try:
                if "collection" in types:
                    return linspace[-1] #max weight for collection goals
                else:
                    return linspace[presentTags.index(progString)]
            except ValueError: #progression is being excluded anyway
                return 1
    else: 
        def weightScale(progString, types):
            return 1
    for g in catList["goals"]: #add weight=1 to all non-weighted goals for later
        if "weight" not in g.keys():
            g["weight"] = 1 * weightScale(g["progression"][0], g["types"])
        else:
            g["weight"] = g["weight"] * weightScale(g["progression"][0], g["types"])
        #check if we should exclude the goal based on options passed
        goalTags = g["types"] + g["progression"]
        for tag in goalTags:
            if tag in noTags:
                remGoals.append(g)
                break
    for g in remGoals:
        if g in catList["goals"]: #in case goal got added to remList twice; don't want to error out due to typo or w/e
            catList["goals"].remove(g)
    return catList["goals"], [u for u in catList["exclusions"]]

def findExclusions(goalName, exclusionDic, pattern=False):
    """
    Given a goal name and the main exclusion list, returns the exclusions relevant to this goal or an empty list if none.

    """
    exclus = []
    for exclusionSet in exclusionDic:
        if goalName in exclusionSet["unique"]:
            if not pattern:
                if "pattern" in exclusionSet.keys() and exclusionSet["pattern"]: #pattern-only exclusion
                    continue #skip this one
            if "limit" not in exclusionSet.keys() or exclusionSet["limit"] == 1: #no limit or limit reached
                exclus = exclus + exclusionSet["unique"]
            else:
                exclusionSet["limit"] = exclusionSet["limit"] - 1
    return exclus if exclus != [] else False
    

def removeGoalByName(goalList:list, toRemove):
    listCopy = goalList.copy()
    for goal in goalList:
        if goal["name"] == toRemove:
            listCopy.remove(goal) #can't change mutable types during iteration
    return listCopy

def board(allGoals:dict, exclusionDic, size=25, **kwargs):
    """
    Generates a list of 25 goals from the dict of goals pass as a dictionary. Goals will have a name and optionally exclusions.
    Returns a list of goal names.
    """
    goals = []
    lockout = kwargs["lockout"] if "lockout" in kwargs.keys() else False
    tagLimits = kwargs["tagLimits"].copy() if "tagLimits" in kwargs.keys() and kwargs["tagLimits"] is not None else None
    pattern = kwargs["pattern"] if "pattern" in kwargs.keys() else False
    progs = kwargs["keepProgression"] if "keepProgression" in kwargs.keys() else False

    if "priorGoals" in kwargs.keys(): #linked boards, apply exclusions now
        for goal in kwargs["priorGoals"]:
            exclusions = findExclusions(goal, exclusionDic)
            if exclusions: #exclusions is false if limit > 1 or no exclusions found
                for excludedGoal in exclusions:
                    allGoals = removeGoalByName(allGoals, excludedGoal)


    while len(goals) < size:
        if len(allGoals) == 0: #critical failure
            raise EOFError("Out of goals! Try again.")

        newGoal = random.choices(allGoals, weights=[g["weight"] for g in allGoals])[0] #list comprehension to extract weights

        #process board limits
        skip = False
        if tagLimits is not None:
            goalTags = newGoal["types"] + newGoal["progression"]
            for tag in goalTags:
                if tag in tagLimits.keys(): #tag has a limit
                    if tagLimits[tag] == 0: #limit has been reached
                        try:
                            allGoals.remove(newGoal)
                        except ValueError: #goal already gone
                            pass
                        skip = True #remove goal from list and redraw
        if skip:
            continue

        ### GOAL IS LOCKED IN AT THIS POINT. DO NOT REDRAW

        #process set exclusions
        exclusions = findExclusions(newGoal["name"], exclusionDic, pattern=pattern)
        if exclusions: #exclusions is false if no exclusions found
            for excludedGoal in exclusions:
                allGoals = removeGoalByName(allGoals, excludedGoal)

        #decrement tag limits
        if tagLimits is not None:
            for tag in goalTags:
                if tag in tagLimits.keys(): #tag has a limit
                    tagLimits[tag] = tagLimits[tag] - 1 #decrement tag limit

        #format ranges and append to list
        #
        if "range" in newGoal.keys(): #goal has a range
            if not lockout or "lockout-range" not in newGoal.keys(): #use base range
                goalName = newGoal["name"].replace("{{X}}", str(random.choice(newGoal["range"])))
            else: #use lockout range
                goalName = newGoal["name"].replace("{{X}}", str(random.choice(newGoal["lockout-range"])))
        else: #no range, ez
            goalName = newGoal["name"]
        if progs: #keep progression tag for sorting
            goals.append({"name": goalName, "progression": newGoal["progression"]})
        else:
            goals.append(goalName)

        #remove goal from list to not get chosen twice
        try:
            allGoals.remove(newGoal)
        except ValueError: #what
            pass

    random.shuffle(goals) #mix em all up when we're done
    return goals

def bingosyncBoard(noTags=[], **kwargs):
    """
    Generates a board and returns a bingosync formatted list.
    """
    if "tagLimits" in kwargs.keys():
        limits = kwargs["tagLimits"]
    else:
        limits = None

    if "silly" in kwargs.keys() and kwargs["silly"]:
        pass
    else: #exclude silly by default
        noTags.append("silly")

    if "noBlocking" in kwargs.keys() and kwargs["noBlocking"]:
        pattern = True
        noTags.append("blocking")
    else:
        pattern = False

    if "size" in kwargs.keys():
        boardList = board(*getAllGoals(noTags=noTags), size=int(kwargs["size"]), lockout=(not "lockout" in noTags), tagLimits=limits, pattern=pattern)
    else:
        boardList = board(*getAllGoals(noTags=noTags), lockout=(not "lockout" in noTags), tagLimits=limits, pattern=pattern)
    out = []
    for name in boardList:
        out.append({"name": name})
    return out

def lockoutBoard(noTags=[], size=49, **kwargs):
    """
    Generates a fixed board for lockout.live ascend mode. EXPERIMENTAL.
    """
    if "tagLimits" in kwargs.keys():
        limits = kwargs["tagLimits"]
    else:
        limits = None

    if "silly" in kwargs.keys() and kwargs["silly"]:
        pass
    else: #exclude silly by default
        noTags.append("silly")

    if "noBlocking" in kwargs.keys() and kwargs["noBlocking"]:
        pattern = True
        noTags.append("blocking")
    else:
        pattern = False

    boardList = board(*getAllGoals(noTags=noTags), size=int(size), 
                            lockout=(not "lockout" in noTags), tagLimits=limits, 
                            pattern=pattern, keepProgression=True) #list of {"name","progression"} dictionary

    boardList.sort(key=lambda goal: orderedProg.index(goal["progression"][0])) #sort by progression order

    #Now we need to setup the stupid lockout.live dictionary grr
    out = {
        "game" : random.choice(ROOM_NAMES),
        "version" : "0.1",
        "limits": LL_LIMITS
    }
    goalsList = []
    sliceSize = int(sqrt(size))
    for sliceStart in range(0,size,sliceSize):
        goalSlice = boardList[sliceStart:sliceStart+sliceSize].copy()
        random.shuffle(goalSlice)
        for i, goalDic in enumerate(goalSlice):
            newDic = {
                "goal" : goalDic["name"],
                "individual_limit": 1,
                "range" : [],
                "board_categories": [],
                "line_categories": [],
                "tooltip": "",
                "icons" : [],
                "preferred_grid_position": size-(sliceStart+i) #this is 1 for top-left
            }
            goalsList.append(newDic)
    for i in range(sliceSize): #lockout needs more goals than required for some reason
        newDic = {
            "goal" : f"this goal is fake{i}",
            "individual_limit": 1,
            "range" : [],
            "board_categories": [],
            "line_categories": [],
            "tooltip": "",
            "icons" : []
        }
        goalsList.append(newDic)
    out["objectives"] = goalsList
    return out


def linkedBoards(noTags, size=5, **kwargs):
    b1Tags, b2Tags = noTags
    #set up tag limits and such
    if "tagLimits" in kwargs.keys():
        limits = kwargs["tagLimits"]
    else:
        limits = None

    if "silly" in kwargs.keys() and kwargs["silly"]:
        pass
    else: #exclude silly by default
        b1Tags.append("silly")
        b2Tags.append("silly")

    #generating a first board
    board1List = board(*getAllGoals(noTags=b1Tags), lockout=(not "lockout" in noTags), tagLimits=limits, size=size)
    #generate a second board after applying exclusions based on already chosen boards
    board2List = board(*getAllGoals(noTags=b2Tags), lockout=(not "lockout" in noTags), tagLimits=limits, size=size, priorGoals=board1List)
    b1 = []
    b2 = []
    for name in board1List:
        b1.append({"name": name})
    for name in board2List:
        b2.append({"name": name})
    return b1, b2


def printTypes():
    """
    Prints all types and progression flags currently in use.
    """
    with open(os.path.join(ASSETS_PATH, CAT_FILENAME)) as f:
        catList = json.load(f)
    types = []
    prog = []
    for g in catList:
        for t in g["types"]:
            if t not in types:
                types.append(t)
        for p in g["progression"]:
            if p not in prog:
                prog.append(p)
    print(f"Types: {types}\n\nProg:{prog}")

def lockoutFormat():
    """
    Outputs a list of goals formatted for Lockout.Live.
    """
    mainList, _ = getAllGoals() #lockout.live doesn't acknowledge exclusions
    out = {
        "game" : "Hollow Knight: Silksong",
        "limits" : LL_LIMITS
    }
    goalsList = []
    for goalDic in mainList:
        try:
            r = goalDic["range"]
        except KeyError:
            r = []
        totTypes = goalDic["progression"] + goalDic["types"]
        bTypes = []
        lTypes = []
        for t in totTypes:
            if t == "widow":    #the difference between widow and walljump progression was causing balance issues
                t = "walljump"  #get outta here
            if t in BOARD_TYPES:
                bTypes.append(t)
            else:
                lTypes.append(t)
        newDic = {
            "goal" : goalDic["name"],
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

def bingosyncFormat():
    """
    Outputs a list of goals formatted for bingosync.
    """
    with open(os.path.join(ASSETS_PATH, CAT_FILENAME)) as f:
        catList = json.load(f)
    goalsList = []
    for goalDic in catList["goals"]:
        if "range" in goalDic.keys():
            for x in goalDic["range"]:
                goalsList.append({"name": goalDic["name"].replace("{{X}}", str(x))})
        else:
            goalsList.append({"name": goalDic["name"]})
    return goalsList

def readableFormat():
    """
    Outputs a list of goals in nice, readable formatting.
    """
    with open(os.path.join(ASSETS_PATH, CAT_FILENAME)) as f:
        catList = json.load(f)
    linesList = []
    for goalDic in catList["goals"]:
        if "range" in goalDic.keys():
            for x in goalDic["range"]:
                boldName = f"**{goalDic['name'].replace('{{X}}', str(x))}**"
                progression = goalDic["progression"]
                types = goalDic["types"]
                linesList.append(f"{boldName} | Progression level(s): {progression} | Other tags: {types}\n\n")
        else:
            boldName=f"**{goalDic['name']}**"
            progression = goalDic["progression"]
            types = goalDic["types"]
            linesList.append(f"{boldName} | Progression level(s): {progression} | Other tags: {types}\n\n")
    return linesList

if __name__ == "__main__":
    ####dump the current format for lockout.live
    with open(os.path.join(ASSETS_PATH,COMPUTED_SUBDIR,"silksong_lockoutlive.json"), "w") as f:
        json.dump(lockoutFormat(), f, indent=4)

    ####dump the current format for bingosync
    with open(os.path.join(ASSETS_PATH,COMPUTED_SUBDIR,"silksong_bingosync.json"), "w") as f:
        json.dump(bingosyncFormat(), f, indent=4)
    #print("File dumped.")

    ####Generate sophont-readable list of goals
    with open(os.path.join(ASSETS_PATH,COMPUTED_SUBDIR,"silksong_readable.md"), "w") as f:
        f.writelines(readableFormat())

    ####Test bingosync format
    #print(json.dumps(bingosyncFormat()))

    ####Test lockout format
    #print(json.dumps(lockoutFormat()))

    ####Test board generation
    thisBoard = bingosyncBoard(noTags=["lockout"])
    print(json.dumps(thisBoard))
