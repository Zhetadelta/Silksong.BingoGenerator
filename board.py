import os, json, random

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
maxWeightScale = 2
    
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
        def weightScale(progString):
            try:
                return linspace[presentTags.index(progString)]
            except ValueError: #progression is being excluded anyway
                return 1
    else: 
        def weightScale(progString):
            return 1
    for g in catList["goals"]: #add weight=1 to all non-weighted goals for later
        if "weight" not in g.keys():
            g["weight"] = 1 * weightScale(g["progression"][0])
        else:
            g["weight"] = g["weight"] * weightScale(g["progression"][0])
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

def findExclusions(goalName, exclusionDic):
    """
    Given a goal name and the main exclusion list, returns the exclusions relevant to this goal or an empty list if none.

    """
    exclus = []
    for exclusionSet in exclusionDic:
        if goalName in exclusionSet["unique"]:
            if "limit" not in exclusionSet.keys() or exclusionSet["limit"] == 1: #no limit or limit reached
                exclus = exclus + exclusionSet["unique"]
            else:
                exclusionSet["limit"] = exclusionSet["limit"] - 1
                return False
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
    tagLimits = kwargs["tagLimits"] if "tagLimits" in kwargs.keys() else None

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
        exclusions = findExclusions(newGoal["name"], exclusionDic)
        if exclusions: #exclusions is false if limit > 1 or no exclusions found
            for excludedGoal in exclusions:
                allGoals = removeGoalByName(allGoals, excludedGoal)

        #decrement tag limits
        if tagLimits is not None:
            for tag in goalTags:
                if tag in tagLimits.keys(): #tag has a limit
                    tagLimits[tag] = tagLimits[tag] - 1 #decrement tag limit

        #format ranges and append to list
        if "range" in newGoal.keys(): #goal has a range
            if not lockout or "lockout-range" not in newGoal.keys(): #use base range
                goals.append(newGoal["name"].replace("{{X}}", str(random.choice(newGoal["range"]))))
            else: #use lockout range
                goals.append(newGoal["name"].replace("{{X}}", str(random.choice(newGoal["lockout-range"]))))
        else: #no range, ez
            goals.append(newGoal["name"])

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

    if "size" in kwargs.keys():
        boardList = board(*getAllGoals(noTags=noTags), size=int(kwargs["size"]), lockout=(not "lockout" in noTags), tagLimits=limits)
    else:
        boardList = board(*getAllGoals(noTags=noTags), lockout=(not "lockout" in noTags), tagLimits=limits)
    out = []
    for name in boardList:
        out.append({"name": name})
    return out

def linkedBoards(noTags, **kwargs):
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
    board1List = board(*getAllGoals(noTags=b1Tags), lockout=(not "lockout" in noTags), tagLimits=limits)
    #generate a second board after applying exclusions based on already chosen boards
    board2List = board(*getAllGoals(noTags=b2Tags), lockout=(not "lockout" in noTags), tagLimits=limits, priorGoals=board1List)
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
            if t == "widow":    #the difference between widow and walljump progression was small enough that categorizing things was hard
                t = "walljump"  #it was also causing balance issues. get outta here
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
