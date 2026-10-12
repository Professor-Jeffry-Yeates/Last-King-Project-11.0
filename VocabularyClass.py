import random, math, os
class VocabularyClass():
    """Convert formatted text into text and substitute text from specific randomized files/lists.
    The extra parameters are files contining lists to randomly choose from. Once a file
    is read from, its contents are held in lists for faster access a second time.
    Examples:
        response = vocab("Just a sentence")
        response = vocab("Just the random color {0}", "potion_prefix")
        response = vocab(roomEnteringPhrase, roomEnteringContent, "scroll")
    Contents (2nd element) and definitions (1st element) can be replaced using dictionary elements.
    This allows easier to read code when contents or definitions are used in multiple places.
    Contents have the keyword substituted into it before formatting to load keyword-specific files.
    Examples:
        definition: '{1} a {2} {0}{3}. You are {4} and yell "{5}"! Oh well. {6}'
        content: "verb_room_entered,pre_adj_{0},post_adj_{0},emotional_response,emotional_outburst,thought_what_next"
    """
    def __init__(self, data, listFolder):
        self.data = data.setResource("vocabdata", self)
        self.folder = listFolder # Folder where .txt files are found
        self.normal = dict() # Normal substitutions lists
        self.special = dict() # Substitutions with special formats or randomness
        self.contents = dict() # Contents stored ahead of time
        self.definitions = dict() # Definitions stored ahead of time
        self.punTuples = [(", .","."),("? .","?"),(", ,",","),("  .","."),(" .","."),("  "," "),("?.","?")]

    def extractToList(self, listing):
        """Extract separate elements from comma-separated strings, lists or tuples into a list"""
        newList = []
        if isinstance(listing,str):
            if len(listing) > 0:
                newList = listing.split(',')
        elif isinstance(listing,tuple):
            if len(listing) > 0:
                newList = list(listing)
        elif isinstance(listing,list):
            if len(listing) > 0:
                newList = listing
        return newList

    def extractListFromFile(self, name):
        """Load list from a file"""
        newList = []
        if len(name) > 0:
            file = name.lower()+".txt"
            fileName = os.path.join(self.folder,file )
            if os.path.exists(fileName):
                try:
                    with open(fileName, 'r') as file:
                        lines = file.readlines()
                except Exception as e:
                    self.data.logError(f"Error: Unable to open {fileName} in the vocabulary folder: {e}")
    
                else:
                    for line in lines:
                        freshLine = line.rstrip("\n")
                        if len(freshLine) > 0: newList.append(freshLine)
        return newList

    def addDefinition( self, name, definition ):
        """Add a definition for use as a dictionary element"""
        if isinstance(name, str) and len(name) > 0:
            if isinstance(definition, str)   and len(definition) > 0:
                self.definitions[name]=definition

    def addContent( self, name, definition ):
        """Add a content for use as a dictionary element"""
        if isinstance(name, str) and len(name) > 0:
            if isinstance(definition, str)   and len(definition) > 0:
                self.contents[name]=definition

    def addNormalVocabulary(self, name, listing=None): 
        """Normal vocabulary lists are added in real time as needed.  They can be added manually.
        Examples are specific words, phrases, or sentences that are used in the game. 
        Example, 'Potion' can be prefixed with a particular color."""
        newList = []
        if listing is None:
            newList = self.extractListFromFile(name)
        else:
            newList = self.extractToList(listing)
        self.normal[name] = newList
        
    def addSpecialVocabulary(self, name, dictionary, listing= None): # 
        """ Add a non-normal listing to choose from.  Dictionary elements are:
        LIST:  Required list of words either already in the library or provided separetly in the call
        FORMAT: Optional format string to format with the list.  This format result is returned as one item
        STANDARD_DEVIATION: Automatically calculated when the list is added - used by BELL_CURVE
        RANDOM: One of these random choices( BELL_CURVE, WEIGHTED to earlier listing items, NORMAL if excluded).
        """
        if isinstance(name, str) and len(name) > 0 and isinstance(dictionary, dict):
            usingDictionary = dictionary.copy()
            self.special[name] = usingDictionary
            if listing is not None:
                usingDictionary['LIST'] = self.extractToList(listing)
                useListing = listing
            else:
                useListing = usingDictionary['LIST']
            if len(useListing) > 0:
                size = len(useListing)
                data_points = range(1, size + 1)
                mean = sum(data_points) / size
                variance = sum((x - mean) ** 2 for x in data_points) / size
                standard_deviation = math.sqrt(variance)
                usingDictionary['STANDARD_DEVIATION'] = standard_deviation

    def findInDefinitions(self, value):
        definitionResult = self.definitions.get(value, None)
        return definitionResult

    def findInContents(self, value):
        contentResult = self.contents.get(value, None)
        return contentResult

    def complete(self, *args, **wargs):
        """Complete the vocabulary with the given arguments. This is the main function.
        *args are a collection of definition, collection, and keywords. **wargs are optional pre-saved
        definitions and/or contents.
        """
        length = len(args)
        result = ""
        if length == 0: return result
        listElement = args
        if isinstance(listElement, str):
            length = 1
            definition = listElement
            keyword = listElement
            content = listElement
        elif isinstance(listElement[0], list) or isinstance(listElement[0], tuple):
            tryElement = listElement[0]
            length = len(tryElement)
            # Default guesses
            definition = tryElement[0]
            keyword = tryElement[length-1]
            content = tryElement[min(length-1,length-2)]
        else:
            length = len(listElement)
            # Default guesses
            definition = listElement[0]
            keyword = listElement[length-1]
            content = listElement[min(length-1,length-2)]

        # Adjust if a premade definition was included
        choose = length
        foundDefinition = False
        value = wargs.get("definition",None)
        if value is not None:
            definitionResult = self.definitions.get(value, None)
            if definitionResult is not None:
                content = definition
                definition = definitionResult
                foundDefinition = True

        # Adjust if a premade content was included
        foundContent = False
        value = wargs.get("content", None)
        if value is not None:
            contentResult = self.contents.get(value, None)
            if contentResult is not None:
                content = contentResult
                foundContent = True

        # Adjust which mode to choose based on parameters and dictionary elements 
        if foundDefinition or foundContent: choose += 1
        if foundDefinition and foundContent: choose = 3

        match choose:
            case 1: # Just what was passed in
                result = keyword

            case 2: # A single format string, and also a keyword or list of names containing text
                listResults = self.extractListFromParameter(keyword)
                 

            case 3: # A format string, a format string or list of names containing file-categories to 
                # randomly select from, and replacement for file category such as "scroll" or "potion".

                # The file names are provided and there is no provided formatting
                if definition.startswith("pre_adj_"):
                    listResults = self.extractListFromParameter([definition, "adv_object_finding", content])
                    definition = "You {2} a {1} {0}, {3}." 

                # Formatting is required
                else:

                    # formatedNames = self.extractListFromParameter(content)
                    # if len(formatedNames) > 0:
                    #     result = definition.format(*formatedNames)
                    # else:
                    #     result = definition
                    formatedNames = content.format(keyword)
                    listResults = self.extractListFromParameter(formatedNames)

                # Final formatting
                itemName = keyword.replace("_"," ")
                result = definition.format(itemName, *listResults)
            case _:
                pass
        if isinstance(result, list):
            sentenceResult = "There is bad input as the result in a list: " + str(result[0])
        else:
            ending = wargs.get("ending",".")
            if ending is not None and len(result) > 0:
                sentenceResult = result[0].upper() + result[1:] + ending
            else:
                sentenceResult = result
        # Cleanup the punctuation
        sentenceResult = self.cleanUpPunctuation(sentenceResult)
        return sentenceResult

    def cleanUpPunctuation(self, text):
        sentenceResult = text
        for finding,changeTo in self.punTuples:
            sentenceResult = sentenceResult.replace(finding,changeTo)
        return sentenceResult
        
    def getSpecialRandomResult(self, specialDictionary, size, listing):
        """Get a random result or other modifications from an special dictionary."""
        result = ""
        if size > 0 and isinstance(specialDictionary, dict):
            if isinstance(listing,list) and len(listing) > 0:
                randomness = specialDictionary.get('RANDOM', 'NORMAL')
                match randomness:
                    case "BELL_CURVE":
                        standard_deviation = specialDictionary.get('STANDARD_DEVIATION', None)
                        if standard_deviation is None:
                            data_points = range(1, size + 1)
                            mean = sum(data_points) / size
                            variance = sum((x - mean) ** 2 for x in data_points) / size
                            standard_deviation = math.sqrt(variance)
                        rawNumber = random.randint(0, size) * standard_deviation
                        number = min(size-1,max(0,int(rawNumber)))
                        pass
                    case "WEIGHTED":
                        weight = sum(range(1, size + 1))
                        weightedNumber = random.randint(0, weight - 1)
                        number = 0
                        for i in range(size, 0, -1):
                            weight -= i
                            if weight <= weightedNumber:
                                break
                            number += 1
                        pass
                    case _: # NORMAL
                        number = random.randint(0, size - 1)
                result = listing[number] 
                if randomness == "USE_ONCE": del listing[number]
        return result

    def extractListFromParameter(self, stringOrListOfNames): # Can also be a tuple
        """Extract a list of names from a string or list of names and choose one. Can be recursive.
        If a string, it is split by commas. If a list, it is used directly. Elements are lists names
        to choose from and are read dynamically if not alread read-in. If these are special elements
        they are used to format the result or return a random result from a different list. Elements
        in these can also be format strings with their own lists.
        """
        if isinstance(stringOrListOfNames, str):
            listNames = stringOrListOfNames.split(',')
        elif isinstance(stringOrListOfNames,list) or isinstance(stringOrListOfNames,tuple):
            listNames = stringOrListOfNames
        else:
            listNames = []

        listResults = []
        for item in listNames:    
            result = None
            listing = self.normal.get(item, None) # Search to normal dictionary first
            if listing is not None:
                size = len(listing)
                number = random.randint(0, size - 1)
                result = listing[number]
            else:
                newNormalListNeeded = True
                specialDictionary = self.special.get(item, None) # Search to special dictionary second
                if specialDictionary is not None: 
                    listing = specialDictionary['LIST'] # Get the list from the special dictionary
                    formatString = specialDictionary.get('FORMAT', None)
                    if formatString is not None:
                        listResults = self.extractListFromParameter(listing)
                        result = formatString.format(*listResults)
                        newNormalListNeeded = False
                    elif len(listing) > 0:
                        result = self.getSpecialRandomResult(specialDictionary, len(listing), listing)
                        newNormalListNeeded = False
                    
                if newNormalListNeeded: # Not found anywhere, bring in a new normal list
                    newList = self.extractListFromFile(item)
                    if len(newList) == 0: newList.append("")
                    self.normal[item] = newList
                    size = len(newList)
                    number = random.randint(0, size - 1)
                    result = newList[number]
            if result is not None: listResults.append(result)
        return listResults

    def selectRandomNamesFromList(self, name):
        resultList = self.extractListFromParameter(name)
        return resultList

    def findNameInList(self, name, listName):
        resultList = self.normal.get(listName, None)
        if resultList is None:
            self.addNormalVocabulary(listName)
            resultList = self.normal.get(listName, None)
        return (name in resultList)
    
    def extractRandomItemFromFile(self, filename):
        listOfThings = self.extractListFromParameter(filename)
        size = len(listOfThings)
        number = random.randint(0, size - 1)
        result = listOfThings[number] 
        return result

    def makeStandardDescription( self, name):
        standardName = f"standard_{name.lower()}"
        standardName = standardName.replace(" ","_")
        found = self.checkExistence(description=standardName, content=standardName)
        if found:
            description = [standardName,standardName,name]
        else:
            specificDescription = self.findInDefinitions(standardName)
            specificContent = self.findInContents(standardName)
            if specificDescription is not None and specificContent is not None:
                description = [specificDescription, specificContent, name]
            else:
                description = [f"pre_adj_{standardName}",f"post_adj_{standardName}",name]
        return description

    def makeNormalDescription( self, name, standard=False):
        normalName = name.lower().replace(" ","_")
        if standard:
            normalName = f"standard_{normalName}"
        found = self.checkExistence(description=normalName, content=normalName)
        if found:
            description = [normalName,normalName,name]
        else:
            specificDescription = self.findInDefinitions(normalName)
            specificContent = self.findInContents(normalName)
            if specificDescription is not None and specificContent is not None:
                description = [specificDescription, specificContent, name]
            else:
                description = [f"pre_adj_{normalName}",f"post_adj_{normalName}",name]
        return description
    
    def makeObjectDescription( self, dictionary):
        resultList = self.selectRandomNamesFromList("object")
        if len(resultList) > 0:
            name = resultList[0].strip()
            dictionary["Name"] = name
            dictionary["Kind"] = "object"
            dictionary["Description"] = ["pre_adj_object","post_adj_object",name]

    def checkExistence(self, *args, **wargs):
        found = True

        # Specific dictionary items looking in specific dictionaries
        standardDescription = wargs.get("description", None)
        if standardDescription is not None:
            text = self.definitions.get(standardDescription,None)
            if text is None: found = False
        standardContent = wargs.get("content", None)
        if standardContent is not None:
            text = self.contents.get(standardContent,None)
            if text is None: found = False

        # Check any arguments
        for filename in args:
            path = os.path.join(self.folder, filename + ".txt")
            existing = os.exists(path)
            if not existing: found = False

        return found

    def __call__(self, *args, **wargs):
        """Call the complete function with the given arguments. This is the main function"""
        return self.complete(*args, **wargs)

    def __str__(self):
        """Return a string representation of the Vocab object."""
        string = ""
        for name, listing in self.normal.items():
            string = (f"Normal: {name} -> {listing}")
        for name, dictionary in self.special.items():
            string += f"\nSpecial: {name} -> {dictionary}"
        return string

    def __getitem__(self, name):
        """Get an item from the normal or special dictionaries."""
        if name in self.normal:
            return self.normal[name]
        elif name in self.special:
            return self.special[name]
        else:
            return "KeyError(" + f'"{name}" not found in Vocab.'+")"