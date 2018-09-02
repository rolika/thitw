"""
The House in the Woods
Text adventure game
"""

import json  # data persistence in the game
import re  # splitting commands at expletive words
from collections import namedtuple  # holds all game data
import textwrap  # pretty printing on console
import readline  # input() remembers previous entries
import sys  # exiting
import os  # file handling


####################################################################################################
# CONSTANTS
####################################################################################################

EXPLET = r"\s*(?:\b\s\b|\baz?\b|\bés\b|\begy\b|\bplusz\b)\s*"
WRAP_WIDTH = 80
HISTORY_BUFFER = 20
CHANGE_PROMPT = 5  # change to simple prompt after 5 steps
MSG_OK = "Rendben"  # must be the same as value of "ok" in commands.json, see in increase_step()

RE_EXPLET = re.compile(EXPLET, flags=re.IGNORECASE)


####################################################################################################
# DECORATOR FUNCTIONS
####################################################################################################

def linewrap(func):
    """Wrap lines to fit to the output.
    
    Args:
        func:   function to decorate

    Modifies:   nothing

    Returns:
        function:   wrapper function
    """
    def linewrapper(adv):
        """Do the actual wrapping.
        
        Args:
            adv:    decorated functions argument

        Modifies:   nothing

        Returns:
            string: wrapped text
        """
        return textwrap.fill(func(adv), width=WRAP_WIDTH)
    return linewrapper

def show(func):
    """Show text on the game's standard output.
    Empty strings won't be showed to avoid empty lines on the output.
    
    Args:
        func:   function to decorate

    Modifies:   nothing

    Returns:
        function:   wrapper function
    """
    def shower(adv):
        """Do the actual printing.
        
        Args:
            adv:    decorated functions argument

        Modifies:   nothing

        Returns:    nothing
        """
        text = func(adv)
        if text:
            print(text)
    return shower

def increase_step(func):
    """Increase player's step count.
    
    Args:
        func:   function to decorate

    Modifies:
        adv:    although through the wrapper function

    Returns:
        function:   wrapper function
    """
    def stepper(adv):
        """Do the actual increase of step count by one.
        
        Args:
            adv:    decorated functions argument

        Modifies:
            adv:    value in player["step"] is incremented by one

        Returns:
            string: whatever message the decorated function provides
        """
        adv.player["step"] += 1
        return func(adv)
    return stepper

def teleport(func):
    """Teleport the player into its inventory, call function, teleport back.
    
    Args:
        func:   function to decorate

    Modifies:   nothing

    Returns:
        function:   wrapper function
    """
    def teleporter(adv):
        """Do the actual teleport.
        
        Args:
            adv:    decorated functions argument

        Modifies:
            adv:    player's location, only temporarly

        Returns:
            string: empty string to conform the decorator
        """
        backup_location = adv.player["location"]
        adv.player["location"] = "leltár"
        func(adv)
        adv.player["location"] = backup_location
        return ""
    return teleporter

####################################################################################################
# MAIN EXECUTING FUNCTION
####################################################################################################

def main():
    """Main executing function.

    Args:   none

    Modifies:
        adv:    through the called functions

    Returns:    nothing
    """
    # adventure-elements in a named tuple, access like adv.rooms or adv.player
    # this adventure namedtuple will be passed around by functions allowing access to all game data
    adv = setup(*get_jsons())
    if not all(adv):
        sys.exit("Something went wrong, unable to start the game.")

    # create references to handler functions
    adv.player["commands"] = {command: eval(command) for command in adv.commands}

    # setup readline history
    readline.set_history_length(HISTORY_BUFFER)
    readline.clear_history()
    readline.set_auto_history(True)

    # main game loop
    while check(adv.player["status"], "playing", "alive", "nowinner"):
        room_description(adv)
        items_listing(adv)
        adv.rooms[adv.player["location"]]["status"].add("visited")
        player_input(adv)


####################################################################################################
# ADVENTURING FUNCTIONS
# All functions here have the single namedtuple argument that holds all the game's data.
####################################################################################################

@show
@linewrap
def room_description(adv):
    """Provide room description.

    Args:
        adv:    namedtuble holding the game data

    Modifies:   nothing

    Returns:
        string: short name or long description of room or too dark message
    """
    location = adv.rooms[adv.player["location"]]
    if "visible" in location["status"]:
        if "verbose" in adv.player["status"]:
            return location["long"]
        if "short" in adv.player["status"] or "visited" in location["status"]:
            return adv.player["location"].capitalize() + "."
        return location["long"]
    return adv.messages["toodark"]

@show
@linewrap
def items_listing(adv):
    """Provide listing of visible and portable items in the current location.

    Args:
        adv:    namedtuble holding the game data

    Modifies:   nothing

    Returns:
        string: short name listing of items or too dark message
    """
    if "visible" in adv.rooms[adv.player["location"]]["status"]:
        items = [name for name, item in adv.items.items()\
                 if item["location"] == adv.player["location"] and\
                 check(item["status"], "visible", "portable")]
        return adv.messages["inventory" if adv.player["location"] == "leltár" else "items"]\
               .format(listing(items)) if items else ""
    return adv.messages["toodark"]

def player_input(adv):
    """Read player's next command.

    Args:
        adv:    namedtuble holding the game data

    Modifies:
        adv:    player["command"] holds the input string

    Returns:
        string: although through execute() and react()
    """
    prompt = ">" if adv.player["step"] > CHANGE_PROMPT else adv.messages["prompt"]
    adv.player["command"] = input("{} ".format(prompt)).lower()
    execute(adv)

def execute(adv):
    """Execute player's command.

    Args:
        adv:    namedtuble holding the game data

    Modifies:
        adv:    player["command"] holds the splitted command in a list of strings

    Returns:
        string: although through react()
    """
    adv.player["command"] = list(filter(None, RE_EXPLET.split(adv.player["command"])))
    if check(adv.commands["again"], *adv.player["command"], logic=any):
        again(adv)  # again is very special, must be handled before anything else
        execute(adv)  # execute() is separated from player_input() because of this recursive call
    else:
        react(adv)

@show
@linewrap
def react(adv):
    """Reaction to player's command.

    Args:
        adv:    namedtuble holding the game data

    Modifies:   nothing

    Returns:
        string: directly or through a handler function
    """
    exe = adv.player["commands"]
    # first, look up for a verb
    com = idword(adv.commands, adv.player["command"])
    if com:
        return exe[com](adv)
    # second, look up for a movement direction, as this is the most common command
    if idword(adv.direction, adv.player["command"]):
        return exe["move"](adv)
    # at last, the parser doesn't understand
    return adv.messages["???"]


####################################################################################################
# HELPER FUNCTIONS
# Various functions to support the adventuring.
# Common is, they don't take the adventure namedtuple as argument.
####################################################################################################

def setup(*elements):
    """Setup namedtuple holding all the game data.

    Args:
        *elements:  correspond to .json filenames in the current directory

    Modifies:   nothing

    Returns:
        namedtuple: named adv with fieldnames corresponding to .json filenames
    """
    return namedtuple("adv", " ".join(elements))._make(map(load, elements))

def check(collection, *values, logic=all):
    """Check if certain values are present in collection.

    Args:
        collection: iterable data collection
        *values:    arbitrary numbers of values
        logic:      keyword only argument, defaults to 'all', can be used with 'any' too

    Modifies:   nothing

    Returns:
        boolean:    indicates result
    """
    return logic(value in collection for value in values)

def confirm(question):
    """Confirm a question with yes or no.

    Args:
        question:   string containing the confirmed question

    Modifies:   nothing

    Returns:
        boolean:    indicates result
    """
    return input(question + " ").lower().startswith("i")

def savefile(command):
    """Create savefile-name.
    If there's no valid name ending with .save, default.save used.

    Args:
        command:    string containing the player's last command

    Modifies:   nothing

    Returns:
        string: complete filename with extension
    """
    sf = "default"
    for com in command:
        if com.endswith(".save"):
            sf = com.split(".")[0]
            break
    return sf

def listing(words, definite=False):
    """Concatenate words to a single string.

    Args:
        words:      collection of strings
        definite:   True:   concatenate with definite articles
                    False:  concatenate with indefinite articles
                    None:   just concatenate

    Modifies:   nothing

    Returns:
        string: a single sentence of concatenated words
    """
    words = (article(word, definite) + word for word in words)
    return ", ".join(words)

def article(word, definite):
    """Article to word considering leading vowels.

    Args:
        word:       string containing a word
        definite:   True:   concatenate with definite articles
                    False:  concatenate with indefinite articles
                    None:   just concatenate

    Modifies:   nothing

    Returns:
        string: containing an article or empty
    """
    if definite is None:
        return ""
    if definite:
        if deaccent(word)[0] in "aeiou":
            return "az "
        return "a "
    return "egy "

def deaccent(word):
    """Transfrom accented letters to non-accented.

    Args:
        word:   string containing a word

    Modifies:   nothing

    Returns:
        string: lowercased without accents
    """
    return word.lower().translate(str.maketrans("áéíóöőúüű", "aeiooouuu"))

def idword(vocabulary, command):
    """Check if command contains a known word in the vocabulary.

    Args:
        vocabulary: dictionary containing keywords and its synonyms
        command:    list of strings

    Modifies:   nothing

    Returns:
        string: identified keyword or
        None:   no match found
    """
    for keyword, synonyms in vocabulary.items():
        if check(synonyms, *command, logic=any):
            return keyword
    return None


####################################################################################################
# JSON DATA PERSISTENCE
# Functions here relate to data persistence used by the game.
####################################################################################################

def get_jsons():
    """Get all .json filenames from current directory.

    Args:   none

    Modifies:   nothing

    Returns:
        list of strings:    containing .json-filenames without extension
    """
    with os.scandir() as it:
        return [entry.name.split(".")[0] for entry in it if entry.name.endswith(".json")]

def load(element, ext="json"):
    """Load adventure elements from .json-files.
    As the JSON-format doesn't support sets, all lists in the .json files get converted to sets, see
    list2set().

    Args:
        element:    .json-filename without extension
        ext:        filename extension, used by savefile() too with .save extension

    Modifies:   nothing

    Returns:
        dictionary: adventure element loaded from .json-file or
        None:       if something went wrong
    """
    try:
        with open(element + "." + ext, "r") as fo:
            return json.load(fo, object_hook=list2set)
    except (IOError, json.JSONDecodeError):
        return None

def dump(content, filename):
    """Write game data in json format.

    Args:
        content:    data in a dictionary
        filename:   filename with extension

    Modifies:   nothing

    Returns:
        boolean:    indicates success
    """
    try:
        with open(filename, "w") as fp:
            json.dump(content, fp, ensure_ascii=False, indent=4)
        return True
    except (IOError, json.JSONDecodeError):
        return False

def list2set(element):
    """Lists should become sets.
    Used as object hook in load(), especially in json.load().

    Args:
        element:    .json-element

    Modifies:   nothing

    Returns:
        element:    itself unchanged or as set if the element was a list
    """
    for key in element:
        if type(element[key]) is list:
            element[key] = set(element[key])
    return element

####################################################################################################
# HANDLER FUNCTIONS
# Function names must correspond to the keys in commands.json, see setup() and react().
# Handler functions must take the adventure namedtuple as a single argument.
# All functions must return some kind of a string message about the action taken. This is needed by
# react()'s decorators.
####################################################################################################

def leave(adv):
    """Player exits the game.
    Asks for confirming before exiting.

    Args:
        adv:    namedtuble holding the game data

    Modifies:
        adv:    player's status by removing 'playing'

    Returns:
        string: 'bye' message if really leaving or 'ok' if playing forth
    """
    if confirm(adv.messages["confirm"]):
        adv.player["status"].remove("playing")
        return adv.messages["bye"]
    return adv.messages["ok"]

@increase_step
def move(adv):
    """Player tries to move in a given direction.
    Examining objects increases the step count.

    Args:
        adv:    namedtuble holding the game data

    Modifies:
        adv:    player's location

    Returns:
        string: message if moving was possible or a warning if it wasn't
    """
    drc = idword(adv.direction, adv.player["command"])
    destination = adv.rooms[adv.player["location"]]["exits"].get(drc)
    if drc and destination:
        adv.player["location"] = destination
        return adv.messages["ok"]
    return adv.messages["cantgo"]

def save(adv):
    """save game to .json file - provide filename ending .save
    Looks for provided filename ending .save, or default.save is used.
    Will be saved:  player's status, location, steps
                    status of all rooms

    Args:
        adv:    namedtuble holding the game data

    Modifies:   nothing

    Returns:
        string: message if saving the game was successful or a warning if something went wrong
    """
    tosave = {"player": {"status": list(adv.player["status"]),
                         "location": adv.player["location"],
                         "step": adv.player["step"]}}
    tosave.update({"rooms": {name: list(adv.rooms[name]["status"]) for name in adv.rooms}})
    if dump(tosave, savefile(adv.player["command"]) + ".save"):
        return adv.messages["ok"]
    return adv.messages["!!!"]

def restore(adv):
    """Restore saved game.
    Looks for provided filename ending .save, or default.save is used.

    Args:
        adv:    namedtuble holding the game data

    Modifies:
        adv:    player's data
                all room status data
    Returns:
        string: message if restoring was successful or a warning if it wasn't
    """
    rst = load(savefile(adv.player["command"]), ext="save")
    if rst:
        # restore player
        adv.player["status"].clear()
        adv.player["inventory"].clear()
        adv.player["status"].update(rst["player"]["status"])
        adv.player["location"] = rst["player"]["location"]
        adv.player["step"] = rst["player"]["step"]
        # restore room's status
        for room, status in rst["rooms"].items():
            adv.rooms[room]["status"].clear()
            adv.rooms[room]["status"].update(status)
        return adv.messages["ok"]
    return adv.messages["!!!"]

def step(adv):
    """Show player's step count.

    Args:
        adv:    namedtuble holding the game data

    Modifies:   nothing

    Returns:
        string: message showing steps so far
    """
    return adv.messages["step"].format(adv.player["step"])

@show
@linewrap
def again(adv):
    """Repeat last command.
    The actual repeating is in execute(), it digs here in readline's history.

    Args:
        adv:    namedtuple holding the game data

    Modifies:
        adv:    player's actual command ('again') is substituted with the command before or with an
                empty string, if there wasn't any before (won't be recognized by the parser)

    Returns:
        string: message about repeating a certain command
    """
    idx = readline.get_current_history_length()
    if idx > 1:
        readline.remove_history_item(idx - 1)
        adv.player["command"] = readline.get_history_item(idx - 1)
    else:
        adv.player["command"] = ""
    return adv.messages["repeat"] + adv.player["command"]

@increase_step
@teleport
def inventory(adv):
    """Show items in player's inventory.
     Uses the already available item_listing() through 'teleporting' the player into its inventory.

    Args:
        adv:    namedtuple holding the game data

    Modifies:
        adv:    temporarly modifies player's location

    Returns:
        string: empty, conform to the decorator
    """
    items_listing(adv)
    return ""

@increase_step
def examine(adv):
    """Lets the player look around.
    Examining objects increases the step count.

    Args:
        adv:    namedtuple holding the game data

    Modifies:
        adv:    when successful, adds 'examined' status to object

    Returns:
        string: depending on examine
                stands alone:   long description of current location
                with item:      long description of that object
                with inventory: inventory listing
                or else:        warning message about unknown object
    """
    return adv.messages["unknown"]


if __name__ == "__main__":
    main()
