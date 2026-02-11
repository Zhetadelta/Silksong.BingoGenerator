# BINGYFLEA
A discord bot and associated codebase used to support [bingosync](https://bingosync.com/) and [lockout.live](https://lockout.live/) silksong play.

The up-to-date lockout.live and bingosync files live in assets/generated/.

An easy-to-read list of goals is [here!](https://github.com/Zhetadelta/Silksong.BingoGenerator/blob/main/assets/generated/silksong_readable.md)

## Commands
Add the bot to your user account or server via [this link!](https://discord.com/oauth2/authorize?client_id=1429591758248874105)

- newboard

Very simple command that spits out a Bingosync-formatted list. Set the game to Custom (Advanced) and the variant to "Fixed Board" to use. Supports lockout-exclusive goals as well as progression-limiting for shorter games.

- newroom or newcaravan

Bingyflea will generate a board AND handle the room creation for you. Has the same options as newboard!

The password for these rooms is always "fast".

- advancedboard

Command that allows exclusion of arbitrary tags (types and/or progression) from goals. Ex: `flea, key, faydown` would generate a board without any flea goals, no simple key requirements, and no faydown cloak requirements.

## Goal contribution
The current list of goals is "categorized_v3.json" in the Assets folder. To add a goal or exclusion, add any necessary lines in the relevant sections in that file.

### Format specs

A goal must be a dictionary as follows:

- `"name" : string` The name of the goal. This will appear on the bingy square.

- `"types" : [string]` Applicable tags for the goal. Not enforced via code but goals should probably have at least one type.

#### Possible types:

"craft", "flea", "key", "tool", "melody", "quest", "locket", "upgrade", "fight", "npc", "location", "collection", "relic", "hardsave", "blocking", "silly"

#### Opt-in types

The following types are excluded by default and must be opted into manually: Silly

- `"progression" : [string]` Progression stage when the goal is expected to be achievable. Goals must have at least one, but some (such as ranges) can have multiple.

#### Progression strings:

"early", "dash", "cloak", "walljump", "act2", "clawline", "faydown"

- `"weight" : 1` **(Optional)** If not given, a weight is assumed to be 1. A weight of 2 means a goal is twice as likely to be picked. This can be a decimal if you really want that kind of granularity. 

- `"range" : [int]` **(Optional)** A goal with `"{{X}}"` in the name will have that string replaced with a number in the given range.

- `"lockout-range" : [int]` **(Optional)** For lockout goals, a seperate range can be defined for the lockout version of that goal. Use "lockout-range" **in addition to the normal range.**

Example:

"{{X}} Memory Lockets" with a `"range" : [1,2,5]` can be any of the following goals:

- 1 Memory Lockets
- 2 Memory Lockets
- 5 Memory Lockets

These are automatically exclusive, and the group can be added to an exclusive pool using the string with {{X}} in it.

#### Exclusions
An exclusion must be a dictionary as follows:

- `"unique" : []` A list of the goals in this exclusion group.

- `"limit" : 1` **(Optional)** A maximum number of goals in this group to appear on any given board. If not given, assumed to be 1 (only one of these goals can appear).

- `"pattern" : true` **(Optional)** Add this field to an exclusion to make it only apply to pattern-preset boards.