"""
The House in the Woods
Text adventure game
"""

import json
import re
from collections import namedtuple
import textwrap
import readline  # input() remembers previous entries
import sys
import os


# constants

EXPLET = r"\s*(?:\b\s\b|\baz?\b|\bés\b|\begy\b|\bplusz\b)\s*"
WRAP_WIDTH = 80
HISTORY_BUFFER = 20
CHANGE_PROMPT = 5  # change to simple prompt after 5 steps
MSG_OK = "Rendben"  # must be the same as "ok" in commands.json, see in increase_step()

RE_EXPLET = re.compile(EXPLET, flags=re.IGNORECASE)


# decorator functions

def linewrap(func):
    """wrap lines"""
    def linewrapper(adv):
        return textwrap.fill(func(adv), width=WRAP_WIDTH)
    return linewrapper

def show(func):
    """show description"""
    def shower(adv):
        print(func(adv))
    return shower

def increase_step(func):
    """increase step count"""
    def stepper(adv):
        msg = func(adv)
        if msg.startswith(MSG_OK):  # only successful actions get counted
            adv.player["step"] += 1
        return msg
    return stepper


# main executing function

def main():
    # adventure-elements in a named tuple, access like adv.rooms or adv.player
    adv = setup(*get_jsons())
    if not all(adv):
        sys.exit("Something went wrong, unable to start the game.")

    # create references to handler functions
    adv.player["commands"] = {command: eval(command) for command in adv.commands}

    # init readline history
    readline.set_history_length(HISTORY_BUFFER)
    readline.clear_history()
    readline.set_auto_history(True)

    # main game loop
    while check(adv.player["status"], "playing", "alive", "nowinner"):
        room_description(adv)
        adv.rooms[adv.player["location"]]["status"].add("visited")
        player_input(adv)


# helper functions

@show
@linewrap
def room_description(adv):
    """provide room description"""
    location = adv.rooms[adv.player["location"]]
    if "visible" in location["status"]:
        if "verbose" in adv.player["status"]:
            return location["long"]
        if "short" in adv.player["status"] or "visited" in location["status"]:
            return adv.player["location"].capitalize() + "."
        return location["long"]
    return adv.messages["toodark"]

def player_input(adv):
    """read player's next command"""
    prompt = ">" if adv.player["step"] > CHANGE_PROMPT else adv.messages["prompt"]
    adv.player["command"] = input("{} ".format(prompt)).lower()
    execute(adv)

def execute(adv):
    """execute player's command"""
    adv.player["command"] = list(filter(None, RE_EXPLET.split(adv.player["command"])))
    if check(adv.commands["again"], *adv.player["command"], logic=any):
        again(adv)  # again is very special, must be handled before anything else
        execute(adv)  # execute() is separated from player_input() because of this recursive call
    else:
        react(adv)

@show
@linewrap
def react(adv):
    exe = adv.player["commands"]
    # first, look up for a verb
    for com, words in adv.commands.items():
        if check(words, *adv.player["command"], logic=any):
            return exe[com](adv)
    # second, look up for a movement direction
    for words in adv.direction.values():
        if check(words, *adv.player["command"], logic=any):
            return exe["move"](adv)
    # at last, the parser doesn't understand
    return adv.messages["???"]

def setup(*elements):
    """elements correspond to .json filenames"""
    return namedtuple("adv", " ".join(elements))._make(map(load, elements))

def check(collection, *values, logic=all):
    """check if certain values are present in collection"""
    return logic(value in collection for value in values)

def are_you_sure():
    """answer yes or no"""
    return input("Biztos vagy benne? ").lower().startswith("i")

def direction(adv):
    """identify direction in command"""
    for drc, words in adv.direction.items():
        if check(words, *adv.player["command"], logic=any):
            return drc
    return None


# json data persistence

def get_jsons():
    """get all .json filenames from current directory"""
    with os.scandir() as it:
        return [entry.name.split(".")[0] for entry in it if entry.name.endswith(".json")]

def load(element, ext="json"):
    """adventure elements stored in dictionary"""
    try:
        with open(element + "." + ext, "r") as fo:
            return json.load(fo, object_hook=list2set)
    except (IOError, json.JSONDecodeError):
        return None

def dump(content, filename):
    """write game data in json format"""
    try:
        with open(filename, "w") as fp:
            json.dump(content, fp, ensure_ascii=False, indent=4)
        return True
    except (IOError, json.JSONDecodeError):
        return False

def list2set(element):
    """lists should become sets"""
    for key in element:
        if type(element[key]) is list:
            element[key] = set(element[key])
    return element

def savefile(adv):
    """create or read savefile-name"""
    sf = "default"
    for com in adv.player["command"]:
        if com.endswith(".save"):
            sf = com.split(".")[0]
            break
    return sf


# handler functions

def leave(adv):
    """player exits the game"""
    if are_you_sure():
        adv.player["status"].remove("playing")
        return adv.messages["bye"]
    return adv.messages["ok"]

@increase_step
def move(adv):
    """player tries to move in a given direction"""
    drc = direction(adv)
    destination = adv.rooms[adv.player["location"]]["exits"].get(drc)
    if drc and destination:
        adv.player["location"] = destination
        return adv.messages["ok"]
    return adv.messages["cantgo"]

def save(adv):
    """save game to .json file - provide filename ending .save"""
    tosave = {"player": {"status": list(adv.player["status"]),
                         "location": adv.player["location"],
                         "inventory": list(adv.player["inventory"]),
                         "step": adv.player["step"]}}
    tosave.update({"rooms": {name: list(adv.rooms[name]["status"]) for name in adv.rooms}})
    if dump(tosave, savefile(adv) + ".save"):
        return adv.messages["ok"]
    return adv.messages["!!!"]

def restore(adv):
    """restore saved game - look for provided filename ending .save"""
    rst = load(savefile(adv), ext="save")
    if rst:
        # restore player
        adv.player["status"].clear()
        adv.player["inventory"].clear()
        adv.player["status"].update(rst["player"]["status"])
        adv.player["inventory"].update(rst["player"]["inventory"])
        adv.player["location"] = rst["player"]["location"]
        adv.player["step"] = rst["player"]["step"]
        # restore room's status
        for room, status in rst["rooms"].items():
            adv.rooms[room]["status"].clear()
            adv.rooms[room]["status"].update(status)
        return adv.messages["ok"]
    return adv.messages["!!!"]

def step(adv):
    """show player's step count"""
    return adv.messages["step"].format(adv.player["step"])

@show
@linewrap
def again(adv):
    """repeat last command - handled in execute(), just for placeholding"""
    idx = readline.get_current_history_length()
    if idx > 1:
        readline.remove_history_item(idx - 1)
        adv.player["command"] = readline.get_history_item(idx - 1)
    else:
        adv.player["command"] = ""
    return adv.messages["repeat"] + adv.player["command"]


if __name__ == "__main__":
    main()
