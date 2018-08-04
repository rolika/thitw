"""
Element classes
"""

class AdventureElement(dict):
    """base class for rooms, items, places, traps etc"""
    def __init__(self, props):
        """init with property: value elements coming as dictionary from json file"""
        super().__init__(props)
        self["status"] = set(self["status"])
        self["vocabulary"] = set(self["vocabulary"])

    def __str__(self):
        """pretty print for testing"""
        return "{}\n{}".format(self["name"], self["long"])

    def check(self, prop, *values, logic=all):
        """check element's property containing certain values"""
        return logic(value in self[prop] for value in values)


class Room(AdventureElement):
    """hold the game's places"""
    def __init__(self, props):
        super().__init__(props)

    def destination(self, direction):
        """return destination room's name or None if the player can't go that way"""
        return self["exits"].get(direction)


class Player(AdventureElement):
    """hold everything player-related"""
    def __init__(self, props):
        super().__init__(props)
        self["location"] = None

    def is_in_game(self):
        return self.check("status", "alive", "playing", "nowinner")
    

if __name__ == "__main__":
    """testing stuff"""
    import json
    with open("places.json") as fp:
        places = {place["name"]: Room(place) for place in json.load(fp)}
        for place in places:
            if places[place].destination("UP"):
                print(places[place]["exits"]["UP"])
