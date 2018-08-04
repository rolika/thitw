"""
Main game script
"""

import json
import advelem

def main():
    rooms = init("room")
    player = init("player")
    player["Henry Fuljames"]["location"] = "terasz"

    while player["Henry Fuljames"].is_in_game():
        com = input("> ")

def init(element):
    """adventure elements stored in a dictionary keyed with the elements names"""
    with open(element+".json", "r") as j:
        return {item["name"]: getattr(advelem, element.capitalize())(item) for item in json.load(j)}

if __name__ == "__main__":
    main()
