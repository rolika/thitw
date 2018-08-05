"""
Main game script
"""

import json
import re
from collections import namedtuple


def main():
    # storing adventure-elements in a named tuple
    # ~ AdventureElements = namedtuple("AdventureElements", "rooms, player, commands")
    # ~ advelems = AdventureElements._make((init("rooms"), init("player"), init("commands")))
    advelems = make_advelems("rooms", "player", "commands")

    # game loop
    while check(advelems.player["status"], "playing", "alive", "nowinner"):
        print(advelems.rooms[advelems.player["location"]]["long"])
        print(parse(input("> ").lower(), advelems))


def make_advelems(*elements):
    """elements correspond to .json filenames"""
    AdvElems = namedtuple("AdvElems", " ".join(elements))
    return AdvElems._make(init(elem) for elem in elements)

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


def check(collection, *values, logic=all):
    """check if certain values are present in collection"""
    return logic(value in collection for value in values)


def parse(command, advelems):
    """parse player command"""
    expletive = re.compile(r"\s*(?:\baz?\b|\bés\b|\begy\b|\bplusz\b)\s*", flags=re.IGNORECASE)
    execute = {
        "exit": exit_game
    }
    command = [word for word in expletive.split(command) if word]
    # first, look up for a commanding verb
    for com in advelems.commands:
        if check(advelems.commands[com], *command, logic=any):
            for verb in advelems.commands[com]:  # remove verb from command
                try:
                    command.remove(verb)
                except ValueError:
                    pass
            return execute[com](command, advelems)
    # second, look up for a movement direction
    pass
    # at last, the parser doesn't understand
    return "Nem értem!"


def exit_game(command, advelems):
    """player exits the game"""
    advelems.player["status"].remove("playing")
    return "Viszlát!"


if __name__ == "__main__":
    main()
