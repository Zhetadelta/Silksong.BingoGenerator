from board import CaravanGenerator, GameName, GameType, orderedProgs
from os import path, curdir
import matplotlib.pyplot as plt

ITERS = 2000
FIG_PATH = path.join(curdir, "analysis")

def plotit(counts: dict, figurename: str):
    fig, ax = plt.subplots()
    pcts = percents(counts)
    xlables = [f"{i}-{str(pcts[i])}\\%" for i in counts.keys()]
    ax.bar(xlables, counts.values(), color="tab:purple")
    for tick in ax.xaxis.get_major_ticks()[1::3]:
        tick.set_pad(15)
    for tick in ax.xaxis.get_major_ticks()[2::3]:
        tick.set_pad(25)
    ax.set_title(figurename)
    fig.tight_layout()
    plt.savefig(f"{path.join(FIG_PATH, figurename)}.png")

def generate(kwargs: dict):
    counts = {p:0 for p in orderedProgs[GameName.Silksong]}
    for i in range(ITERS):
        try:
            g = CaravanGenerator("categorized_v3.json", 6, **kwargs)
            progs = [g.getGoalProgression(n["name"]) for n in g.export()]
            for prog in progs:
                counts[prog] += 1
        except:
            pass
    return counts

def percents(counts: dict):
    total = sum(counts.values())
    return {p: round(counts[p]*100/total,1) for p in counts.keys()}

fdl = generate({"noTags": ["faydown", "act3", "silksoar"], "lockout": True})
plotit(fdl, "clawline-lockout prog forcing")

fdlnf = generate({"noTags": ["faydown","act3", "silksoar"], "lockout": True, "gameType":GameType.NoForcing})
plotit(fdlnf, "clawline-lockout no forcing")

fdnf = generate({"noTags": ["faydown","act3", "silksoar"], "gameType":GameType.NoForcing})
plotit(fdnf, "clawline no forcing")

fdf  = generate({"noTags": ["faydown","act3", "silksoar"]})
plotit(fdf, "clawline prog forcing")

g = CaravanGenerator("categorized_v3.json", 6, noTags=["faydown", "act3", "silksoar"])

counts = {p:0 for p in orderedProgs[GameName.Silksong]}
for goal in g.goalSet:
    counts[goal["progression"][0]] += 1
print(percents(counts))