"""
Main game script
"""

import json
import re

def main():
    rooms = init("rooms")
    player = init("player")
    commands = init("commands")
    while check(player["status"], "playing", "alive", "nowinner"):
        print(rooms[player["location"]]["long"])
        print(parse(input("> ").lower(), rooms, player, commands))




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


def check(among, *values, logic=all):
    """check if certain values are present"""
    return logic(value in among for value in values)


def parse(command, rooms, player, commands):
    """parse player command"""
    expletive = re.compile(r"\s*(?:\baz?\b|\bés\b|\begy\b|\bplusz\b)\s*", flags=re.IGNORECASE)
    execute = {
        "exit": exit_game
    }
    command = [word for word in expletive.split(command) if word]
    # first, look up for a commanding verb
    for com in commands:
        if check(commands[com], *command, logic=any):
            for verb in commands[com]:  # remove verb from command
                try:
                    command.remove(verb)
                except ValueError:
                    pass
            return execute[com](command, rooms, player, commands)
    # second, look up for a movement direction
    pass
    # at last, the parser doesn't understand
    return "Nem értem!"


def exit_game(command, rooms, player, commands):
    """player exits the game"""
    player["status"].remove("playing")
    return "Viszlát!"


if __name__ == "__main__":
    main()
