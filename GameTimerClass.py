__version__ = '11.0'
from MultitaskingClasses import *
MACOS_PAUSE = 30
class GameTimerClass():
    """ Setup and save game timers, setup user input and actions """
    def __init__(self, data):
        self.data = data.setResource('timers', self)
        self.root = data.root
        self.canvas = None
        self.map = None
        
        # Data class dependent values
        self.logError = data.logError
        self.UIautomaticTime = self.data.UIautomaticTime
        self.UIloopTime = self.data.UIloopTime
        self.providedTimers = data.providedTimers
        self.lastTimeInLoop = 0
        
        # Movement values
        self.mouseMoves = [] # List of moves to reach the goal.  Single letters: U, D, L, R in byte array
        self.queuedEvents = [] # List of mouse events to process after the current goal is reached
        self.userKeyInput = False
        self.mouseEvent = None
        self.x_adjustment = 0
        self.y_adjustment = 0
        self.keys = None
        self.goalCoordinates = None # Coordinates of where to mouse click was made
        
        # Movement lists
        self.direction = ['Up','Down','Left','Right']
        self.wsad = ['w','s','a','d']
        self.keyActive = False
        self.loopStarted = False
        
        # Load in initial timers 
        self.timerCentral =  TimerControlClass(self.data)  
        for timingDictionary in self.providedTimers:
            timerListing = self.createGameTimerList(timingDictionary)
            self.timerCentral.addTimer(*timerListing)
 
    def loadTorches(self):    
        """ Load up torches which track time #"""
        initialTorches = self.data.quiz.get("Torches", 20 )
        self.data.initializeTorches(initialTorches) 
        
        # Start the GameResultFile saving quiz, torches, and coins
        text = f'Quiz {self.data.quiz["Quiz Name"]} with coin goal: {self.data.quiz["Coin Goal"]} and torches: {self.data.quiz["Torches"]}' 
        self.data.writeGameResult(text)
 
    def registerMap(self, map ):
        """ Copy values needed for the map being used """
        self.map = map
        self.canvas = map.canvas
        self.root =  self.canvas.root
        self.keys = map.keys
        self.wasd_keys_allowed = map.canvas.wasd_keys_allowed
        self.canvas.update()
        self.canvas.widget.focus_set()
        if not self.loopStarted:
            self.loopStarted = True
            self.setupUI()
            self.loopForUI()
            
    def createGameTimerList(self, timingDictionary):
        """Create the list holding a single timer's information for the timer control."""
        if 1 <= len(timingDictionary) <= 4:
            functionName = timingDictionary["function"]
            parameter = timingDictionary.get("parameter",'')
            function = self.data.findFunctionbyName(functionName, parameter)
            repeat = timingDictionary.get("repeat", None)
            single = timingDictionary.get("single", None)
            if repeat is not None:
                result = [timingDictionary["id"], timingDictionary["repeat"], timingDictionary["repeat"], function, parameter]
            elif single is not None:
                result = [timingDictionary["id"], timingDictionary["single"], 0, function, parameter]
        return result

    def setupUI(self):
        """ None: No input bindings, generally used by remote maps without user input
         'keys only': Only key input accepted, mouse clicks on map don't move the user
         True: Both mouse and key input accepted
         False: Only mouse input accepted
         """
        if self.map.mouseOnly == None:
            pass 
        elif self.map.mouseOnly == "keys only":
            self.root.bind("<KeyPress>", self.keyMapPress)
            self.root.bind("<KeyRelease>", self.keyMapRelease)
            self.root.bind("<Escape>", self.escapeRelease)
        elif self.map.mouseOnly:
            self.root.bind("<Button-1>", self.mouseMapClick)
        else:
            self.root.bind("<Button-1>", self.mouseMapClick)
            self.root.bind("<KeyPress>", self.keyMapPress)
            self.root.bind("<KeyRelease>", self.keyMapRelease)
            self.root.bind("<Escape>", self.escapeRelease)

    def mouseMapClick(self,event):
        """Process a mouse click on this canvas"""
        if event.widget == self.canvas.widget:
            self.mouseEvent = event
            self.mouseEvent.x += self.map.x_adjustment
            self.mouseEvent.y += self.map.y_adjustment
        
    def keyMapPress(self,event):
        """ event type 2 is key down, type 3 is key up#"""
        self.keys[event.keysym] = True
        self.keyActive = True
                
    def keyMapRelease(self,event):
        """ event type 2 is key down, type 3 is key up """
        self.keys[event.keysym] = False
        self.keyActive = True

    def escapeRelease(self, event):
        """ Check torch timers while we are at it"""
        player = self.data.getResource("player")
        if player is not None:
            self.data.torchCheck()

            # Message if out of questions
            if self.data.noMoreQuestions():
                self.data.noMoreQuestionsMessage()

            # Get the location of the last object with a question and move there on <esc>
            mapObject = player.lastQuestionObject
            if mapObject is not None:
                coord = mapObject.dictionary["Map"]
                bbox = self.canvas.widget.bbox(player.id)
                moves = self.determineMouseMoves( coord, bbox)
                self.map.setFlying(True)
                self.map.performAutomaticMovement(moves, showMovement=True)
                self.map.setFlying(False)

                # You could be directly on an "ask later" treasure and get stuck.
                # If so, forget if it was the last object so the question can get asked.
                lastObject = self.data.getLastTouch()
                if lastObject is not None:
                    itemList = self.map.getObjectsInfoAt(coord[0], coord[1], ignoreObject=player)
                    if itemList is not None:
                        for mapObjectId in itemList:
                            if mapObjectId == lastObject.id:
                                self.data.setLastTouch(None)
                                break
                    
    def checkForAutomaticMovement(self): 
        """ Called only from the UI Loop.  Move with the saved direction"""
        if self.goalCoordinates != None:
            while len(self.mouseMoves) > 0:
                if not self.canvas.movementHalted: 
                    self.map.performAutomaticMovement(self.mouseMoves, standardCheck=True, showMovement=True)
                self.goalCoordinates = None
                self.mouseMoves.clear()
                if len(self.queuedEvents) > 0:
                    self.mouseEvent = self.queuedEvents.pop(0)
                    self.checkForMouseMovement()

        return self.goalCoordinates is not None
    
    def determineMouseMoves(self, newSpot, objectBox):
        """ Determine a series of mouse moves to get to a location. Allows scrolling to work."""
        # Mouse movement based on OS type must be used when calculating movement
        x_offset = 1
        y_offset = 1
        if self.map is not None:
            x_offset += self.map.os_x_adjustment
            y_offset += self.map.os_y_adjustment

        # Offset from center of object
        x1 = objectBox[0] + abs(objectBox[2]-objectBox[0])/2
        y1 = objectBox[1] + abs(objectBox[3]-objectBox[1])/2
        x_diff = newSpot[0] - x1
        y_diff = newSpot[1] - y1

        # Direction as a letter
        testString = ""
        vertical = "U" if y_diff < 0 else "D"
        horizontal = "L" if x_diff < 0 else "R"
        count = int(abs(x_diff/x_offset) + abs(y_diff/y_offset))

        mouseMoves = bytearray(int(count/2)+1)
        each_x = abs(x_diff / count ) if count > 0 else 1.0
        xCount = 0.0
        limit = x_offset
        for i in range(count):
            xCount += each_x
            if xCount >= limit:
                mouseMoves.insert(i,ord(horizontal))
                limit += x_offset
                testString += horizontal
            else:
                mouseMoves.insert(i,ord(vertical))
                testString += vertical

        #print(f"From ({x1},{y1}) to {newSpot} with diff({x_diff},{y_diff})= {testString}")
        return mouseMoves
    
    def checkForMouseMovement(self):
        """ Check for a mouse movement to save point selected"""
        if self.mouseEvent != None:
            localEvent, self.mouseEvent = self.mouseEvent, None

            # If a mouse goal is in progress, set the waiting goal for later processing
            if not self.canvas.movementHalted: 
                if self.goalCoordinates == None:
                    self.goalCoordinates = ( int(localEvent.x), int(localEvent.y) )
                    #print(f"Mouse click setting goal to {self.goalCoordinates}")
                else:
                    self.queuedEvents.append(localEvent)

                # Determine the movements needed to reach the goal
                if self.map.centerObject != None:
                    objectBoxCoordinates = self.canvas.widget.bbox(self.map.centerObject.id)
                    self.mouseMoves = self.determineMouseMoves(self.goalCoordinates, objectBoxCoordinates)
    
    def clearAutomaticMouseMovements(self):
        """Clear any automatic mouse movements"""
        self.canvas.movementHalted = True
        self.mouseEvent = None
        self.mouseMoves.clear()
        self.queuedEvents.clear()
        self.canvas.movementHalted = False

    def checkForKeyMovement(self):
        """ Check for keystrokes, process any found """

        # Circumstances when keystrokes are ignored
        if not self.keyActive: return
        if self.canvas.movementHalted: return

        somethingDone = False
        multipleMovesList = []
        
        for direction, beingHeldDown in self.keys.items():
            if beingHeldDown:
                
                # Once found, place them is a list 
                somethingDone = True
                if self.wasd_keys_allowed: # convert wasd into cardinal names first
                    if direction in self.wsad:
                        index = self.wsad.index(direction)
                        direction = self.direction[index]
                multipleMovesList.append(direction)
                
        # Pass this on noting any listing of multiple keys being activated at once
        if somethingDone:        
            self.map.movingList(multipleMovesList, smoothMovement=True)
            #self.canvas.update(MACOS_PAUSE)

        self.keyActive = somethingDone
    
    def cleanKeyMovements(self):
        """Remove any key combinations that are not used (shift-W as an example)"""
        for key in self.keys: 
            if key not in self.direction and key not in self.wsad:
                self.keys[key] = None

    def checkForAnimations(self):
        pass

    def stop(self):
        self.timerCentral.stop()

    ########################## MAIN LOOP ########################
    def loopForUI(self):
        self.checkForKeyMovement()
        self.checkForMouseMovement()
        automaticLooping = self.checkForAutomaticMovement()
        if automaticLooping:
            while automaticLooping:
                self.checkForAnimations()
                self.timerCentral.oneSecondCheck()
                automaticLooping = self.checkForAutomaticMovement()
        else:
            self.checkForAnimations()
            self.timerCentral.oneSecondCheck()
        self.root.after(self.UIloopTime, self.loopForUI) # set the refresh rate here ... Smaller number means faster scrolling