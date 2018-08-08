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


def main():
    # store adventure-elements in a named tuple, for access like adv.rooms or adv.player
    adv = setup("rooms", "player", "commands", "messages", "direction")

    # main game loop
    while check(adv.player["status"], "playing", "alive", "nowinner"):
        print(textwrap.fill(show(adv), width=80))
        adv.rooms[adv.player["location"]]["status"].add("visited")
        print(parse(input("> ").lower(), adv))

def parse(command, adv):
    """parser for player's commands"""
    explet = re.compile(r"\s*(?:\b\s\b|\baz?\b|\bés\b|\begy\b|\bplusz\b)\s*", flags=re.IGNORECASE)
    execute = {
        "exit": exit_game,
        "move": move,
        "save": save,
        "restore": restore
    }
    command = [word for word in explet.split(command) if word]
    # first, look up for a commanding verb
    for com, words in adv.commands.items():
        if check(words, *command, logic=any):
            for verb in words:  # remove verb from command
                try:
                    command.remove(verb)
                except ValueError:
                    pass
            return execute[com](command, adv)
    # second, look up for a movement direction
    for words in adv.direction.values():
        if check(words, *command, logic=any):
            return execute["move"](command, adv)
    # at last, the parser doesn't understand
    return adv.messages["???"]


# handler functions

def exit_game(command, adv):
    """player exits the game"""
    if are_you_sure():
        adv.player["status"].remove("playing")
        return adv.messages["bye"]
    return adv.messages["ok"]

def move(command, adv):
    """player tries to move in a given direction"""
    drc = direction(command, adv)
    destination = adv.rooms[adv.player["location"]]["exits"].get(drc)
    if drc and destination:
        adv.player["location"] = destination
        return adv.messages["ok"]
    return adv.messages["cantgo"]

def save(command, adv):
    """save game to .json file - provide filename ending .save"""
    tosave = {"player": {"status": list(adv.player["status"]),
                         "location": adv.player["location"],
                         "inventory": list(adv.player["inventory"])}}
    tosave.update({"rooms": {name: list(adv.rooms[name]["status"]) for name in adv.rooms}})
    if dump(tosave, savefile(command) + ".save"):
        return adv.messages["ok"]
    return adv.messages["oops"]    

def restore(command, adv):
    """restore saved game - look for provided filename ending .save"""
    rst = load(savefile(command), ext="save")
    if rst:
        # restore player
        adv.player["status"].clear()
        adv.player["inventory"].clear()
        adv.player["status"].update(rst["player"]["status"])
        adv.player["inventory"].update(rst["player"]["inventory"])
        adv.player["location"] = rst["player"]["location"]
        # restore room's status
        for room, status in rst["rooms"].items():
            adv.rooms[room]["status"].clear()
            adv.rooms[room]["status"].update(status)
        return adv.messages["ok"]
    return adv.messages["oops"]


# helper functions

def setup(*elements):
    """elements correspond to .json filenames"""
    return namedtuple("adv", " ".join(elements))._make(map(load, elements))

def check(collection, *values, logic=all):
    """check if certain values are present in collection"""
    return logic(value in collection for value in values)

def are_you_sure():
    """answer yes or no"""
    return input("Biztos vagy benne? ").lower().startswith("i")

def direction(command, adv):
    """identify direction in command"""
    for drc, words in adv.direction.items():
        if check(words, *command, logic=any):
            return drc
    return None

def show(adv):
    """provide environment description"""
    location = adv.rooms[adv.player["location"]]
    if "visible" in location["status"]:
        if "verbose" in adv.player["status"]:
            return location["long"]
        if "short" in adv.player["status"] or "visited" in location["status"]:
            return adv.player["location"].capitalize() + "."
        return location["long"]
    return adv.messages["toodark"]


# json data persistence

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

def savefile(command):
    """create or read savefile-name"""
    sf = "default"
    for com in command:
        if com.endswith(".save"):
            sf = com.split(".")[0]
            break
    return sf


if __name__ == "__main__":
    main()
