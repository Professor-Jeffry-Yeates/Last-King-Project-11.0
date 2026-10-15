__version__ = '11.0'
from CoffeeBean import *
from CoffeeCanvas import *
from PlayerClass import *
import json, random, platform, os, sys
from datetime import *
from Utilities import setDictionaryValueAsBoolean

from resource_path import get_parent_resource_path

class QuizClass():
    """Load from files the information about a specific quiz, including:
        folders, questions, map, and other information. """

    def __init__(self, fileName=None):
        # Platform specific changes
        if platform.system() == 'Windows':
            from PC_PlatformSpecific import PlatformSpecific as PlatformSetup
        else:
            from Mac_PlatformSpecific import PlatformSpecific as PlatformSetup

        # Get the specific game folder and file with the game instructions and information. 
        instructionFile = "{0}.json".format("Instructions")
        
        # First try is in the main folder. Second try is one folder up
        firstTrySuccessful = False
        thisDirectory = os.getcwd()
        contentPath = os.path.join(thisDirectory, fileName)
        instructionFilePath = os.path.join(contentPath,instructionFile)
        
        # Open the local game file from this directory which is in JSON format 
        try:
            with open(instructionFilePath, "r") as f: data = json.load(f)
            firstTrySuccessful = True
        except FileNotFoundError:
            print(f"Error: Game file {instructionFilePath} not found. Trying one directory up.")

        # A standalone executable keeps Quiz content inside the bundle
        if not firstTrySuccessful and getattr(sys, "frozen", False):
            bundle_root = getattr(sys, "_MEIPASS", "")
            contentPath = os.path.join(bundle_root, fileName)
            instructionFilePath = os.path.join(contentPath, instructionFile)
            try:
                with open(instructionFilePath, "r") as f: data = json.load(f)
                firstTrySuccessful = True
            except FileNotFoundError:
                print(f"Error: Game file {instructionFilePath} not found. Trying one directory up.")
            
        # Upon failure, open the local game file in one directory up which is in JSON format 
        if not firstTrySuccessful:
            upOneDirectory = get_parent_resource_path('')
            contentPath = os.path.join(upOneDirectory, fileName)
            instructionFilePath = os.path.join(contentPath,instructionFile)
            try:
                with open(instructionFilePath, "r") as f: data = json.load(f)
            except FileNotFoundError:
                print(f"Error: Game file {instructionFilePath} not found. Exiting")
                exit()

        # Save the information in a dictionary.There are some defaults for development
        try:
            self.dictionary = dict(**data)
            self.dictionary.setdefault("Quiz Name", "Development")
            self.dictionary.setdefault("Title", "Development")
            self.dictionary.setdefault("Quiz Folder", "Development")
            self.dictionary.setdefault("SenarioMap", "CCUland")
            setDictionaryValueAsBoolean(self.dictionary, "Shuffle Questions", True)
        except:
            print(f"Error: Game file {instructionFilePath} is not properly formatted. Exiting")
            exit()

        # Save the specific game files and folder locations
        try:
            for item in ["JSON","Content","GameObjects"]:
                self.dictionary[item +" Path"] = contentPath
            
            for item in ["Music","Sounds","Objects"]:
                self.dictionary[item + " Path"] = os.path.join(contentPath, item)
            self.dictionary["Vocabulary"] = os.path.join(contentPath, "Vocabulary")
                
            for item in ["Questions","Places","GameObjects","Objects","ScenarioObjects"]:
                self.dictionary[item + " Json"] = os.path.join(contentPath, item + ".json")

            # Maps contain a map and the player path for the map
            mapFolder = os.path.join(contentPath, "Maps")

            scenarioMapName = self.dictionary["SenarioMap"]
            self.dictionary["SenarioMap Path"] = os.path.join(mapFolder, scenarioMapName+"_path.png")
            if scenarioMapName.find("_map") == -1: scenarioMapName += "_map"
            if scenarioMapName.find(".") == -1: scenarioMapName +=".png"
            self.dictionary["SenarioMap"] = os.path.join(mapFolder,scenarioMapName)

            mapName = self.dictionary["Map Name"]
            self.dictionary["Map Path"] = os.path.join(mapFolder, mapName+"_path.png")
            if mapName.find("_map") == -1: mapName += "_map"
            if mapName.find(".") == -1: mapName +=".png"
            self.dictionary["Map"] = os.path.join(mapFolder, mapName)

        except:
            print(f"Error: Game folder {contentPath} is not properly populated. Exiting")
            exit()

        # Additional defaults for folders
        self.dictionary.setdefault("Places Path", "Places")
        self.dictionary.setdefault("Objects", "Objects")
        self.dictionary.setdefault("Questions", "Questions.json")
        self.dictionary.setdefault("Music", "Music",)
        self.dictionary.setdefault("Sounds", "Sound")
        self.dictionary.setdefault("GameObjects", "GameObjects")

        # Pictures and problem files
        self.dictionary.setdefault("Problems", "Problems") 
        self.dictionary.setdefault("Pictures", "Pictures")
        self.dictionary["Problem Folder"] =  os.path.join( contentPath, self.dictionary["Problems"])
        self.dictionary["Picture Folder"] = os.path.join( contentPath, self.dictionary["Pictures"])

    def __getitem__(self, key):
        if key in self.dictionary:
            return self.dictionary[key]
        else:
            return None
        
    def get(self, key, alternative):
        if key in self.dictionary:
            return self.dictionary[key]
        else:
            return alternative
