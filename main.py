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


# decorator functions

def linewrap(func):
    """wrap lines"""
    def linewrapper(*args):
        return textwrap.fill(func(*args), width=80)
    return linewrapper

def show(func):
    """show description on stdout"""
    def shower(*args):
        print(func(*args))
    return shower


# main executing function

def main():
    # adventure-elements in a named tuple, access like adv.rooms or adv.player
    adv = setup(*get_jsons())
    adv.player["commands"] = create_handlers(adv.commands)

    if not all(adv):
        print("Something went wrong, unable to start the game.", file=sys.stderr)
        sys.exit()

    # main game loop
    while check(adv.player["status"], "playing", "alive", "nowinner"):
        room_description(adv)
        adv.rooms[adv.player["location"]]["status"].add("visited")
        parse(player_input(adv))
        adv.player["steps"] += 1


# helper functions

@show
@linewrap
def parse(adv):
    """parser for player's commands"""
    execute = adv.player["commands"]
    # first, look up for a commanding verb
    for com, words in adv.commands.items():
        if check(words, *adv.player["command"], logic=any):
            for verb in words:  # remove verb from command
                try:
                    adv.player["command"].remove(verb)
                except ValueError:
                    pass
            return execute[com](adv)
    # second, look up for a movement direction
    for words in adv.direction.values():
        if check(words, *adv.player["command"], logic=any):
            return execute["move"](adv)
    # at last, the parser doesn't understand
    return adv.messages["???"]

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

def direction(adv):
    """identify direction in command"""
    for drc, words in adv.direction.items():
        if check(words, *adv.player["command"], logic=any):
            return drc
    return None

def player_input(adv):
    """read player's next command"""
    explet = re.compile(r"\s*(?:\b\s\b|\baz?\b|\bés\b|\begy\b|\bplusz\b)\s*", flags=re.IGNORECASE)
    prompt = ">" if adv.player["steps"] > 5 else adv.messages["prompt"]
    command = input("{} ".format(prompt)).lower()
    adv.player["command"] = [word for word in explet.split(command) if word]
    return adv

def setup(*elements):
    """elements correspond to .json filenames"""
    return namedtuple("adv", " ".join(elements))._make(map(load, elements))

def create_handlers(commands):
    """dynamically create handler functions"""
    return {command: eval(command) for command in commands}

def check(collection, *values, logic=all):
    """check if certain values are present in collection"""
    return logic(value in collection for value in values)

def are_you_sure():
    """answer yes or no"""
    return input("Biztos vagy benne? ").lower().startswith("i")


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
                         "steps": adv.player["steps"]}}
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
        adv.player["steps"] = rst["player"]["steps"]
        # restore room's status
        for room, status in rst["rooms"].items():
            adv.rooms[room]["status"].clear()
            adv.rooms[room]["status"].update(status)
        return adv.messages["ok"]
    return adv.messages["!!!"]

def steps(adv):
    """show player's step count"""
    return adv.messages["steps"].format(adv.player["steps"])


if __name__ == "__main__":
    main()
