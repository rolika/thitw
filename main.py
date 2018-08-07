"""
Main game script
"""

import json
import re
from collections import namedtuple
import textwrap


def main():
    # store adventure-elements in a named tuple, for access like adv.rooms or adv.player
    adv = setup("rooms", "player", "commands", "messages", "direction")

    # game loop
    while check(adv.player["status"], "playing", "alive", "nowinner"):
        print(textwrap.fill(show(adv), width=80))
        adv.rooms[adv.player["location"]]["status"].add("visited")
        print(parse(input("> ").lower(), adv))


def setup(*elements):
    """elements correspond to .json filenames"""
    return namedtuple("adv", " ".join(elements))._make(map(init, elements))

def init(element):
    """adventure elements stored in dictionary"""
    with open(element+".json", "r") as fo:
        return json.load(fo, object_hook=list2set)

def list2set(element):
    """lists should become sets"""
    for key in element:
        if type(element[key]) is list:
            element[key] = set(element[key])
    return element


def parse(command, adv):
    """parse player command"""
    explet = re.compile(r"\s*(?:\b\s\b|\baz?\b|\bés\b|\begy\b|\bplusz\b)\s*", flags=re.IGNORECASE)
    execute = {
        "exit": exit_game,
        "move": move
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


if __name__ == "__main__":
    main()
