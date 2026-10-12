__version__ = '11.0'
from QuizClass import *
from MapClass import *
import CoffeeCanvas
from random import shuffle
from VocabularyClass import *
from StatusClass import *
from RewardClass import *
from DragonClass import *
from TrollClass import *
from SpiderClass import *
import multiprocessing as mp
import datetime, pathlib, os, tempfile

def parent_of_run_directory():
    """Folder above the directory the program was started from."""
    return os.path.normpath(os.path.join(os.getcwd(), os.pardir))

def can_replace_file(path):
    """Return True when an existing file at path can be removed and a new one created.
    A successful check removes the file so the next save starts clean."""
    try:
        folder = os.path.dirname(path)
        if folder and not os.path.isdir(folder):
            return False
        if os.path.exists(path):
            os.remove(path)
        with open(path, "a") as result_file:
            result_file.write("")
        os.remove(path)
        return True
    except OSError:
        return False

def game_result_path(filename="GameResult.txt"):
    """Path for the result file: parent of the run folder, or the temp folder if that cannot be saved."""
    preferred = os.path.join(parent_of_run_directory(), filename)
    if can_replace_file(preferred):
        return preferred
    fallback = os.path.join(tempfile.gettempdir(), filename)
    can_replace_file(fallback)
    return fallback

class DataClass():
    """Data Class for storing most data and providing access to it."""

    def __init__(self, canvas, vocabulary, **kwargs):
        """Initialize the DataClass, start with manually providing links to all the other major classes.
        PARAMETERS
            canvas: main canvas everything is draw on
            vocabulary: instantiated vocabulary class
            kwargs:   'debugging'
                      any pair of keys and instantiated classes for access upon request
        FILES:
            'GameResult.txt' stores the results in the parent of the folder the program is run from.
            If that file cannot be saved there, it is saved in the temporary folder.
        """
        self.canvas = canvas
        self.root = canvas.root
        
        self.debugging = kwargs.pop("debugging", False) # Set in controls to enable error catching (as in question area)
        
        """ Resources saves access to major classes based on a provided name. This allows auditing of access
        similar to dependency injection.  It is initialized with data itself. Entries can be added or removed.
        This access allows classes to access other classes when processing, even though they were not all
        instantiated in a particular order."""
        self.resources = {'data':self} # Collect links to all major resources used by the quiz
        for key, value in kwargs.items(): self.setResource( key, value)

        # Setup to use a gameresult file in the parent folder, or the temp folder if that cannot be written
        self.errorFile = None
        self.gameResultFile = game_result_path("GameResult.txt")
        self.outputDirectory = os.path.dirname(self.gameResultFile)
        
        # This vocabulary class can be game specific and is incorparated into the standard vocabulary
        self.vocab = VocabularyClass(self, self.quiz['Vocabulary'])
        vocabulary.setup(self) # Requires other resources to be set up first
        self.setResource('vocabulary', self.vocab)

        # Setup for questions
        self.missedQuestions = []  # List to keep track of used questions
        self.recycleMissedQuestions = self.quiz.get("Recycle missed questions", "Empty")

        # Major paths to files
        self.jsonFolder = None if self.quiz is None else self.quiz.dictionary["JSON Path"]
        self.objectsPath = None if self.quiz is None else self.quiz.dictionary["Objects Path"]

        # Collect all the JSON information in lists
        self.objects = DataClass._readJsonFileArray( "Objects", self.quiz )
        self.postPlayerObjects = []  # List for objects that are above the player
        self.places = DataClass._readJsonFileArray( "Places", self.quiz, ordered="id" )
        self.questions = DataClass._readJsonFileArray( "Questions", self.quiz, ordered="id")
        gameObjectsDictionary = DataClass._readJsonCompilationDictionary( "GameObjects", self.quiz )
        self.providedTimers = gameObjectsDictionary.get( "Timers", [] )
        self.sounds = gameObjectsDictionary.get( "Sounds", [] )
        self.music = gameObjectsDictionary.get( "Music", [] )
        self.soundtracks = gameObjectsDictionary.get( "Soundtracks", [] )
        self.npcs = gameObjectsDictionary.get( "NPCs", [] )
        self.specialCode = self.specialCodeFunction

        self.boss = None # Which ever boss is active, access it here, generally by self.boss.activate()
        self.potionMapObject = None # Potion object, if it exists. Limited at the moment to just one. Could become an array.
        
        # Timing
        self.startTime = None
        self.torches = 0
        self.initialTorches = 0
        self.torchBurnTime = 60
        self.gameIsActive = True
        self.codingLock = mp.Lock()
        self.graphicLock = mp.Lock() # Lock graphic usage to support threadsafe
        self.processExitFunction = self.defaultReturn
        
        # Collected as a first screen
        self.userName = None
        self.studentName = None
        self.nickname = None

        # Computer specific values for timing
        if canvas.window.MacOS:
            self.UIfadeTime = 20  # Speed of fading objects
            self.UIautomaticTime = 4 # Pause between automatic mouse click processing
            self.UIloopTime = 2 # 16 # Speeds up looping, looking for mouse clicks or key inputs
            self.UIautomaticMove = 1  # Each movement for processing stored mouse clicks
        else:
            self.UIfadeTime = 50            
            self.UIautomaticTime = 4
            self.UIloopTime = 2 #16
            self.UIautomaticMove = 1

        self.mapScrollDictionary = {}
        """ OBJECTS:  Insure each object has all required fields as the JSON file does not need to specify defaulted values
            TREASURES have similar attributes.
        Possible fields for objects are (R) means Required in JSON file:
        Name (R):     Identifies specific object but can also be generic, such as "Object" or "Treasure"
        Purpose: (R)  Text describing the purpose of the object, such as "A weapon to fight with" or "A place to rest"
        Kind:         Subset of purpose, text specific to the kind of object, can be based on its Name. RANDOM is replaced by randomly chosen using Name.
        File (R):     Graphics file name (default extension is ".png) if there is one 
        Map:          Named location or coordinate. If missing a random location matching its use is selected from map places
        Use:          Type of location object is placed in. Searched for if Map location is not named.
        Activate:     (Text/F) if object is activated by another object. That object uses the Activate name to find the object
        Is a Room:    (T/F) if object describes the room it is in. Darkness does this.
        Room:         Name of the room this object is in. If not specified, it is the same as the Map location.
        Transport:    (T/F) on whether the user can travel across the object as a Safe Travel.  Used by troll bridges.
        Action:       Single/List/tuple of named actions as text. Can be substituted with actual code after processing
        Message:      Message displayed upon object being activated
        Contents:     List of objects that are in the room, only used by rooms
        Description:  Initial description of object displayed in the game. Text follows these VocabularyClass() rules and can be blank of "STANDARD".
        1) Single text element is a straight text description with no changes
        2) Two text elements are a vocab description string and the second its random content list(s).
        3) Three text elements are a vocab description and content list followed by the object's dictionary key for the value of that key's values
        NOTE: If a vocab description does not have curly braces in it, it is a named vocab description. Similarly, if a content string
              is not a list, tuple, or does not conatin comma(s) then it is a named content list and not a list itself.
              If a description is named "STANDARD" then a 3 element description is created for that KIND or USE of the object.

        """
        
        # Insure questions have all needed keys
        self.updateOptionalQuestionKeys(ordered="id")
        if self.quiz.get("Shuffle Questions",True):
            shuffle(self.questions)
            
        # Guarentee (almost) all places keys are specified
        for index,itemDictionary in enumerate(self.places):
            self.initializePlaces(itemDictionary, index)
        if self.quiz.get("Shuffle Places",True):
            shuffle(self.places)

        # Add in random Treasures at the front of the object lists
        randomTreasureCount = self.quiz.get("Random Treasure", 0)
        if randomTreasureCount > 0:
            maxTreasures = len(self.questions) + 5
            randomTreasureCount = min(randomTreasureCount, maxTreasures)  # Minimum of 10 random treasures
            for _ in range(randomTreasureCount):
                itemDictionary = dict(Purpose="Treasure" )
                self.objects.insert(0,itemDictionary)

        # For all objects, default attributes provided or abbreviations expanded
        for itemDictionary in self.objects:
            self.initializeDarkness(itemDictionary)
            self.initializeTreasure(itemDictionary) 
            self.initializeWeapons(itemDictionary)

        self.initializeQuizWeapons()
        for index,itemDictionary in enumerate(self.objects):
            self.initializeObject(itemDictionary, index)
            self.exchangeTreasureKeywords(itemDictionary)
            self.exchangeObjectKeywords(itemDictionary)

        # Lastly, add in any requested random objects and special objects in the quiz json
        self.initializeRandomObjects()
    
    def logError(self, *args):
        """Log string messages to a log file."""
        # Keep the error log next to the game result, or in the temp folder if that cannot be written
        if self.errorFile is None:
            directory = getattr(self, "outputDirectory", None) or parent_of_run_directory()
            self.errorFile = os.path.join(directory, "log_temp.txt")
            if not can_replace_file(self.errorFile):
                self.errorFile = os.path.join(tempfile.gettempdir(), "log_temp.txt")
                can_replace_file(self.errorFile)
        
        # Save each args/item provided
        if args is not None and len(args) > 0:
            try:
                log_file = open(self.errorFile, "a")
            except OSError:
                self.errorFile = os.path.join(tempfile.gettempdir(), "log_temp.txt")
                log_file = open(self.errorFile, "a")
            with log_file:
                for arg in args:
                    message = ""
                    if type(arg) == str:
                        message = arg
                    elif type(arg) == datetime.datetime:
                        message = arg.strftime("%Y-%m-%d %H:%M:%S")
                    elif type(arg) == Exception:
                        message = "Exception: " + str(arg)
                    else:
                        message = str(arg)
                    if len(message) > 0:
                        log_file.write(message)
                log_file.write("\n\n")
    
    def _extractParameter( text ):
        """ Extract the parameter from a string like "gold(100)" or message(Hello there) and 
        return the tuple parameter as the lower case text and either an integer or text.   
        If no text return no and if no parameter is found, return None for it."""
        if text is None: return None,None
        leftParen = text.find("(")
        if leftParen < 0: return text,None
        rightParen = text.find(")")
        if rightParen < 0: return text,None
        parameter = text[leftParen+1:rightParen]
        usefulText = text[:leftParen]
        if len(parameter) == 0: return usefulText,None
        if not parameter.isdigit(): return usefulText,parameter
        try:
            number = int(parameter)
            return usefulText, number
        except ValueError:
            return usefulText,parameter
    _extractParameter = staticmethod(_extractParameter)
    
    def _readJsonFileArray(name, quiz, optional=False, ordered=None):
        """Read data from a JSON file. 
        Parameters:
            name: file name
            quiz: quiz information
            optional: non-optional elements have an error message if they fail
            ordered: Default None, if not None, add ordered string as a key incremented from 1
        Return: List of dictionaries
        """
        success = True
        array = []
        shortname = name + " Json"
        filename = quiz[shortname]
        try:     
            with open(filename, "r") as f: rawJsonData = json.load(f)
        except:
            if not optional: 
                DataClass.logError(f"Error: Unable to access {name} data which contains the quiz dictionary!")
            success = False

        else:
            counter = 1
            elements = rawJsonData[name]
            for item in elements:
                try:
                    attemptedDictionary = dict(**item)
                    if ordered != None:
                        attemptedDictionary[ordered] = counter
                        counter += 1
                except:
                    DataClass.logError(f"Error in DataClass: Unable to read {item} into dictionary {name}!")
                else:
                    array.append(attemptedDictionary)

        if not success and not optional:
            exit()         
            
        return array
    _readJsonFileArray = staticmethod(_readJsonFileArray)
  
    def _extractIndividualActions(actions):
        if actions is None: return []
        actionList = []
        if type(actions) == str:
            textList = actions.split(",")
            if len(textList) == 1:
                actionTuple = DataClass._extractParameter(textList[0])
                actionList.append(actionTuple)
            else:
                for eachActionName in textList:
                    actionTuple = DataClass._extractParameter(eachActionName)
                    actionList.append(actionTuple)
        elif type(actions) == list:
            for eachActionName in actions:
                actionTuple = DataClass._extractParameter(eachActionName)
                actionList.append(actionTuple)
        elif type(actions) == callable:
            actionTuple = actions, None
            actionList.append(actionTuple)         
        return actionList
    _extractIndividualActions = staticmethod(_extractIndividualActions)
  
    def _readJsonCompilationDictionary(name, quiz, optional=False):
        """Read data from a JSON file that contains multiple parts."""
        success = True
        shortname = name + " Json"
        filename = quiz[shortname]
        try:     
            with open(filename, "r") as f: data = json.load(f)
            data = dict(**data)
        except:
            if not optional: 
                DataClass.logError(f"Error: Unable to access {name} data which contains the quiz dictionary!")
            success = False

        if not success and not optional:
            exit()
        return data
    _readJsonCompilationDictionary = staticmethod(_readJsonCompilationDictionary)
 
    def setResource(self, name, actualClassReference):
        """ Store a class resource into the data class, such as a map or status bar. 
        Will also add a  reference back to data if it does not exist.
        """
        self.resources[name] = actualClassReference
        if hasattr(actualClassReference, 'data'):
            if actualClassReference.data is None:
                actualClassReference.data = self
        match name:
            case 'instructions':
                self.instructions = actualClassReference
            case 'statusBar':
                self.statusBar = actualClassReference
            case 'rewardBox':
                self.rewardBox = actualClassReference
            case 'soundMixer':
                self.soundMixer = actualClassReference
            case 'playersMap':
                self.playersMap = actualClassReference
            case 'map':
                self.map = actualClassReference
            case 'badges':
                self.badges = actualClassReference
            case 'quiz':
                self.quiz = actualClassReference
            case 'questionArea':
                self.questionArea = actualClassReference
            case 'player':
                self.player = actualClassReference
            case 'debugging':
                self.debugging = actualClassReference
        return self
    
    def getResource(self, name):
        """ Get a class resource from the data class, such as a map or status bar. """
        return self.resources.get(name, None)

    def removeResource(self, name):
        found = self.resources.get(name, None)
        if found != None:
            del self.resources[name]
            _ = self.setResource( name, None)
            
    def initializePlaces(self, itemDictionary, index):
            _ = itemDictionary["Map"] # "Map" must exist, force an error if missing
            itemDictionary["Id"] = index
            itemDictionary.setdefault("Use",'Any')
            itemDictionary.setdefault("Name",'')
            itemDictionary.setdefault("Description",'')
            itemDictionary.setdefault("Message",'')
            itemDictionary.setdefault("Room", '') # Room is optional, but if it exists, it must be a string

    def initializeRandomObjects(self):
        count = self.quiz.get("Random Object", 0)
        for eachRandomObject in range(count):
            index = len(self.objects)
            itemDictionary = dict(Name="RANDOM", Description="was not found")
            self.initializeObject(itemDictionary, index)
            self.exchangeObjectKeywords(itemDictionary)
            if itemDictionary is not None and itemDictionary["Description"] != "was not found": 
                self.objects.append(itemDictionary)

    def initializeWeapons(self, itemDictionary):
        if itemDictionary is not None:  
            name = itemDictionary["Name"]
            if name.find("Sword") >= 0:
                itemDictionary.setdefault("Purpose","Weapon")
                itemDictionary.setdefault("Action", "Sword")  
                names = name.split(" ")
                if len(names) > 1:
                    newName = f"{names[0]} Game{names[1]}"
                else:
                    newName = f"Game{name}"
                itemDictionary.setdefault("File", newName)

    def initializeQuizWeapons(self):
        # Get the place to insert quiz named weapons
        start = 0
        for index in range(len(self.objects)):
            itemDictionary = self.objects[index]
            name = itemDictionary.get("Name", None)
            if name in ["Sword","Potion","Darkness"]:
                start = index
                break
            
        # Add in any requested quiz weapons
        for name in ["Broken Sword", "Damaged Sword"]:
            count = self.quiz.get(name, 0)
            for _ in range(count):
                itemDictionary = dict(Name=name, Purpose="Weapon", Action="Sword")
                names = name.split(" ")
                if len(names) > 1:
                    newName = f"{names[0]} Game{names[1]}"
                else:
                    newName = f"Game{name}"
                itemDictionary.setdefault("File", newName)
                self.objects.insert(start,itemDictionary)

    def initializeObject(self, itemDictionary, index):
        if itemDictionary is not None:
            itemDictionary['Id'] = index    

            itemDictionary.setdefault("Room","")  
            itemDictionary["Is a Room"] = False if itemDictionary["Room"] == False else ( len(itemDictionary["Room"]) > 0 )
            fileName = itemDictionary.get("File", None)
            if fileName is None:
                itemDictionary["File"] = ""
            elif fileName.find(".") < 0:
                itemDictionary["File"] = f"{fileName}.png"

            itemDictionary.setdefault("Purpose", "Object")
            anyPurpose = itemDictionary["Purpose"]
            itemDictionary.setdefault("Map",[])
            itemDictionary["StandardMap"] = itemDictionary["Map"] 
            itemDictionary.setdefault("Name", "RANDOM")  
            itemDictionary.setdefault("Transport", anyPurpose == 'invisible')
            itemDictionary.setdefault("Boss",False)
            itemDictionary.setdefault("Contents",[])  
            itemDictionary.setdefault("Modify", False)
            itemDictionary.setdefault("Use",'Any') 
            ## itemDictionary.setdefault("Special",None) String, OK to be missing
            descriptionDefault = "STANDARD_" + anyPurpose.upper()
            itemDictionary.setdefault("Description",descriptionDefault)
            itemDictionary.setdefault("Activate",False) # If a string, it can be activivated by its room or a room can activate it remotely
            itemDictionary.setdefault("Action", None) # Default action is a question or an action by the object

            # Specialty Objects - Invisible
            if anyPurpose == "invisible":
                mapLocation = itemDictionary["Map"]
                coord = mapLocation
                if mapLocation == "Player Location":
                    boxLocation = self.quiz.get("Player Location", "Center" )
                    if type(boxLocation) == str: 
                        if boxLocation == "Center":
                            coord = self.map.getCurrentCenterLocation()
                itemDictionary["Map"] = coord
                itemDictionary.setdefault("Size", [12,30])
                itemDictionary.setdefault("Polygon", None) # Can be an invisible object with [points...]

    
    def displayPreplayerObjects(self, map, displayDarkness=True):
        """ Display all objects that are below the player, such as the map, paths, and treasure. """
         
        # If the treasure has a specific question, store it so it is not randomly taken
        for objectDictionary in self.objects:
            if  objectDictionary["Purpose"] == 'Treasure':
                action = objectDictionary.get("Action", None)
                question,parameter = self._extractParameter(action)
                if question.lower() == 'question':
                    if parameter is not None and len(parameter) > 0:
                        parameter = parameter.lower()
                        foundQuestion = None
                        for index,eachQuestion in enumerate(self.questions):
                            if eachQuestion['Title'].lower() == parameter:
                                foundQuestion = self.questions.pop(index)
                                break
                        objectDictionary['Question'] = foundQuestion
          
        # Add in each object action connections, create it and add any any actions
        for objectDictionary in self.objects: # On top of any treasure
            coord = objectDictionary["Map"]
            polygon = objectDictionary.get("Polygon", None)
            if len(coord) == 0 and polygon is None: continue    
            name = objectDictionary.get("Name", "")
            purpose = objectDictionary["Purpose"]
            transport = objectDictionary.get('Transport', False) # Can be traveled over like a path

            if purpose.lower() == "darkness" and not displayDarkness: continue # Debugging option

            # Invisible objects are used to trigger "Action"s at specific places but the obects are not shown.
            # A General suggestion is they be of travel-width 12 to they are always hit once but not lots of times.
            if purpose.lower() == "invisible": 

                # Polygons
                if polygon is not None:
                    # The points in the polygon need to be map coordintes
                    # convert each number in the polygon list to use map coordinates
                    newPolygon = []
                    first = polygon[0]
                    if isinstance(first, Point) or isinstance(first, tuple):
                        for point in polygon:
                            newPoint = map.convertStandardToMapCoordinates(point)
                            newPolygon.append(newPoint)
                    else:
                        for a in range(0,len(polygon),2):
                            b = a+1
                            newPoint = map.convertStandardToMapCoordinates(polygon[a], polygon[b])
                            newPolygon.append( (newPoint[0], newPoint[1]) )
                    theObject = MapPolygon(map, newPolygon, fill=None, outline=None, width=0, 
                                           invisible=True, transport=transport, name=name)
                    
                # Rectangles (other objects can be made as needed)
                else:
                    height, width = objectDictionary["Size"]
                    x,y = coord
                    x1 = x + int(width/2)
                    y1 = y + int(height/2)
                    x -= int(width/2)
                    y -=  int(height/2)
                    theObject = MapRectangle(map, x, y, x1, y1, fill=None, outline=None, width=0, 
                                             invisible=True, transport=transport, name=name)
            # Everything else is a map object - generally an image
            else:
                autoDraw = True
                purpose = objectDictionary["Purpose"]
                if purpose.lower() == "delayed":
                    autoDraw = False
                    objectDictionary["Purpose"] = objectDictionary["Name"]
                purpose = objectDictionary["Purpose"]
                if purpose.lower() == "dragon":
                    self.establishDragonColor(objectDictionary)
                filename = objectDictionary["File"]
                objectCoord = coord
                coord = map.convertMapCoordinatesToStandard(objectCoord)
                theObject = MapImage(map, objectCoord, path=self.objectsPath, file=filename, name=name, transport=transport, autoDraw=autoDraw )
                # Used to label each darkness for finding on the map during debugging
                # if purpose.lower() == "darkness":
                #     labeling = Text(self.map.canvas, objectCoord, text=f"{name}:({objectCoord[0]},{objectCoord[1]})", font=("TKDefaultFont", 9), color="White",
                #      bindingallowed=False)
                #     labeling.interactive=False
                #     labeling.transport=True 
                #     labeling.invisibleObject=False
                #     labeling = Text(self.map.canvas, objectCoord[0], objectCoord[1]+12, text=f"Map:({coord[0]},{coord[1]})", font=("TKDefaultFont", 9), color="White",
                #      bindingallowed=False)
                #     labeling.interactive=False
                #     labeling.transport=True 
                #     labeling.invisibleObject=False
            map.canvas.update()
            self.connectFunctions(theObject, objectDictionary)

    def displayPostplayerObjects(self, map):
        # Add in each object that shows above the player so the player moves "behind" it without touching it
        for objectDictionary in self.postPlayerObjects:
            filename = objectDictionary.get("File", None)
            if filename is None: 
                pass
            coord = objectDictionary["Map"]
            if len(coord) == 0: continue    
            contentPath = self.quiz.dictionary["Objects Path"]
            file = objectDictionary["File"]
            transport = objectDictionary.get('Transport', False) # Can be traveled over like a path
            theObject = MapImage(map, coord, path=contentPath, file=file, transport=transport )
            # Post-player objects cannot be touched so they have no functions to connect: self.data.connectFunctions(theObject, objectDictionary)
        map.canvas.update()

    def returnClassfrom(self, kindOfNpc):
        """Return the class to use for the NPC, if it exists."""
        classToUse = None
        if kindOfNpc == "Dragon":
            classToUse = DragonClass
        elif kindOfNpc == "Troll":
            classToUse = TrollClass

        # Check for the name of the NPC
        else:
            for objectDictionary in self.objects:
                if objectDictionary['Name'] == kindOfNpc:

                    # OK, determine what it is
                    purpose = objectDictionary.get('Purpose', None)
                    special = objectDictionary.get('Special', None)
                    if purpose is not None and special is not None:

                        # Match the name to the class
                        className = special + purpose + "Class"
                        match className:
                            case "SleepingSpiderClass":
                                classToUse = SleepingSpiderClass
                            case "AttackingSpiderClass":
                                classToUse = AttackingSpiderClass
                            case "DefendingSpiderClass":
                                classToUse = DefendingSpiderClass
                            case "IgnoringSpiderClass":
                                classToUse = IgnoringSpiderClass
                            case "ScreamingSpiderClass":
                                classToUse = ScreamingSpiderClass
                        break
        return classToUse

    def initializeDarkness(self, itemDictionary):
        anyPurpose = itemDictionary.get("Purpose", None)
        if anyPurpose == "Darkness":
            darknessName = itemDictionary["Name"]
            itemDictionary.setdefault("Action", "Darkness")
            itemDictionary.setdefault("Map",darknessName)
            itemDictionary.setdefault("File",darknessName)
            itemDictionary.setdefault("Room",darknessName)
            itemDictionary.setdefault("Transport", False)
            itemDictionary.setdefault("Description"," ") # Will be the room desciption

    def initializeTreasure( self, itemDictionary):
        treasurePurpose = itemDictionary.get("Purpose", None)
        if treasurePurpose == "Treasure":
            itemDictionary.setdefault("Name", "RANDOM")
            itemDictionary.setdefault("File", "RANDOM")
            itemDictionary.setdefault("Purpose", "Treasure")
            itemDictionary.setdefault("Action","Question")  
            itemDictionary.setdefault("Map",[])
            itemDictionary.setdefault("Room", False)
            itemDictionary.setdefault("Transport", False)
            itemDictionary.setdefault("Activate", False)
            itemDictionary.setdefault("Use",'Treasure')
            itemDictionary.setdefault("Question","Question") # Replace with question code
            itemDictionary.setdefault("Description",'NORMAL') # Can be a dictionary with optional keys description, content, namedDescription, namedContent
            itemDictionary.setdefault("Message",'')

    def exchangeObjectKeywords(self, itemDictionary):
        """Certain dictionary keys have values exchanged for a different value"""
        if itemDictionary["Name"] == "RANDOM": # We have a randomly selected object
            objectDescriptionList = self.vocab.selectRandomNamesFromList("random_object")
            if len(objectDescriptionList) > 0:
                description = objectDescriptionList[0].strip()
                itemDictionary["Name"] = f'Random Object {itemDictionary["Id"]}'
                itemDictionary["File"] = None # Random objects don't have files to display, just their text
                locationText = "{0} you {1} " + description
                newDescription = self.vocab(locationText, "adv_object_location,adv_object_finding")
                itemDictionary["Description"] = newDescription

        # Non-random objects can have standard descriptions or specific descriptions based on their purpose or name
        else:
            description = itemDictionary["Description"]
            purpose = itemDictionary["Purpose"]
            name = itemDictionary["Name"]

            # Specialty Objects - NPC
            if description == "NPC":
                descriptionName = purpose.lower().strip()
                itemDictionary["Description"] = " There is a "+descriptionName+" called "+name+" in there. "

            elif description == "STANDARD_OBJECT":
                if name.lower() == "random_object":
                    useDescription = self.vocab.makeObjectDescription(itemDictionary)
                    itemDictionary["Description"] = useDescription.strip()
                else:
                    useDescription = self.vocab.makeStandardDescription(purpose)
                    #itemDictionary["Description"] = useDescription.strip()
            elif isinstance(description, str) and description[:9] == "STANDARD_":
                descriptionName = name.lower().strip()
                newDescriptionName = descriptionName.replace(" ","_") # Make sure it is a valid name
                definitionParameters = "standard_" + newDescriptionName
                itemDictionary["Description"] = self.vocab(newDescriptionName, 
                                        definition=definitionParameters, 
                                        content=definitionParameters )
        pass

    def exchangeTreasureKeywords(self, itemDictionary):
        """Certain dictionary keys have values exchanged for a different value"""
        description = itemDictionary["Description"]
        name = itemDictionary["Name"]
        file = itemDictionary["File"]

        # Random treasures - get a random name
        if name.upper() == "RANDOM":
            newKindList = self.vocab.selectRandomNamesFromList("treasure_type")
            if isinstance(newKindList, list):
                name = newKindList[0]
            else:
                name = newKindList
            fileName = name
            potionFound = name == "potion"

            # If this random name has sub-types, get one of those
            treasureSubtypeFound = self.vocab.findNameInList(name, "treasure_subtypes")
            if treasureSubtypeFound:
                treasureSubtype = f"{name}_subtypes" 
                treasureSubtypeName = self.vocab.selectRandomNamesFromList(treasureSubtype)
                if isinstance(treasureSubtypeName, list):
                    fileName = treasureSubtypeName[0] + " " + name.capitalize()
                else:
                    fileName = treasureSubtypeName + " " + name.capitalize()

                # Some treasures have specific names which are not file names
                if fileName.startswith("Small "):
                    name = fileName[6:]
                else:
                    name = fileName

            # We have our random treasure
            itemDictionary["Name"] = name
            itemDictionary["File"] = fileName

            # Potions may have questions once selected from the badge
            if potionFound:
                itemDictionary["Action"] = "pickupPotion"
                itemDictionary["Purpose"] = "Question"
                itemDictionary["Description"] = self.vocab.makeNormalDescription("potion", standard=True)

        elif file.upper() == "RANDOM":
            itemDictionary["File"] = name

        file = itemDictionary["File"]
        dot = file.find(".")
        if dot < 0: itemDictionary['File'] = f"{file}.png"
        
        if isinstance( description, str) and len(description) > 0:
            standard = (description == "STANDARD")
            if description != "NPC":
                itemDictionary["Description"] = self.vocab.makeNormalDescription(name, standard=standard)
        elif isinstance(description, dict):
            descriptionName = name.lower().strip()
            newDescriptionName = descriptionName.replace(" ","_") # Make sure it is a valid name
            definitionParameters = newDescriptionName # "standard_" + newDescriptionName
            itemDictionary["Description"] = self.vocab(newDescriptionName, 
                                    definition=definitionParameters, 
                                    content=definitionParameters )
  
    def findMapObject( self, name=None, treasure=None, map=None, first=True):
          """Find an object in the map by its name, treasure, or map location."""
          response = []
          for eachObject in self.objects:
              if name is not None and eachObject["Name"] == name:
                  response.append(eachObject)
                  if first: break
              elif treasure is not None and eachObject["Purpose"] == "Treasure" and eachObject["Name"] == treasure:
                  response.append(eachObject)
                  if first: break
              elif map is not None and eachObject["Map"] == map:
                  response.append(eachObject)
                  if first: break

          if len(response) == 0:
              return None
          elif len(response) == 1:
              return response[0]
          else:
              return response

    def saveScrollInformatioin(self, map):
        scrollInfo = MapScrollInformation(map) # Save map parameters in class functions
        self.mapScrollDictionary[scrollInfo.name] = scrollInfo
        pass
    
    def loadScrollInformation(self, map):
        usingMapInfo = self.mapScrollDictionary.get(map.mapImageName, None)
        if usingMapInfo is not None:
            map.loadScrollInformation(usingMapInfo) # Set map parameters
            del self.mapScrollDictionary[map.mapImageName]
        
    ############### Map and Objects Connection ##############
  
    def connectMapAndObjects(self, **kwargs):
        """Called from the main class once maps are ready to be connected to.  kwargs are any additional resources to save"""
        self.resources.update(kwargs)
        self.loadMapCoordinates() 
        self.connectRoomsAndActivity()

    def loadMapCoordinates(self): 
        # Loop through all objects and match them with a room or placement somewhere.
        for objectDictionary in self.objects:
            mapPosition = objectDictionary["Map"]
            if type(mapPosition) is list:
                if len(mapPosition) == 2:
                    objectDictionary["StandardMap"] = mapPosition
                    objectDictionary["Map"] = self.map.convertStandardToMapCoordinates(mapPosition)
                    continue
                mapPosition = mapPosition[0] if len(mapPosition) == 1 else ''
                altName = "Monster" if objectDictionary["Purpose"] in ["Spider","Troll","Rous"] else ''
                purpose = objectDictionary["Purpose"]

            found,roomDictionary = self.matchingKeyFromDictionary(objectDictionary, placesKey='Room', matches=mapPosition)
            if not found: 
                found,roomDictionary = self.matchingKeyFromDictionary(objectDictionary,  placesKey='Use', matches=mapPosition, changeToUsed=True)
            if not found: 
                if purpose == "invisible": 
                    continue # Invisible don't need anything below
                found,roomDictionary = self.matchingKeyFromDictionary(objectDictionary, placesKey='Use', matches=altName, changeToUsed=True)
            if not found: 
                found,roomDictionary = self.matchingKeyFromDictionary(objectDictionary, placesKey='Use', matches=purpose, changeToUsed=True)

            # Second attempt looking for Used places
            if not found: 
                found,roomDictionary = self.matchingKeyFromDictionary(objectDictionary,  placesKey='Use', matches='Any', changeToUsed=True)
            if not found: 
                found,roomDictionary = self.matchingKeyFromDictionary(objectDictionary,  placesKey='Use', matches='Used', changeToUsed=True)
            if found:
                objectDictionary["Room"] = roomDictionary["Room"]
                objectDictionary["StandardMap"] = roomDictionary["Map"]
                objectDictionary["Map"] = self.map.convertStandardToMapCoordinates(roomDictionary["Map"])
                objectDictionary["Room Dictionary"] = roomDictionary
            
            pass

    def connectRoomsAndActivity(self):
        """Loop through all objects and treasure and place their dictionary into their room's content list"""

        # Loop through all objects and treasure and place their dictionaries into their room's content list
        for roomObjectDictionary in self.objects:
            roomName = roomObjectDictionary["Room"]
            if roomObjectDictionary["Is a Room"] and len(roomName) > 0:
                theContentRoomList = roomObjectDictionary["Contents"]

                # Check and add any objects in the room
                for eachObjectDictionary in self.objects:
                    if eachObjectDictionary["Id"] == roomObjectDictionary["Id"]: continue
                    if  roomName == eachObjectDictionary["Room"]:
                        theContentRoomList.append(eachObjectDictionary)
                roomObjectDictionary["Contents"] = theContentRoomList
        pass

        # Link any activation for each object 
        # Loop for all objects
        for eachObjectDictionary in self.objects:

            # Make a backup copy of the original map
            linkContentRoomList = eachObjectDictionary.get("Contents", [])

            # Check if the object activates another object
            activate = eachObjectDictionary.get("Activate",None)
            if activate is None: continue
            if type(activate) == str and len(activate) > 0:

                # It does, there may be several. Process each object using its name.
                objectList = activate.split(",")
                for eachObjectName in objectList:

                    # Check for NPC (Non-Player Characters) which are distinct from objects with a 
                    # simples series of one-shot or repeating functions.
                    npc, kindOfNpc = self._extractParameter(eachObjectName)
                    if npc == "NPC" and kindOfNpc is not None and len(kindOfNpc) > 0:
                        eachObjectDictionary["NPC"] = kindOfNpc

                    # Otherwise find that object to-be-activated by name. The object will call .activate()
                    else:
                        # Search all objects to find the on(s) to link their activation
                        for objectToActivate in self.objects:

                            # Find an object with the matching name to this name
                            if objectToActivate["Name"] == eachObjectName:

                                # We have a match, add a unique object to the content list of this object
                                duplicateFound = False
                                for existingObject in linkContentRoomList:
                                    if existingObject["Name"] == eachObjectName:
                                        # If the object is already in the room, then don't add it again
                                        duplicateFound = True
                                        break
                                if not duplicateFound: eachObjectDictionary["Contents"].append(objectToActivate)
                                break
                
            # Check if the object modifies another object
            modify = eachObjectDictionary.get("Modify", None)
            eachObjectDictionary["Modify"] = []
            if modify is None: continue
            if type(modify) == str and len(modify) > 0:
                
                # It does, there may be several. Process each object using its name.
                objectList = modify.split(",")
                for eachObjectName in objectList:
                    nameOfMethod, objectName = self._extractParameter(eachObjectName)
                        
                    # Search all objects to find the one to link the method calling it
                    for objectToModify in self.objects:

                        # Find an object with the matching name to this name
                        if objectToModify["Name"] == objectName:
                            currentModifyFuncion = self.findFunctionbyName(nameOfMethod)
                            if currentModifyFuncion is not None:
                                modifyTuple = (currentModifyFuncion,objectToModify)
                            eachObjectDictionary["Modify"].append(modifyTuple)
                    
                pass

    def matchingKeyFromDictionary(self, specificfObjectList, placesKey, matches, changeToUsed=False):
        """Using the specific object list, look for a matching value in the matching key in the places dictionary list.
        When we are done, each object that has a room has been linked to that room. Some objects don't have rooms."""
        found = False
        foundDictionary = None

        # Loop until there is a match
        if matches is not None and type(matches) == str and len(matches) > 0:
            length = len(self.places)
            for index in range(length):
                dictionaryFromPlaces = self.places[index]
                lookingAtKey = dictionaryFromPlaces.get(placesKey,None)
                if lookingAtKey is None or len(lookingAtKey) == 0: continue # No key to match
                if dictionaryFromPlaces.get("Use",None) == "Full": continue # Not available for use as it has been use to the fullest

                # Check for a match. Note some keys are not the room name but some other text, like "Secret Door A".
                if  lookingAtKey == matches: 
                    found = True
                    foundDictionary = dict(**dictionaryFromPlaces )
                    foundDictionary["Room Dictionary"] = dictionaryFromPlaces

                    # If we have a match but the places dictionary does not have a room, then look for the room in a different manner
                    foundRoom = foundDictionary.get('Room','')
                    if foundRoom == '':

                        # Search for a matching key in the USE key of dictionaries in the places dictionary list
                        placeId = dictionaryFromPlaces['Id'] # But don't include the dictionary that already matched
                        for eachRoomDictionary in self.places:
                            if placeId == eachRoomDictionary['Id']: continue

                            # When there is a match, store the room and dictionary so all the information is available
                            if eachRoomDictionary['Use'] == matches:
                                foundRoom = eachRoomDictionary.get('Room', '')
                                foundDictionary["Room"] = foundRoom
                                #foundDictionary["Room Dictionary"] = eachRoomDictionary
                                break

                    # Limit the use of this place if requested
                    if changeToUsed:
                        current = self.places[index]["Use"]
                        match current:
                            case "Full":
                                newValue = "Full"
                            case "Used":
                                newValue = "Full"
                            case _:
                                newValue = "Used"
                        self.places[index]["Use"] = newValue
                    break
        return found,foundDictionary
     
    def noMoreQuestionsMessage(self, *args ):
        self.statusBar.set('No more questions, they all were answered!')
        return # Better to send a status bar message or return a question object with a message?

    def getQuestion(self, tags='Title', name=None, useMissedQuestions=False):
        """Get a random question from the list of questions or when they run out any missed questions unless
        a specific title of a question is requested or no recycling of missed questions.  An NPC such as
        a dragon may pull questions off of the missed list first, then get new question (or just missed)."""
        question = None

        # Check if questions are available, if not then recycle missed questions (if allowed)
        if len(self.questions) == 0:
            if len(self.missedQuestions) == 0:
                return None # Nothing left
                
            elif self.recycleMissedQuestions == "Recycle":
                self.questions.extend(self.missedQuestions)
                self.missedQuestions.clear()
            elif self.recycleMissedQuestions == "Recycle One":
                question = self.missedQuestions.pop()
                self.questions.append(question)
            else:
                return None

        # Determine which question list to use
        if useMissedQuestions:
            if len(self.missedQuestions) == 0:
                return None
            usedQuestionList = self.missedQuestions
            alternativeList = self.questions
        else:
            usedQuestionList = self.questions
            alternativeList = self.missedQuestions

        # Get a random question or a specific question by name (check both lists)
        if name is None:
                question = usedQuestionList.pop()
        else:
            for index, question in enumerate(usedQuestionList):
                if question[tags] == name:
                    question = usedQuestionList.pop(index)
                    break
            if question is None:
                for index, question in enumerate(alternativeList):
                    if question[tags] == name:
                        question = alternativeList.pop(index)
                        break
        self.lastQuestion = question
        return question

    def saveMissedQuestion(self):
        """Add the last question to the list of missed questions."""
        if self.lastQuestion is not None:
            self.missedQuestions.append(self.lastQuestion)
            self.lastQuestion = None

    def connectFunctions(self, theObject, objectDictionary):
        # Called from MapClass: displayPreplayerObjects
        # Combine the newly minted object with a question from the big question dictionary.  

        if self.questionArea is None:
            self.questionArea = self.getResources('questionArea')  # Just make sure it is current
        theObject.data = self # NOTE: Connect every object back to data - bad policy
        objectDictionary["MapObject"] = theObject  # Store the object in the dictionary for later use
        theObject.dictionary = objectDictionary

        # Link all NPCs (separate from Activate as those are not NPCs)
        usingNPC = theObject.dictionary.get("NPC",None)
        if usingNPC:
            self.linkNPC(theObject, objectDictionary)

        # Save each action into the object as a function
        self.convertActionsToFunctions(theObject)
              
    def linkNPC(self, theObject, objectDictionary):
        # if this is the NCP itself, then establish it
        usingNPC = theObject.dictionary.get("NPC",None)
        if usingNPC == objectDictionary['Name']:
            if not hasattr(theObject, 'NPC'):
                classToUse = self.returnClassfrom(usingNPC)
                if classToUse is not None:
                    theObject.NPC = classToUse(self, objectDictionary)
                    if theObject.dictionary["Boss"]:
                        self.boss = theObject.NPC
                else:
                    self.logError(f"Error: No class found for NPC {usingNPC}.") 
                    theObject.NPC = None
            if theObject.NPC: theObject.addAction(theObject.NPC.activate)
        # This object refers to the NCP, so link to it 
        else:
            for eachObject in self.objects:
                if eachObject["Name"] == usingNPC:
                    mapObjectNPC = eachObject["MapObject"]
                    theObject.NPC = mapObjectNPC.NPC
                    theObject.addAction(theObject.NPC.activate)
                    break   
                                 
    # Save each text action into the object as a function
    def convertActionsToFunctions(self, theObject):
        # Save each action into the object as a function
        action = theObject.dictionary.get("Action", None)
        actionList = self._extractIndividualActions(action) ### <--- Extract action info
        if actionList is None: return
        for actionTuple in actionList:
            actionName, parameter = actionTuple
            if actionName is None or len(actionName) == 0: continue
            if type(actionName) == callable:
                theObject.addAction(actionName)
            elif type(actionName) == str:
                checkUsingName = actionName.lower()

                if checkUsingName == "question":
                    newAction = self.questionFunction
                    theObject.addAction(newAction) # This action retrieves & sets up graphics for the question
                else:
                    newAction = self.retrieveFunctionFromAction(theObject, actionName, parameter)  ### <--- Retrieve the function from the action name
                    theObject.addAction(newAction) 
                        
    def missedQuestionStatus(self):
        status = len(self.missedQuestions) > 0
        return status

    def noMoreQuestions(self):
        result =  len(self.questions) == 0 and len(self.missedQuestions) == 0
        return result
    
    def initializeTorches(self, initialTorches):
        now = datetime.datetime.now()
        self.startTime = now
        self.torches = initialTorches
        if self.initialTorches > 0: # Extra torches previously allotted to student
            self.torches = int(1 + self.initialTorches*initialTorches)
        self.initialTorches = int(initialTorches) # Force int if a percent or float was here
        player = self.getResource("player")
        player.history['Torches_Left'] = initialTorches
        player.inventory.append('Torch')
        badges = self.getResource("badges")
        badges.addIcon('Torch', PlayerClass.TYPE_TORCH, amount=initialTorches)

    def torchChange(self, amount):
        now = datetime.datetime.now()
        self.startTime = now
        self.torches = amount
        self.initialTorches = amount
        self.updateTorch()

    def provideMoreTorches(self, amount):
        if self.torches > 0:
            self.torches = int(1 + amount *self.torches)
            self.updateTorch()
        else:
            self.initialTorches = amount

    def updateTorch(self, *args):
        if self.torches >= 0:
            player = self.getResource("player")
            player.history['Torches_Left'] = self.torches
            badges = self.getResource("badges")
            badges.addIcon('Torch', PlayerClass.TYPE_TORCH, amount=self.torches)
            if self.torches > 0:
                instructions = self.getResource('instructions')
                instructions.add(f"\n<Red> A torch went out, using torch #{self.torches}!>")
            elif self.torches == 0:
                self.torches = -1
                self.root.after( 100, self.exitGameBox )
                
    def torchCheck(self, *args):
        if self.torches > 0:
            currentTime = datetime.datetime.now()
            difference = currentTime - self.startTime
            minutes = int(difference.total_seconds()//60)
            torchesLeft = int(self.initialTorches - minutes)
            if torchesLeft != self.torches:
                self.torches = torchesLeft
                self.updateTorch()
            
    def condenseList(self, theList):
        """Condense a list by removing None entries and eliminating lists in lists"""
        if theList is None: return []
        if not isinstance(theList,list): return [theList]
        newList = []
        for eachItem in theList:
            if eachItem in ([],()): 
                resultList = self.consenseList(eachItem) # Recursive
                for eachSubItem in resultList:
                    newList.append(eachSubItem)
            elif eachItem is None: 
                continue
            else:
                newList.append(eachItem)
        return newList
                
    def convertFromString(self, value, replaceSlash=False):
        """Convert a string into its intended type"""
        # Only strings with contents are converted here
        if not type(value) == str: return value
        string = value.strip()
        if len(string) == 0: return value

        # Booleans of true or false
        if string.lower() == "true":
            returnValue = True
        elif string.lower() == "false":
            returnValue = False

        else:
            returnValue = string # Default return value

            # Removing outer layer of quotes
            firstLetter = string[0]
            if (firstLetter == "'"  or firstLetter == '"') and string[-1] == firstLetter:
                returnValue = string[1:-1] 

            # Check for a decimal or integer value
            elif(firstLetter.isnumeric() or firstLetter == "+" or firstLetter == "-"):
                if string.find('.') >= 0:
                    try:
                        returnValue = float(string)
                    except:
                        pass
                else:
                    try:
                        returnValue = int(string)
                    except:
                        pass
            
            # Still unchanged, must be a real string, check to replace unneeded slashes
            elif replaceSlash:
                """ Replace any double slash \\ with / for comparisons, remove any \n ending"""
                length = len(string) - 1
                returnValue = ""
                for count,letter in enumerate(string):
                    if letter == "\\":
                        returnValue += "/"
                    elif letter == '\n':
                        if count < length: returnValue += "/n"
                    else:
                        returnValue += letter

        return returnValue
    
    def extractProblem(self, folderPath, file):
        """Extract a dictionary (in JSON format) and Python code from a .txt file."""
        jsonList,dictionary,code,returning,lines = [],{},"","",None
        
        # Atempt to open the problem and read in all its content into as list
        path = pathlib.Path(folderPath, file)
        try:     
            with open(path, "r") as f: 
                lines = f.read()
                lines = lines.splitlines(keepends=True)
        except:
            self.logError(f"Error: Unable to access {path} data which contains the JSON and code!")
        if lines is not None: 

            # Extract the code, answer, and the JSON. The code is fine as it is.
            braceFound = False
            jsonFound = False
            returnFound = False
            for eachLine in lines:
                line = eachLine.strip()
                if line.startswith("---------"):
                    returnFound = True
                    continue
                if returnFound:
                    dataPoints = eachLine.split(",")
                    returningLine = ""
                    length = len(dataPoints) - 1
                    for count,dataPoint in enumerate(dataPoints):
                        returningLine += dataPoint.replace("'","").replace('"',"").strip()
                        if count < length: returningLine += ","
                    returning = returning + returningLine + "\n"
                    continue
                if jsonFound:
                    code += eachLine
                    continue
                if not braceFound and len(line) > 0:
                    if line[0] == "{":
                        braceFound = True
                        continue
                if braceFound:
                    if len(line) > 0 and line[0] == "}":
                        jsonFound = True
                        continue
                    if line[-1] == '\n': line = line[:-1] # Remove newline character
                    jsonList.append(line)  
                
            # Everything was searched, now parse the JSON into a dictionary and save any answer
            for line in jsonList:
                element = line.split(':')
                if len(element) == 2 and len(element[0]) > 0 and len(element[1]) > 0:
                    key = element[0].strip().replace('"','').replace("'","")
                    value = element[1].strip()
                    if value[-1] == ',': value = value[:-1]
                    firstLetter = value[0]
                    if firstLetter in ['[','{','(']:
                        if firstLetter == '[':
                            collection = []
                        elif firstLetter == '(':
                            collection = ()
                        else:
                            collection = {}
                        if len(value) > 2:
                            listing = value[1:-1].split(',')
                            for item in listing:
                                eachItem = self.convertFromString(item)
                                if firstLetter == '[':
                                    collection.append(eachItem)
                                elif firstLetter == '(':
                                    collection.append(eachItem)
                                else:
                                    dictionaryList = eachItem.split(':')
                                    if len(dictionaryList) == 2:
                                        collection[dictionaryList[0]] = dictionaryList[1]
                        dictionary[key] = collection        
                    else:
                        value = element[1].strip().replace('"','').replace("'",'')
                        if value[-1] == ',': value = value[:-1]
                        dictionary[key] = self.convertFromString(value)
                        
            # Get the name and filename and set them
            parts = file.split('.')
            namePart = parts[0]
            parts = namePart.split('_')
            number = parts[1]
            if number[0] == '0': number = number[1:]
            finalName = parts[0] + ' #' + number
            dictionary.setdefault('Name', finalName)
            dictionary.setdefault('File', file)
            
            # Code, Return, and Answer can be in the dictionary or specifically listed
            if len(code) == 0: code = dictionary.get("Code", "")
            dictionary.setdefault("Answer", None) # Optional, expected user answer to get the return
            dictionary.setdefault("Return", returning) # Return value for any language
            
            # Insure the dictionary has all optional keys (some missing keys are OK)
            dictionary.setdefault("Language", "Python")
            dictionary.setdefault("Category", dictionary["Language"])
            dictionary.setdefault("Reward", "")
            dictionary.setdefault("Penalty", "")
            dictionary.setdefault("Imports", "")
            dictionary.setdefault("Required", [])
            dictionary.setdefault("Exclude", [])
            dictionary.setdefault("Parameters",[])
            dictionary.setdefault("Dictionary",{})
            dictionary.setdefault("Variables", "")
        return dictionary, code
    
    def questionFunction(self, *args, **kwargs):
        """ Function to create a question form based on the question dictionary processed above
        Return a function that will set up the question and process it. Handled differently from a plain object.
        Plain objects have actions saved in their action list, but questions have a several functions to store.
        They are success, failure, and second try.  One or more of these may be its own question.  The question in
        the question class is overwritten with a list of function calls or the text of the question.  
        Additionally, a radio question can be a 'discussion' where each answer has its own called function."""

        # Return if incomplete provisions
        if len(args) == 0: return None
        mapObject = args[0]
        if mapObject is None: return None
                
        # Manual check on timing, torches have not been accurate
        if kwargs.get("torchCheck",True): self.torchCheck()

        # If the mapObject already has a question in it, no need to get a random question.
        # This allows for NPC to ask their own questions, such as a dragon or troll.
        # Set mapObject.questionFunctionsInitialized = True if the question is already set up (see below).
        if mapObject.question is None:
            useMissedQuestions = kwargs.get('useMissedQuestions', False)
            question = self.getQuestion(useMissedQuestions=useMissedQuestions)  # Get a random question from the list of questions
            if question is None or len(question) == 0:
                self.noMoreQuestionsMessage()
                mapObject.undraw()
                return None
        else:
            question = mapObject.question
            
        # Check if a file holds additional information
        file = question.get('File', None)
        if file is not None:
                    
            # Problem location
            if (quiz := self.getResource("quiz")):
                problemFolder = quiz.get("Problem Folder","Problems")
            else:
                problemFolder = "Problems"
            problemPath = pathlib.Path(os.path.join(os.getcwd(), problemFolder))
            problemQuestion, code = self.extractProblem( problemPath, file )
            problemQuestion["Code"] = code
            theName = question.pop('Name', "")
            theTitle = question.pop('Title', "")
            problemQuestion.update(question)
            checkingTitle = problemQuestion.get("Title","")
            if len(checkingTitle) == 0 :  problemQuestion["Title"] = theTitle
            checkingName = problemQuestion.get("Name","")
            if len(checkingName) == 0 :  problemQuestion["Name"] = theName
            question = problemQuestion
            mapObject.question = problemQuestion 
            usesSuccess = problemQuestion.get("Success", None) # Code might be usingSuccess, not reward
            if usesSuccess is not None: 
                reward = question.get("Reward",None)
                if reward is None or reward == False or reward == "":
                    question["Reward"] = usesSuccess
            
        if ( player := self.getResource("player")):
            player.lastQuestionObject = mapObject

        # Trying a question again - a Gold question a second time could be worth a Silver reward
        useSecondTry = question.get('Second Try',None) 
        if useSecondTry is None or ( isinstance(useSecondTry,str) and len(useSecondTry) == 0):
            useSecondTry = False
        mapObject.tries = 1 if not useSecondTry else 2

        # If we are answering again, the following were already set
        if not mapObject.questionFunctionsInitialized:
            mapObject.questionFunctionsInitialized = True

            # Get the text forms of the reward/penalty functions
            reward = question.get("Reward", None)
            if len(reward) == 0: reward = None
            penalty = question.get("Penalty", None)
            if len(penalty) == 0: penalty = None
            numberTwo = question.get("Second Try", None)

            if numberTwo is None:
                secondTry = None
            elif type(numberTwo) == str and len(numberTwo) > 0:
                secondTry = numberTwo
            else:
                secondTry = None
            ##secondTry = None if numberTwo is None else numberTwo if type(numberTwo) == str and len(numberTwo) > 0 : None

            # Get the actual success & failure possible functions based on the values in the question
            # First, determine the Success action results back into the question
            successTuple = self.returnRewardFunctions(reward)
            successReward = successTuple[0]
            successPenalty = successTuple[1]
            if reward is None:
                question['Success'] = self.condenseList([self._successfulQuestion])
            elif question.get("ProvidedObject",True): 
                question['Success'] = self.condenseList([successReward, self.fade, self._successfulQuestion])
            else:
                question['Success'] = self.condenseList([successReward, self._successfulQuestion])
                
            # Second, determine the Failure action results back into the question
            penaltyTuple = self.returnRewardFunctions(penalty)
            penaltyPenalty = penaltyTuple[1]
            if penalty is None:
                question['Failure'] = self.condenseList(self._failedQuestion)
            elif mapObject.noFailure:
                question['Failure'] = self.condenseList([successPenalty, penaltyPenalty,])
            else:
                question['Failure'] = self.condenseList([successPenalty, penaltyPenalty, self._failedQuestion ])
                
            # Third, any second try
            secondTryResult = self.returnRewardFunctions(secondTry)
            question['Second Try'] = secondTryResult

            # Treasures can provide multiple attempts or questions, so we need to know if the treasure is kept or not
            mapObject.keepTreasure = question.get("Keep Treasure",False)
            if not mapObject.keepTreasure: 
                if not mapObject.noFailure:
                    question['Failure'].append(self.disappear)

            ### WE HAVE OUR QUESTION ###
            mapObject.question = question  
            
        # Ready to implement the question
        # if ( instructions := self.getResource("instructions")):
        #     text = f"\nQuestion asked: {mapObject.question["Title"]}.  "
        #     instructions.newSection(text)
        self.questionArea.implementQuestion(mapObject)
        
    def returnRewardFunctions(self, *args):
        """Return the reward and penalty functions based on the action name provided.
        Arguments must be: [0]: reward and optionally [1,2]: penalty, the object, and the optionally [3]: a parameter
        The most common rewards and penalties are for coins plus fade and disappear."""
        rewardList = []
        penaltyList = []
        if len(args) > 0:
            argument_1 = args[0]
            if argument_1 is None or ( type(argument_1) == str and len(argument_1) == 0):
                return None, None

            # One parameter which may be a comma-separated list of rewards
            if len(args) == 1:
                argumentList = argument_1.split(",")
                actions = []
                for theReward in argumentList:
                    if theReward is None: continue
                    if type(theReward) == callable: 
                        actions.append( theReward, None )
                        continue

                    # Coin based rewards and penalties. Sometimes the penalty is returned but ignored
                    action = None
                    reward = theReward.lower()
                    if reward == "gold":
                        action =  self._addGoldPiece, self._removeGoldPiece
                    elif reward == "silver":
                        action =  self._addSilverPiece, self._removeSilverPiece
                    elif reward == "copper":
                        action =  self._addCopperPiece, self._removeCopperPiece
                    elif reward == "fade":
                        action =  self.fade, self.fade
                    elif reward == "disappear":
                        action =  self.disappear, self.disappear
                    elif reward[:7] == "bounty;":
                        action =  self._addBounty, self._removeBounty 
                    elif reward[:9] == "sterling;":
                        action =  [self._addSterling,self._removeSterling], None

                    # Search all the other functions for the reward or penalty. Results can be lists of multiple actions.
                    else:
                        action = self.retrieveFunctionFromAction(self, theReward, theReward), None

                    # Rewards and penalties are paired but might be ignored by the calling function.
                    if action is not None:
                        rewardList.append(action[0])
                        penaltyList.append(action[1])
                
                # Return values determined to make it easy for the calling function to use
                if len(rewardList) == 0:
                    return None, None
                elif len(rewardList) == 1:
                    return rewardList[0], penaltyList[0]
                else:   
                    return rewardList, penaltyList

            # Two parameters, the first is the reward, the second is the penalty
            elif len(args) == 2:
                reward = self.retrieveFunctionFromAction(self, argument_1, argument_1)
                penalty = self.retrieveFunctionFromAction(self, args[1], args[1])
                return reward, penalty

            else:
                # Look for something in the full list of functions, but extra arguments needed to be provided
                thePenalty, currentObject = args[1], args[2]
                parameter = args[3] if len(args) >= 4 else None
                reward = self.retrieveFunctionFromAction(self, currentObject, argument_1, parameter=parameter)
                penalty = self.retrieveFunctionFromAction(self, currentObject, thePenalty, parameter=parameter)
                return reward, penalty
            
        return None, None                
    
    def updateQuestionDictionary(self, originalDictionary, index=0, name='Unknown', typeOfQuestion=None ):
        """ Set missing values in the question dictionary to defaults based on the type of question."""
        dictionary = dict()
        dictionary.update(originalDictionary)  # Make a copy of the dictionary
        if typeOfQuestion is None:
            typeOfQuestion = dictionary.get("Type", "Multiple Choice")

        # These are required of other keys
        dictionary.setdefault("Name", name)
        dictionary.setdefault("Type",typeOfQuestion)
        options = dictionary.get("Options","") # Not all questions use Options
        answer = dictionary.get("Answer",None)
        if answer is None:
            if isinstance(options, list):
                    answer = options[0]
            else:
                answer = options
        elif isinstance(answer,str): #Answer can be an integer
            if len(answer) == 0:
                if isinstance(options, list):
                        answer = options[0]
                else:
                    answer = options

        dictionary.setdefault("Id", index)
        dictionary.setdefault("Title", name)
        dictionary.setdefault("Search Tags", name)
        dictionary.setdefault("Second Try", "")
        dictionary.setdefault("Keep Treasure", False)
        dictionary.setdefault("Treasure", "")
        dictionary.setdefault("Reward", "")
        dictionary.setdefault("Penalty", "")
        dictionary.setdefault("Failure", "")

        # Optionals based on type of question
        if typeOfQuestion == "Popup":
            dictionary.setdefault("Instructions", "Select just one:")
            dictionary.setdefault("Answer", answer)

        elif typeOfQuestion == "Multiple Choice":
            dictionary.setdefault("Instructions", "Select just one:")
            dictionary.setdefault("Answer", answer)

        elif typeOfQuestion == "Radio Buttons":
            dictionary.setdefault("Instructions", "Select just one:")
            dictionary.setdefault("Answer", answer)

        elif typeOfQuestion == "Yes or No":
            dictionary.setdefault("Instructions", "Answer with either a Yes or No")
            dictionary.setdefault("Options", ["Yes","No"] )
            dictionary.setdefault("Answer", answer)

        elif typeOfQuestion == "True False" or typeOfQuestion == "True/False":
            dictionary.setdefault("Instructions", "Select True or False")
            dictionary.setdefault("Options", ["True","False"])
            dictionary.setdefault("Answer", answer)
            
        elif typeOfQuestion == "Check Box":
            dictionary.setdefault("Instructions", "Select all that apply")

        elif typeOfQuestion == "Table": # Which is much different from the others
            dictionary.setdefault("Instructions", "Select from all popus")
            dictionary.setdefault("TableName", "Table")
            dictionary.setdefault("Table", [])
            dictionary.setdefault("Columns", [])
            dictionary.setdefault("Headers", [])
            dictionary.setdefault("Practice", False)
        elif typeOfQuestion == "Code Edit":
            pass
        return dictionary

    def updateOptionalQuestionKeys(self, ordered=None):
        """Loop through all questions and update their dictionaries to include any missing keys."""
        newQuestionArray = []
        count = len(self.questions) + 1
        for index, dictionary in enumerate(self.questions):
            completedDictionary = self.updateQuestionDictionary(dictionary, index=index)
            if ordered != None:
                completedDictionary[ordered] = count
                count += 1
            newQuestionArray.append(completedDictionary)
        self.questions = newQuestionArray
 
    def createYourOwnQuestion(self, name, typeOfQuestion, **dictionary):
        """Create a question based on the arguments and dictionary provided.  Use the following keys:
        The Name and Type are manditory parameters. The remaining dictionary elements are:
        Options = list of possible answers to choose from
        Answer: The correct text answers
        Index: integer, not used for created questions but defaults to 0.  Manually use the length of the questions list if necessary.
        Title: Title provided
        Search Tags: defaults to the provided Name
        Reward: Name of the reward function, not needed if 'Success' function(s) provided
        Penalty: Name of the penalty function, not needed if 'Failure' function(s) provided
        Success: function(s) to call when the question is answered correctly
        Failure: function(s) to call when the question is answered incorrectly
        Second Try: function(s) to call when the question is answered incorrectly but a second try is allowed
        Keep Treasure: Optionally False, if True the object does not disappear after the question is answered.
        Treasure: name of the treasure's picture
        Instructions: Text to display with the question, defaults to what works for the generic type of question.
        The 'table' type of question has additional values that are not initialized here. Put them in manuualy with the dictionary elements."""

        # Manually set mapObject.questionFunctionsInitialized=True if actual function(s) were provide for Success and Failure.
        # If you provided names that are their function's names, do not set it but let the software find the functions.
        # The question is embedded into the mapObject 'asking' the question. Provided functions can affect that object.
        question = self.updateQuestionDictionary(dictionary, name, typeOfQuestion )
        return question
    
    # Record and retrieve history of player activity
    def recordHistory(self, **dictionary):
        self.player.recordHistory(**dictionary)
                    
    def getHistory(self, key, default=None):
        result = default
        if ( player := self.getResource("player")):
            result = player.getHistory(key,default)
        return result
    
    def getLastTouch(self):
        result = self.getHistory('Last_Touch')
        return result
    
    def setLastTouch(self, touchedObject):
        """Set the last touch to the provided touch."""
        self.recordHistory(Last_Touch=touchedObject)

    # Save the gameText into GameResult.txt in the parent of the run folder, or the temp folder
    def writeGameResult(self, *lines, includeErrors=False):
        
        # Save the gameText into a file named "GameResult.txt
        self._appendGameResult(lines)
            
        # At the end of the game, add to the game text any errors or message that were logged
        if includeErrors:
            if self.errorFile is not None and os.path.exists(self.errorFile):

                with open(self.errorFile, "r") as log_file:
                    logText = log_file.readlines()

                if len(logText) > 0:
                    errorLines = ["\n\nLOG MESSAGES AND ERRORS:\n"]
                    for text in logText:
                            if type(text) == str:
                                if len(text) == 0: continue
                            else:
                                text = str(text)
                            errorLines.append(text)
                    errorLines.append("\n")
                    self._appendGameResult(errorLines)

    def _appendGameResult(self, lines):
        """Append lines to the result file, switching to the temp folder if the current file cannot be saved."""
        try:
            result_file = open(self.gameResultFile, "a")
        except OSError:
            self._switchGameResultToTemp()
            result_file = open(self.gameResultFile, "a")
        with result_file:
            for text in lines:
                    if type(text) == str:
                        if len(text) == 0: continue
                        showText = text
                    else:
                        showText = str(text)
                    result_file.writelines(showText)
            result_file.writelines("\n")

    def _switchGameResultToTemp(self):
        """Move later saves to the temporary folder when the chosen result file cannot be written."""
        fallback = os.path.join(tempfile.gettempdir(), os.path.basename(self.gameResultFile))
        if os.path.normcase(os.path.abspath(fallback)) == os.path.normcase(os.path.abspath(self.gameResultFile)):
            return
        previous = ""
        try:
            with open(self.gameResultFile, "r") as existing:
                previous = existing.read()
        except OSError:
            previous = ""
        self.gameResultFile = fallback
        self.outputDirectory = os.path.dirname(fallback)
        if previous:
            with open(self.gameResultFile, "a") as result_file:
                result_file.write(previous)
            
##########  End-Game code ##############

    def recordIfGameCompleted(self):
        status = self.rewardBox.currentStatus()
        torchesGone = not status["torches"],
        noMoreQuestions = status["noMoreQuestions"] 
        enoughCoinsCollected = status["coinsCollected"]
        gameOver = torchesGone or noMoreQuestions or enoughCoinsCollected
        if gameOver: status["completed"] = True
        return gameOver
    
    def makeLastQuestion(self, returnFunction=None):
        nextFunction = self.exitGame if returnFunction == None else returnFunction
        question = self.quiz["Last Question"]
        reward = question.get("Reward",None)
        question['Reward'] = "exitGame" if reward is None else reward+",exitGame" 
        penalty = question.get("Penalty",None)
        question['Penalty'] = "exitGame" if penalty is None else penalty+",exitGame"
        question["Keep Treasure"] = False
        
        # Store the correct functions (self.questionFunction cannot get it right)
        successTuple = self.returnRewardFunctions(question['Reward'])
        penaltyTuple = self.returnRewardFunctions(question['Penalty'])
        question['Success'] = self.condenseList([successTuple[0], nextFunction])
        question['Failure'] = self.condenseList([penaltyTuple[1], nextFunction ])
        question['Second Try'] = None
        question['vertical'] = True
        
        # Setup a fake object to hold the question
        LastQuestionObject = LastQuestionClass(self, question=question )
        LastQuestionObject.keepTreasure = False
        LastQuestionObject.questionFunctionsInitialized = True
        self.questionFunction(LastQuestionObject, torchCheck=False)
        if ( instructions := self.getResource("instructions")):
            text = f'\nQuestion asked: {LastQuestionObject.question["Title"]}.  '
            text = self.vocab.cleanUpPunctuation(text)
            instructions.newSection(text)
        return LastQuestionObject

    def exitGameBox(self, *args, **wargs):
        # Ways to exit the game box and either return to the big map or the current game:
        # 1) The function was called from somewhere
        # 2) The player entered the exit box and it called this function
        # 3) Some random crash ends up here
        #
        # Ways to end the game
        # 4) Torches have run out
        # 5) There are no more questions
        # 6) Enough coins were once collected
        if self.getHistory("AlreadyExited") or self.startTime is None:
            return # Already exited once
        exitingIsAvailable = False
        
        status = self.rewardBox.currentStatus()
        if status["completed"]:
        
            # Check how game completed
            if status["noMoreQuestions"] or status["coinsCollected"]:
                exitingIsAvailable = True

            # You ran out of torches and completed the game
            elif status["torches"]:
                exitingIsAvailable = True
                self.returnToEntrance()

            # To get here a crash of some type happened
            else:
                self.statusBar.set("I don't know what just happened, but you cannot exit the game until you complete it!")
                self.stopMoving()

        # You just ran out of torches
        elif status["torches"]:
                exitingIsAvailable = True
                self.returnToEntrance()

        # Only exit once
        else: 
            lastObject = self.getLastTouch()
            exitBoxObject = self.findMapObject(name="ExitBox")
            if lastObject != exitBoxObject:
                # You can't leave early
                self.statusBar.set("You cannot exit the game until you complete it!")
                self.stopMoving()
                
        # Final determination
        if exitingIsAvailable:
            self.processExitFunction()
        else:
            return

    def setExitingFunction( self, exitingFunction):
        self.processExitFunction = exitingFunction

    def defaultReturn(self, *args):
        return
    
    def makeFinalCover(self, canvas, *args, **kwargs): 
        """ Create a cover over the entire canvas with a message.  Used when the game ends."""
        coords = canvas.getCanvasCoodinates()
        (x, y, height, width) = canvas.getFourDimensions(coords)
        text = kwargs.get('text', "Initializing")
        background = kwargs.get('background', "Black")
        self.coverMapCanvas = CoffeeCanvas.Canvas(self.canvas, x=x, y=y, width=width, height=height, background=background)
        CoffeeCanvas.Text(self.coverMapCanvas, width/2, height/2, text=text, font=("Papyrus", 20 ), color="White")   

    def removeFinalCover(self):
        if self.coverMapCanvas is not None:
            self.coverMapCanvas.undraw()
      
    def returnToEntrance(self, *args, **wargs):
        """When forced to return, specific graphics are set up. This can be called from 
        multiple places so only call once"""
        if (timers := self.getResource("timers")):
            timers.stop()
        self.makeFinalCover(self.map.canvas, text="Your torches have all burned out!")
        self.map.canvas.update()
        Sleep(4) # So they can read the message
        self.removeFinalCover()
        self.map.canvas.update()
        playerCoord = self.quiz.get("Target Location", (0,0))
        self.map.moveCenterObjectToPosition(playerCoord[0]+20, playerCoord[1])
        self.map.setCenterObjectToTop()
        self.map.canvas.update()
        
    def exitGame(self, *args):
        """Final exit to big map or just end"""

        # Getting called twice, so until then just exit once
        if not self.gameIsActive: return

        self.gameIsActive = False
        self.map.canvas.update()
        Sleep(2) 
        if self.playersMap.returnFunction is None:
            self.root.quit()
        else:
            self.playersMap.returnFunction()   
  
    def makeTheEpilogue(self, epilogue):
        """ Create the epilogue text based on the game summary and player history.
        NOTE: Needs computer info to identify user, more point detail, and time of play.
                self._history = {'Game Completed':False, 'Last Monster':None, 'Last Touch':None, 'Last Reward':None,
                        'Last Theft':None, 'Weapon':False, 'Sword':False, 'Axe':False, 'Met Boss':False, 
                        'Thief':False, 'Torches Left':0, 'Potion':0}
        """
        highlights = [f"{self.nickname}; AKA:{self.studentName} with Login: {self.userName}"]
        winning = self.player.getHistory('Game_Won', False)
        score = self.player.getHistory('Game_Score', 0) * 33.4
        if score == 0:
            rewardHistory = self.rewardBox.currentStatus()
            gameRules = self.quiz.dictionary
            coinGoal = gameRules.get("Coin Goal", 10)
            if coinGoal <= 0: coinGoal = 1 # Protect from a div/0 error
            gold = rewardHistory.get("gold", 0)
            silver = rewardHistory.get("silver", 0)
            copper = rewardHistory.get("copper", 0)
            winning = ( gold >= coinGoal and silver >= coinGoal and copper >= coinGoal )
            score = int((min(1.0,int(gold/coinGoal)) + min(1.0,int(silver/coinGoal)) + min(1.0,int(copper/coinGoal))+ 0.1)*33.4)
        result = "You won! 100"+'%'+" of the goal" if winning else f"You did not win it all! {score}% of the goal"
        scoring = rewardHistory.get("status", None)
      
        goldPlural = "s" if gold != 1 else ""
        silverPlural = "s" if silver != 1 else ""
        copperPlural = "s" if copper != 1 else ""
        rewardText = f"You ended up with {gold} gold piece{goldPlural}, {silver} silver piece{silverPlural}, and {copper} copper piece{copperPlural}."
        highlights.append(rewardText)
        if self.player.getHistory('Met_Boss', False): highlights.append("you met the dragon")
        if self.player.getHistory('Thief', False): highlights.append("you stole gold from it")
        if self.player.getHistory('Weapon', False): 
            if self.player.getHistory('Axe', False): 
                highlights.append("you recieved the king's axe from the dragon (excellent courage)")
            else:
                highlights.append("you picked up a sword or two")
        else:
            highlights.append("you never picked up a weapon (you pacifist)")
        potions = self.player.getHistory('Potion', 0)
        if potions > 0:
            plural = "s" if potions > 1 else ""
            article = "a" if potions == 1 else "some"
            highlights.append(f"you found {article} potion{plural} (they usually taste terrible)")
        torches = self.player.getHistory('Torches_Left', 0)
        if torches > 0:
            plural = "es" if torches > 1 else ""
            article = "a" if torches == 1 else "some"
            highlights.append(f"you even had {article} torch{plural} left at the end of the game")
        length = len(highlights)
        if length == 0:
            highlightText = "You had no highlights, you were a boring player."
        else:
            plural = "s were" if length > 1 else " was"
            if length > 1: 
                highlights[-1] = "and " + highlights[-1]
            highlightText = f"Your highlight{plural} that {', '.join(highlights)}."

        summaryText = f"{result}! {highlightText}."
        text = "\n\nGAME SUMMARY:\n\n" + summaryText+ "\n\n" + epilogue + "\n"
        return text      
            
    def makeSoundOrMusicCode(self, functionToCall, name):
        """ Return an internal sound call which can work without parameters"""
        localFunction = functionToCall
        localName = name
        def localCode(*args):
            localFunction(name)
            
        return localCode
            
    def makeThresholdCode(self, dictionary):
        """Create a function that will play the music based on the dictionary provided. Current music is stopped.
        The dictionary is a dictionary with keys 'Left-Dungeon', 'Right-Sadness', etc. and their values are the music to play.
        The directions are based on the movement keys most likely used wqhen crossing the barrier. Barriers
        should be wider than the player can move (generally 10 pixel at a time) but short enogh you minimize duplicate hits"""
        if len(dictionary) == 0: return None
        localDictionary = dictionary.copy()  # Make a copy of the dictionary to avoid issues with function closure

        # Internal function to be returned which does not need parameters
        def thresholdCode(*args):
            # args[0] is the mapObject, args[1] is the direction
            direction = args[1].lower() if len(args) > 1 else None
            if direction is not None:
                for key,musicToPlay in localDictionary.items():
                    if key.lower() == direction:
                        self.soundMixer.playContinuousMusic(musicToPlay)
                        break
        return thresholdCode

    def disappear(self, *args):
        """Make the object disappear"""
        mapObject = args[0]
        move = None if len(args) < 2 else args[1]
        if mapObject is None: return
        mapObject.undraw()
        
    def fade(self, *args):
        """Fade the object out of existence"""
        mapObject = args[0]
        if mapObject is None: return
        if mapObject.PILimage is not None: # Only these can fade
            for alpha in [220,195,170,145,120,95,70,45,20]:
                mapObject.fade(self, alpha)
                mapObject.canvas.widget.after(self.UIfadeTime) 
        mapObject.undraw()

    def fadeIn(self, *args):
        """Fade the object into existence.  Untested"""
        mapObject = args[0]
        if mapObject is None: return
        if mapObject.PILimage is None: # Only these can fade in
            mapObject.draw()
        else:
            mapObject.hide() # How do I set it visible but completely faded as a start?
            mapObject.draw()
            mapObject.fade(self, 0)
            mapObject.unhide()
            for alpha in [20,45,70,95,120,145,170,195,220]:
                mapObject.fade(self, alpha)
                mapObject.canvas.widget.after(self.UIfadeTime) 

    def drawObject(self, *args):
        """Redraw the object, used for darkness objects to redraw themselves after fading."""
        mapObject = args[0]
        if mapObject is not None:
            mapObject.draw()

    def hideObject(self, *args):
        """Hide the object, used for darkness objects to hide themselves after fading."""
        mapObject = args[0]
        if mapObject is not None:
            mapObject.hide()

    def unhideObject(self, *args):
        """Unhide the object, used for darkness objects to unhide themselves after fading."""
        mapObject = args[0]
        if mapObject is not None:
            mapObject.unhide()

    def hideGroup(self, *args):
        """Hide a group of objects, used for darkness objects to hide themselves after fading."""
        group = args[0]
        if group is not None:
            for mapObject in group:
                mapObject.hide()

    def unhideGroup(self, *args):
        """Unhide a group of objects, used for darkness objects to unhide themselves after fading."""
        group = args[0]
        if group is not None:
            for mapObject in group:
                mapObject.unhide()

    def gloom(self, *args):
        self.darkness(*args) # like darkness but will reappear after a period of time
        
    def remove(self, *args):
        if len(args) == 0: return
        mapObject = args[0]
        if mapObject is None: return
        mapObject.undraw()
        mapObject.delete()
        mapObject = None
        
    def darkness(self, *args):
        """Used by darkness objets to describe what is in the room, activate any linked room, 
        provide any messages, run any functions, and then fade into oblivion.
        This is a function called from the object."""
        mapObject = args[0]
        if mapObject is None: return
        statusBarMessage = mapObject.dictionary.get("Message", "") # Default message for the status Bar
        contentDescriptions = ""

        # Get all objects in the room's contents and format their descriptions
        if mapObject.dictionary["Is a Room"]:
            contents = mapObject.dictionary["Contents"]
            mapDictionary = mapObject.dictionary["Room Dictionary"]
            contentDescriptions = "\n" + mapDictionary["Description"] + " "
            for item in contents:
                objectDescription = item.get("Description",None)
                if objectDescription is not None and len(objectDescription) > 0:
                    if isinstance(objectDescription, list):
                        newDescription = self.vocab(*objectDescription, ending=None)
                        contentDescriptions += newDescription + " "
                    else:
                        newDescription = self.vocab(objectDescription, ending=None)
                        contentDescriptions += newDescription + " "

                # Add any messages for each item
                objectMessage = item.get("Message", None)
                if objectMessage is not None and len(objectMessage) > 0:
                    statusBarMessage += "\n" + objectMessage

            # Run functions for all activated object in the room's contents
            for item in contents:
                activation = item.get("Activate",False)
                if activation:
                    item["Activate"] = False 
                    itemObject = item.get( "MapObject", None)
                    if itemObject is not None:
                        itemObject.callActions()

        self.instructions.newSection(contentDescriptions)
        self.statusBar.set(statusBarMessage)
        self.fade(*args)

    def pickupSword(self, *args):
        """ Code to pick up or get rid of a lesser valued sword"""
        mapObject = args[0] if len(args) > 0 else None
        name = "Sword" if mapObject is None else mapObject.dictionary.get("Name", "Sword")
        if self.player.canYouPickUpSword(name):
            self.player.addItem(name, PlayerClass.TYPE_SWORD)
            self.statusBar.set("You picked up a sword! It's a good one!")
        else:
            self.statusBar.set("Your current weapon is better, keep it!")
        
        if mapObject is not None: mapObject.undraw()
        self.recordHistory(Weapon=True, Sword=True)

    def pickupAxe(self, *args):
        """Code to pick up an axe and drop any sword"""
        mapObject = args[0] if len(args) > 0 else None
        if self.badges is not None:
            self.badges.addIcon("Axe", PlayerClass.TYPE_AXE)
        self.recordHistory(Weapon=True, Axe=True)
        self.player.addItem("Axe", PlayerClass.TYPE_AXE)
        if self.statusBar is not None:
            self.statusBar.set("You have the King'axe! It won't break!")
        if mapObject is not None: mapObject.undraw()

    def pickupPotion(self, *args):
        """Picked-up potions go on the badge widget, but only one carried at a time."""
        mapObject = args[0]
        if mapObject is None: return
        name = mapObject.dictionary.get("Name", "Potion")
        if self.badges is not None:
            self.badges.addIcon(name, PlayerClass.TYPE_POTION)
            self.potionMapObject = mapObject # Use the potion map object even though it is undrawn.
        if self.statusBar is not None:
            self.statusBar.set("You have a potion! What does it do?")
        self.recordHistory(Potion=1)
        mapObject.undraw()

    def usePotion(self, *args):
        """Use a potion if you have one by clicking on its icon. Only one carried at a time. FIFO"""
        activePotion = self.badges.activePotion
        if activePotion is not None:
            self.badges.removePotion()
            self.recordHistory(Potion=-1)
            self.statusBar.set(f"You used a {activePotion.lower()}! Didn't do anything!  <burp>  Oh, wait a moment, the room in spinning... something is appearing...")
            
            # Potions can be a question or a specific action
            purpose = self.potionMapObject.dictionary.get("Purpose", None)
            if purpose == "Question":
                self.questionFunction(self.potionMapObject)
            else:
                # This is where alternative actions can be used, such as allowing travel on different colored paths.
                match activePotion:
                    case "Blue Potion":
                        self.questionFunction(self.potionMapObject)
                    case "Red Potion":
                        self.questionFunction(self.potionMapObject)
                    case "Green Potion":
                        self.questionFunction(self.potionMapObject)
                    case "Yellow Potion":
                        self.questionFunction(self.potionMapObject)
                    case "Purple Potion":
                        self.questionFunction(self.potionMapObject)
                    case "Black Potion":
                        self.questionFunction(self.potionMapObject)
                    case "White Potion":
                        self.questionFunction(self.potionMapObject)
                    case "Colorless Potion":
                        self.questionFunction(self.potionMapObject)
                
            # Ready to implement the potion's question
            self.questionArea.implementQuestion(self.potionMapObject)
            self.potionMapObject = None # Used up  --burp--
    
    def pickupSomethingMysterious(self, *args):
        """ Pick up something mysterious, such as a potion with unknown effects or something not created yet"""
        mapObject = args[0]
        if mapObject is None: return
        name = mapObject.dictionary.get("Name", None)
        if name is None: 
            name = mapObject.name if hasattr(mapObject, 'name') else "Unknown"
        if self.badges is not None:
            self.badges.addIcon(self, name, PlayerClass.TYPE_POTION)
        if self.statusBar is not None:
            self.statusBar.set("You picked up something mysterious! What does it do?")
        mapObject.undraw()

    # Non-parameter calls to add or remove treasure
    def _addGoldPiece(self, *args):
        self.rewardBox.addReward("Gold")
        self.keepTreasure = False
        self.recordHistory(Last_Reward="Gold")

    def _addSilverPiece(self, *args):
        self.rewardBox.addReward("Silver")
        self.keepTreasure = False
        self.recordHistory(Last_Reward="Silver")

    def _addCopperPiece(self, *args):
        self.rewardBox.addReward("Copper")
        self.recordHistory(Last_Reward="Copper")
    
    def _removeGoldPiece(self, *args):
        self.rewardBox.removeReward("Gold")
        self.recordHistory(Last_Reward=None)
    
    def _removeSilverPiece(self, *args):
        self.rewardBox.removeReward("Silver")
        self.recordHistory(Last_Reward=None)

    def _addSterling(self, *args, **kwargs):
        """Sterling allows multiple coins,  Example: "Sterling;Pound(2);Shilling(1);Pence(1)"
         The first argument passed in should be the mapObject calling the function.
         Correct answer totals are calculated in pence then converted to pence (copper),
         shillings (silver), and pounds (gold)."""
        
        # Get a the map object with the scores, rewards, penalty, and question
        if len(args) ==0 : return
        mapObject = args[0]
        score = mapObject.right
        
        # Get a valid bounty list and split the list, remove "strirling"
        reward = mapObject.question.get("Reward", "") if mapObject is not None else ""
        bountyList = reward.lower().split(";")
        del bountyList[0]

        # Split the list and process each valid coinage individually
        total = 0
        for eachBounty in bountyList:
            coin,number = self._extractParameter(eachBounty)
            if coin is not None and number is not None:
                if isinstance(number, str): 
                    try:
                        number = int(number)
                    except:
                        number = 1
                useNumber = min(max(number,0),1000)
                checkCoin = coin.lower()
                if checkCoin == "pence":
                    total += useNumber
                elif checkCoin == "shilling":
                    total += 12 * useNumber
                elif checkCoin == "pound":
                    total += 240 * useNumber
        
        total *= score
        pound = total // 240
        total -= pound * 240     
        shilling = total // 20
        pence = total - (20 * shilling) 
                
        if pence > 0: self.rewardBox.addReward("Copper", amount=pence)
        if shilling > 0: self.rewardBox.addReward("Silver", amount=shilling)
        if pound > 0: self.rewardBox.addReward("Gold", amount=pound)
        if pence or shilling or pound:
            self.map.canvas.update()
            self.canvas.root.after(330)

    def _removeSterling(self, *args, **kwargs):
        """Sterling allows multiple coins,  Example: "Sterling;Pound(2);Shilling(1);Pence(1)"
         The first argument passed in should be the mapObject calling the function.
         Correct answer totals are calculated in pence then converted to pence (copper),
         shillings (silver), and pounds (gold)."""
        
        # Get a valid bouinty list
        if len(args) == 0 : return
        mapObject = args[0]
        score = mapObject.wrong
        reward = mapObject.question.get("Reward", "") if mapObject is not None else ""
        bountyList = reward.lower().split(";")
        del bountyList[0]

        # Split the list and process each valid coinage individually
        total = 0
        for eachBounty in bountyList:
            coin,number = self._extractParameter(eachBounty)
            if coin is not None and number is not None:
                if isinstance(number, str): 
                    try:
                        number = int(number)
                    except:
                        number = 1
                useNumber = min(max(number,0),1000)
                checkCoin = coin.lower()
                if checkCoin == "pence":
                    total += useNumber
                elif checkCoin == "shilling":
                    total += 12 * useNumber
                elif checkCoin == "pound":
                    total += 240 * useNumber
        
        total *= score
        pound = total // 240
        total -= pound * 240     
        shilling = total // 20
        pence = total - (20 * shilling) 
                
        if pence > 0: self.rewardBox.removeReward("Copper", amount=pence)
        if shilling > 0: self.rewardBox.removeReward("Silver", amount=shilling)
        if pound > 0: self.rewardBox.removeReward("Gold", amount=pound)
        if pence or shilling or pound:
            self.map.canvas.update()

    def _removeCopperPiece(self, *args):
        self.rewardBox.removeReward("Copper")
        self.recordHistory(Last_Reward=None)

    def _addBounty(self, *args, **kwargs):
        """Bounty allows multiple coins,  Example: "Bounty;Gold(2);Silver(1);Copper(1)"
         The first argument passed in should be the mapObject calling the function """
        
        # Get a valid bounty list
        if len(args) == 0: return
        mapObject = args[0]
        reward = mapObject.question.get("Reward", "") if mapObject is not None else ""
        bountyList = reward.split(";")
        del bountyList[0]

        # Split the list and process each valid coinage individually
        for eachBounty in bountyList:
            coin,number = self._extractParameter(eachBounty)
            if coin is not None and number is not None:
                if isinstance(number, str): 
                    try:
                        number = int(number)
                    except:
                        number = 1
                useNumber = min(max(number,0),10)
                for addition in range(useNumber):
                    self.rewardBox.addReward(coin)
        self.map.canvas.update()

    def _removeBounty(self, *args, **kwargs):
        return # Bounty is always positive, otherwise it's a famine. Function just returns.

    def removeTreasure(self, **kwargs):
        """Instead of a bounty it is a famine for one type of coin. Pass in a dictionary with keys of
        Gold, Silver, Copper and values the number to remove."""
        for key, value in kwargs.items():
            keyValue = key.lower()
            if isinstance(value, str): value = 10
            useValue = max(min(value,0),10)
            if keyValue == "gold":
                for theft in range(useValue):
                    self.rewardBox.removeRewardGold()
            elif keyValue == "silver":
                for theft in range(useValue):
                    self.rewardBox.removeRewardSilver()
            elif keyValue == "copper":
                for theft in range(useValue):
                    self.rewardBox.removeRewardCopper()

    def _removeSafeColorRed(self, *args):
        self.removeMapColor(self, MAP_RED)
    def _removeSafeColorBlack(self, *args):
        self.removeMapColor(self, MAP_BLACK)
    def _removeSafeColorBlue(self, *args):
        self.removeMapColor(self, MAP_BLUE)
    def _removeSafeColorGreen(self, *args):
        self.removeMapColor(self, MAP_GREEN)
    def _removeSafeColorYellow(self, *args):
        self.removeMapColor(self, MAP_YELLOW)
    def _removeSafeColorMagenta(self, *args):
        self.removeMapColor(self, MAP_MAGENTA)
    def _removeSafeColorCyan(self, *args):
        self.removeMapColor(self, MAP_CYAN)
    def _removeSafeColorWhite(self, *args):
        self.removeMapColor(self, MAP_WHITE)
    def removeMapColor(self, color):
        # Remove any color from the player safe move list
        if ( map := self.getResource("playersMap")):
            removed = map.removeSafeColor(color)
            # if there was, display if to remove part of the map
            if removed:
                colors = dict(zip([MAP_RED, MAP_BLACK, MAP_BLUE, MAP_GREEN, MAP_YELLOW, MAP_MAGENTA, MAP_CYAN, MAP_WHITE],
                                    ["Red", "Black", "Blue", "Green", "Yellow", "Magenta", "Cyan", "White"]))
                name = f"{color[0].upper()}{color[1:].lower()}-Black"
                filename = f"{name}.png"
                path = pathlib.Path(self.objectsPath, filename)
                if pathlib.Path.exists(path):
                    objectCoord = (0,0)
                    coord = self.map.convertMapCoordinatesToStandard(objectCoord)
                    theObject = MapImage(self.map, coord, file=path, name=name )
                    # Place center object back on top
                    if theObject is not None: map.centerObject.moveToTop()

    def establishDragonColor(self, dragonDictionary):
        """ Establish a random color for a dragon.  The ccolor is used in sentences and different images."""
        dragon = dragonDictionary.get("NPC", None)
        file = dragonDictionary.get("File", None)
        if file is None: return dragon
        if file.startswith("SleepingDragon"):
            color = self.vocab.selectRandomNamesFromList("dragon_prefix")[0]
            dragonDictionary["File"] = color + file
            dragonDictionary["Color"] = color
        else:
            color = file.split("SleepingDragon")[0]
            dragonDictionary["Color"] = color
        return dragon

    def stealGoldCoin(self, *args):
        """You can steal a gold coin but it will awaken a grumpy dragon"""
        mapObject = args[0]
        if mapObject is None: return
        if not hasattr(mapObject, 'NPC'):
            mapObject.NPC = None
            dictionary = self.findMapObject("Dragon")
            if dictionary is not None:
                dragon = self.establishDragonColor(dictionary)
                if isinstance(dragon, str) and len(dragon) > 0:
                    dragonObject = self.returnClassfrom(dragon)
                    mapObject.NPC = dragonObject(self, dictionary)
                    self.boss = mapObject.NPC
        if mapObject.NPC is not None: mapObject.NPC.awakenByThief()
        
        # Your gold piece, but at a price
        self._addGoldPiece()
        goldCoinDictionary = self.findMapObject("GoldCoin")
        if goldCoinDictionary is not None:
            goldCoinObject = goldCoinDictionary.get("MapObject", None)
            if goldCoinObject is not None: goldCoinObject.undraw()
                
        statusBar = mapObject.dictionary.get("Message", None) # Default message for the status Bar
        self.statusBar.set("You stole a gold coin! Hope the dragon did not notice it!")
        self.disappear(mapObject)

    def stopMoving(self):
        """Stop any automatic movement of the player"""
        timers = self.getResource("timers")
        timers.clearAutomaticMouseMovements()

    def disappearOnWeapon(self, *args):
        """ Some objects like webs just disappear when hit with a weapon. Swords break down with each use."""
        mapObject = args[0]
        if mapObject is not None:
            weapon = self.player.nameOfWeapon()
            if weapon is not None:
                self.player.weaponIsDamaged()
                self.fade(mapObject)
    
    def objectsTouch(self, object, target):
        """ Check if the object moves and touches the player or another object"""
        found = False
        bbox = object.canvas.widget.bbox(object.id)
        result = object.canvas.widget.find_overlapping(bbox[0], bbox[1], bbox[2], bbox[3])
        for element in result:
            if element == target.id:
                found = True
                break
        return found
    
    def specialCodeFunction(self, *args, **kwargs):
        """ Special code that is not easily categorized, so it is handled in the object itself.  The parameter can be used to provide any needed information."""
        return None # This is just a placeholder. The actual function should be defined in the object that uses it. 
    
    def fillInWithDarkenss(self, mapObject):
        """Fill and object with Black"""
        image = mapObject.PILimage
        if image is not None:
            r, g, b, a = image.split()
            x = r.point(lambda i: 0)  # Make everything black but keep the alpha channel
            w = r.point(lambda i: 255)  # Make everything white but keep the alpha channel
            blackImage = PILImage.merge("RGBA", (x, x, x, a))
            newImage = ImageTk.PhotoImage(blackImage)
            mapObject.updateImage(newImage)

    ################ QUESTIONS ############################
    def _successfulQuestion(self, *args):
        """ Standard function to handle a successful question, check for game ended."""
        if len(args) > 0:
            mapObject = args[0]
            self.recordIfGameCompleted()
            
    def _failedQuestion(self, *args):
        """ Standard function to handle a failed question, such as removing the treasure, fading the object, and removing it."""
        if len(args) > 0:
            mapObject = args[0]

            # For treasure objects, save the missed question for later review
            if isinstance(mapObject, MapImage):
                self.missedQuestions.append(mapObject.question)  # Save the question for later

            # If there was a penalty associated with the question, bring back a questions with that reward
            penalty = mapObject.question["Penalty"]
            if len(penalty) > 0:
                for question in self.questions:
                    if question["Reward"] == penalty:
                        self.missedQuestions.append(question)  # Save the matching question for later
                        break

    def _secondTryQuestion(self, *args):
        #mapObject = args[0]
        #move = None if len(args) < 2 else args[1]
        """ Function to handle a second try question, such as adding a reward, fading the object, and removing it."""
        #mapObject = args[0]

        #################### RETURN FUNCTIONS BASED ON A NAME ##############################
        
    ################ RETURN NAMED FUNCTIONS  ############################
    def retrieveFunctionFromAction(self, currentObject, providedName, parameter=None):
        """ Return a function based on the action name and parameter - easy ones first"""
        action = None
        actionName = providedName.lower()
        match actionName:
            case "exitgame":
                action = self.exitGame
            case "gold":
                action = self._addGoldPiece
            case "silver":
                action = self._addSilverPiece
            case "copper":
                action = self._addCopperPiece
            case "removegold":
                action = self._removeGoldPiece
            case "removesilver":
                action = self._removeSilverPiece
            case "removecopper":
                action = self._removeCopperPiece
            case "fade":
                action = self.fade
            case "disappear":
                action = self.disappear
            case "message":
                localParameter = parameter if parameter is not None else ""
                def localMessageToStatusBar(self, *args):
                    self.data.statusBar.set(localParameter)
                if parameter is not None:
                    action = localMessageToStatusBar
            case "sword":
                action=self.pickupSword
            case 'question': 
                action = self.questionFunction
            case 'savequestion':
                action = self.saveMissedQuestion
            case 'fading':
                return self.fade # Code to fade and then based on useOnce, remove the object or do something else
            case 'fadedirection':   
                return self.fadeDirection # Code to fade from the direction touched and then based on useOnce, remove the object
            case 'darkness':
                return self.darkness
            case 'disappear':
                return self.disappear # Code to disappear then based on useOnce, remove the object
            case 'torchcheck':
                return self.torchCheck
            case 'fadein':
                return self.fadeIn
            case 'draw':
                return self. drawObject
            case 'hide':
                return self.hideObject
            case 'unhide':
                return self.unhideObject
            case 'hidegroup':
                return self.hideGroup
            case 'unhidegroup':
                    return self.unhideGroup
            case 'gloom':
                return self.gloom            
            case 'remove':
                return self.remove
            case 'disappearonweapon':
                return self.disappearOnWeapon
            case 'removeSafeColorRed':
                return self._removeSafeColorRed
            case 'removeSafeColorBlack':
                return self._removeSafeColorBlack
            case 'removeSafeColorBlue':
                return self._removeSafeColorBlue
            case 'removeSafeColorGreen':
                return self._removeSafeColorGreen
            case 'removeSafeColorYellow':
                return self._removeSafeColorYellow
            case 'removeSafeColorMagenta':
                return self._removeSafeColorMagenta
            case 'removeSafeColorCyan':
                return self._removeSafeColorCyan
            case 'removeSafeColorWhite':
                return self._removeSafeColorWhite
                
            # A lambda function did not like parameter or *parameter, or a,b such as return lambda a,b: self.soundMixer.playSound(a,b)
            case 'sound': # Parameter: single name of the sound to produce
                if parameter is None or not isinstance(parameter,str) or len(parameter) <= 0: return None
                action = self.makeSoundOrMusicCode(self.soundMixer.playSound, parameter)  
                return action
                
            case 'backgroundmusic':
                if parameter is None or not isinstance(parameter,str) or len(parameter) <= 0: return None
                action = self.makeSoundOrMusicCode(self.soundMixer.playContinuousMusic, parameter)  
                return action
            
            case 'music':
                if parameter is None or not isinstance(parameter,str) or len(parameter) <= 0: return None
                action = self.makeSoundOrMusicCode(self.soundMixer.playMusic, parameter)  
                return action
            
            case "returntoentrance": 
                return self.exitGameBox

            case "activatedragon": # The function is found in the object, not data
                return currentObject.NPC.activate # Activate the dragon boss
            
            case "talktoboss": # The function is found in the object, not data
                if self.boss is None:
                    return None
                else:
                    return [self.soundMixer.fadeOutMusic,self.boss.activate] # Fade off music and activate the current boss
            case "exitgamebox":
                return self.exitGameBox # Exit the game
            
            case "pickuppotion":
                return self.pickupPotion # Pick up a potion
            
            case "stealgoldcoin":
                return self.stealGoldCoin # Steal a gold coin from the player
            
            case "threshold": # The parameter is an array of control information: [Left-Dungeon,Right-Sadness]
                if parameter is None or len(parameter) <= 0: return None
                dictionary = {}
                eachAction = parameter.split(";")
                for elements in eachAction:
                    elementList = elements.split("-")
                    if len(elementList) >= 2:
                        direction = elementList[0]
                        musicToPlay = elementList[1]
                        dictionary[direction] = musicToPlay
                if len(dictionary) == 0:
                    return None
                action = self.makeThresholdCode(dictionary)  # Create a threshold object with the dictionary
                return action
            case "special":
                return self.specialCode # Special code that is not easily categorized, so it is handled in the object itself.  The parameter can be used to provide any needed information.
            case _: 
                # Check for a call to a NPC
                if actionName[0] == ".":
                    actionToFind = actionName[1:]
                    if hasattr(currentObject, 'NPC'):
                        action = currentObject.NPC.returnFunction(actionToFind) 
                 
        return action        
    
    def findFunctionbyName(self, functionName, parameter):
        """ Find a function by its name in this class or the player class"""
        function = self.retrieveFunctionFromAction(self, functionName, parameter=parameter)
        if function is None or function == False:
            if self.player is not None: 
                function = self.player.retrieveFunctionFromAction(self.player, functionName)
        return function
