__version__ = "8.0"
class ItemClass():
    """ Item Class is for miscelaneouss items in the game. Generally nonresponsive NPCs if 
    they are not alredy their own class. Item Class object do something normal objects do not.
    Nonresponsive NPCs may be items that are just graphics added later in the game and/or items that
    are activiated only by other events. Child classes can initialize or remove actions and messages. 
    If the item kind or name is in the Game Object data, specific actions and messages can be modified 
    for a specific item or kind of item.
    PARAMETERS:
         data:       all game data
         dictionary: required dictionary object for item characteristics
         arguments:  
         dictionary:
    
    """

    def __init__(self, data, dictionary, *args, **kwargs):
        self.data = data
        self.map = data.getResource('map')
        self.arguments = args
        self.dictionary = kwargs

        # Possible things the item can do
        self.Attacking = 1 # Attack Player, then defend
        self.Defending = 2 # In process of defending against player
        self.Ignoring = 3 # Ignores player
        self.Leaving = 4 # Leaving for example when a player has a sword
        self.NoLongerHere = 5 # Has left the map
        self.NotActivated = 6 # First time in
        self.Sleeping = 7 # Sleeping, similar to ignore but a temporary condition
        self.Wakingup = 8 # Awake and will leave peacibly
        self.Hiding = 9 # Disappears but is still there
        self.Unhiding = 10 # Appears or reappears
        self.Exploding = 11 # Boom
        self.Saying = 12 # Just says something

        # Characteristics
        self.gender = dictionary.pop("gender", "it")
        self.Gender = self.gender[0].upper() + self.gender[1:]
        self.instructions = None
        self.mapObject = None
        self.Item = None
        self.ItemName = args[0] if len(args) > 0 else dictionary.get("Name",'')
        self.ItemDictionary = dictionary
        self.ItemKind = None
        self.ItemMatch = self.NotActivated
        self.lastItemMatch = None
        self.DefaultAction = None
        self.chaseCounter = 0
        self.chaseMaximum = 300
        self.idleCounter = 0
        self.ItemHasLeft = False
        self.returningToHome = False
        self.chaseAlreadySuccessful = False
        self.wayBackHome = [] # List holding points to return home
        self.player = None
        self.instructionsToPlayer = ""
        self.status = ""
        self.sound = ""
        self.looping = False # Loop thru action the item can do, some actions lead to other actions
        
        # Dictionary of standard possible actions. These can be added to for child classes (example Spider Class)
        self.actions = {
            self.NoLongerHere: self.noLongerHere,
            self.NotActivated: self.activation,
            self.Attacking: self.attacking,
            self.Wakingup: self.wakingup,
            self.Defending: self.defending,
            self.Ignoring: self.ignoring,
            self.Sleeping: self.sleeping,
            self.Leaving: self.leaving,
            self.Exploding: self.exploding,
            self.Unhiding: self.unhide,
            self.Hiding: self.hide,
            self.Saying: self.saying
        }
        
        # Generic messages to player, override for other NPCs
        self.messageDictionary = {
            "chasing":"  {0} is chasing you!",
            "chasing status":"  {0} is chasing you!",
            "chasing retort":"Better run...!",
            "chasing sound":"Scream",

            "catching":"  {0} catches you!",
            "catching status":"  {0} catches you!",
            "catching weapon":'  {0} says {1} "is not impressed with your {2}"',
            "catching retort":", but {0} will leave!",
            "catching sound":"Scream",

            "fleeing":"  {0} is fleeing from you!",
            "fleeing status":"  {0} is fleeing from you!",
            "fleeing sound":"Scream",
            
            "attacking":"  {0} is attacking you!!",
            "attacking status":"  {0} is attacking you!!",
            "attacking weapon":"  {0} says {1} are not impressed with your {12}!",
            "attacking damage":'  {0} does point out you may have damaged your {0} when you missed and hit the floor!',
            "attacking retort":"  {0} says you are a wimp!",
            "attacking sound":"Scream",

            "defending":"  {0} is defending itself!",
            "defending status":"  {0} is defending itself!",
            "defending weapon":"  {0} defended itself!",
            "defending axe":"  {0} defended itself against your shinny {1}!",
            "defending retort":", but {0} will leave!",
            "defending sound":"Scream",

            "wakingup":"  {0} wakes up!",
            "wakingup status":"  {0} wakes up!",
            "wakingup weapon":"  {0} wakes up!",
            "wakingup retort":" and {0} will leave!",

            "sleeping":"  {0} is asleep.",
            "sleeping status":"  {0} is asleep. Shhhh!",
            "exploding":"  {0} just exploded!",
            "exploding status":"  {0} just exploded, perhaps you noticed!",

            "reapearing":" {0} suddenly reappears!",
            "disappearing":"  {0} suddenly disappears!",
            "saying":"",
            "ignoring":""
        }       
        
        self.activation()

        ##############################            
    def resetMessages(self):
        for key in self.messageDictionary:
            self.messageDictionary[key] = ""
    
    def addAction(self, function):
        length = len(self.actions) + 1
        self.actions[length] = function
        return length

    def returnFunction(self, functionName, *args):
        if self.ItemHasLeft: return None
        resultFunction = self.functions.get(functionName, None)
        return resultFunction
    
    def activation(self, *args):
        if self.mapObject is None:
            self.mapObject = self.ItemDictionary.get("MapObject", None)
            if self.mapObject is  None:
                self.ItemMatch = self.ItemHasLeft
                return None
            
            self.mapObject.autoDraw = True # If a delayed draw, draw it now. Ignored if already drawn
            self.mapObject.draw() 
            self.ItemId = self.mapObject.id 
            self.functions = {"saying": self.saying, "chasing": self.chaseFunction, "fleeing": self.fleeFunction }
     
        if self.ItemMatch == self.NotActivated:
            self.ItemMatch = self.Ignoring
            
        if len(args) > 0: # Next activity to do provided as optional parameter
            if isinstance(args[0],int):
                try:
                    self.ItemMatch = args[0]
                    if self.ItemMatch not in self.actions:
                        self.ItemMatch = self.Ignoring
                except:
                    pass
        self.activate()
    
    def chaseFunction(self, *args):
        if self.ItemMatch == self.NotActivated: self.activation()

        message = self.messageDictionary.get("chasing status","")
        self.status = message.format(self.ItemName)
        message = self.messageDictionary.get("chasing","")
        retort = self.messageDictionary.get("chasing retort","")
        self.instructionsToPlayer = message.format(self.ItemName) + retort.format(self.ItemName)
        self.sound = self.messageDictionary.get("chasing sound","")
        self.displayResult()

        self.caseCounter = 0
        self.chaseAlreadySuccessful = False
        self.ItemMatch = self.Defending
        if self.player is None: self.player = self.data.getResource('player')
        self.chasing()
        
    def fleeFunction(self, *args):
        if self.ItemMatch == self.NotActivated: self.activation()

        message = self.messageDictionary.get("fleeing status","")
        self.status = message.format(self.ItemName)
        message = self.messageDictionary.get("fleeing","")
        retort = self.messageDictionary.get("fleeing retort","")
        self.instructionsToPlayer = message.format(self.ItemName) + retort.format(self.ItemName)
        self.sound = self.messageDictionary.get("fleeing sound","")
        self.displayResult()

        self.chaseCounter = 0
        if len(args) == 2 and type(args[0]) == int and type(args[1]) == int:# coordinate to run to or just away from the player if no coordinate
            self.flee_x = args[0]
            self.flee_y = args[1]
        else:
            if self.player is None: self.player = self.data.getResource('player')

            playerMapCenter = self.player.getPosition()
            playerCenter = self.map.convertMapCoordinatesToStandard(playerMapCenter[0], playerMapCenter[1])
            myCenterPoint = self.mapObject.getCenter()
            ItemCenter = self.map.convertMapCoordinatesToStandard(myCenterPoint.x, myCenterPoint.y)

            x_diff = min(400,max(-400,abs(  abs(ItemCenter[0]) -  abs(playerCenter[0]) )))
            y_diff = min(400,max(-400,abs(  abs(ItemCenter[1]) -  abs(playerCenter[1]) )))
            self.flee_x = ItemCenter[0] - x_diff if ItemCenter[0] > playerCenter[0] else ItemCenter[0] + x_diff
            self.flee_y = ItemCenter[1] - y_diff if ItemCenter[1] > playerCenter[1] else ItemCenter[1] + y_diff
        
        self.ItemMatch = self.Leaving
        self.fleeing()

    def saying(self, *args):
        if self.ItemMatch == self.NotActivated: self.activation()
        self.sound =  self.messageDictionary.get("saying","")
        self.ItemMatch = self.Ignoring
        
    def fleeing(self, *args):
        """ Function to flee from the player or to a place. Will repeat independently until the Item is at that location"""
        myCenterPoint = self.mapObject.getCenter()
        if myCenterPoint is not None:
            myCenter = self.map.convertMapCoordinatesToStandard(myCenterPoint.x, myCenterPoint.y)
            x = 1 if myCenter[0] > self.flee_x else -1 if myCenter[0] < self.flee_x else 0
            y = 1 if myCenter[1] > self.flee_y else -1 if myCenter[1] < self.flee_y else 0
            if x != 0 and y != 0:
                self.mapObject.move(x,y)
                self.mapObject.canvas.update()
                self.data.root.after(40, self.fleeing)
            else:
                self.activate(self.ItemMatch)
        else:
            self.data.logError("Item Class for ", self.dictionary["name"], 
                               "has a fleeing error as there is an invalid mapObject center point")

    def returnToHome(self, *args):
        x,y = self.wayBackHome.pop() if len(self.wayBackHome) > 0 else (0,0)
        if x >0 or y > 0:
            self.mapObject.move(x,y)
            self.mapObject.canvas.update()
            self.data.root.after(40, self.returnToHome)

        # Clear out variables, no repeat of the function
        else:
            self.wayBackHome.clear()
            self.activate(self.ItemMatch)
    
    def chasing(self, *args):
        """ Function to chase the player. Will repeat until the Item is back at her Home or
        has stolen from the player. """

        # There is a limit to how mach chasing will occur 
        if self.chaseCounter >= self.chaseMaximum:
            self.chaseCounter = 0
            self.ItemMatch = self.Defending
            self.data.root.after(20, self.returnToHome)

        # Chase the player and check for a contact
        else:
            self.chaseCounter += 1
            playerMapCenter = self.player.getPosition()
            playerCenter = self.map.convertMapCoordinatesToStandard(playerMapCenter[0], playerMapCenter[1])
            myCenter = self.mapObject.getCenter()
            ItemCenter = self.map.convertMapCoordinatesToStandard(myCenter.x, myCenter.y)
            x = -1 if ItemCenter[0] > playerCenter[0] else 1 if ItemCenter[0] < playerCenter[0] else 0
            y = -1 if ItemCenter[1] > playerCenter[1] else 1 if ItemCenter[1] < playerCenter[1] else 0
            self.mapObject.move(x,y)
            if x != 0: x = -x
            if y != 0: y = -y
            self.wayBackHome.append((x,y))
            self.map.canvas.update()

            # Check if contact is made
            chaseSuccessful = self.data.objectsTouch(self.mapObject, self.player)
            lastObjectTouched = self.data.getLastTouch()

            # If this is the same object as last time (and it is this Item object), continue to the Home
            if lastObjectTouched.id == self.mapObject.id:
                self.chaseCounter = 0
                self.data.root.after(1000, self.returnToHome)
            
            # If successful contact with a new object (which is this Item)
            elif chaseSuccessful:
                self.chaseCounter = 0
                self.ItemMatch = self.Defending

                # Insure a valid touch and not a double touch
                lastObjectTouched = self.data.getLastTouch()
                if lastObjectTouched.id != self.mapObject.id:
                    self.data.setLastTouch(self.mapObject)

                    message = self.messageDictionary.get("catching status","")
                    self.status = message.format(self.ItemName)
                    message = self.messageDictionary.get("catching","")
                    retort = self.messageDictionary.get("catching retort","")
                    self.instructionsToPlayer = message.format(self.ItemName) + retort.format(self.ItemName)
                    self.sound = self.messageDictionary.get("catching sound","")
                    self.displayResult()

                # Get ready to return to the Home
                self.ItemMatch = self.Leaving
                self.data.root.after(1000, self.returnToHome)

            else: # Continue chasing
                self.data.root.after(30, self.chasing)

    def attacking(self, *args):
        self.data.setLastTouch(self.mapObject)
        weapon = self.player.nameOfWeapon()

        message = self.messageDictionary.get("attacking status","")
        self.status = message.format(self.ItemName)
        self.sound = self.messageDictionary.get("attacking sound","")

        message = self.messageDictionary.get("attacking","")
        message = message.format(self.ItemName)

        if weapon is None:
            self.caseCounter = 0
            self.chaseAlreadySuccessful = False
            self.ItemMatch = self.DefaultAction
            retort = self.messageDictionary.get("attacking retort","")
            self.instructionsToPlayer = message + retort.format(self.ItemName)
            self.displayResult()
            self.chasing() 
        else:
            damaged = self.player.weaponIsDamaged()
            if damaged:
                retort = self.messageDictionary.get("damaging weapon","")
            else:
                retort = self.messageDictionary.get("attacking weapon","")
            self.instructionsToPlayer = message + retort.format(self.ItemName, self.gender, weapon)
                    
        self.ItemMatch = self.Defending

    def wakingup(self, *args):
        self.data.setLastTouch(self.mapObject)

        message = self.messageDictionary.get("wakingup status","")
        self.status = message.format(self.ItemName)
        message = self.messageDictionary.get("wakingup","")
        retort = self.messageDictionary.get("wakingup retort","")
        self.instructionsToPlayer = message.format(self.ItemName) + retort.format(self.ItemName)
        self.sound = self.messageDictionary.get("wakingup sound","")

        weapon = self.player.nameOfWeapon()
        if weapon is None:
            self.ItemMatch = self.Ignoring
        else:
            self.ItemMatch = self.Defending
        self.looping = False

    def defending(self, *args):
        self.data.setLastTouch(self.mapObject)

        message = self.messageDictionary.get("defending status","")
        self.status = message.format(self.ItemName)
        message = self.messageDictionary.get("defending","")
        message = message.format(self.ItemName)
        self.sound = self.messageDictionary.get("defending sound","")        
        
        weapon = self.player.nameOfWeapon()
        if weapon is None:
            retort = ""
            weaponRetort = ""
            self.ItemMatch = self.Defending
            self.looping = False
        else:
            if weapon.lower() == "axe":
                weaponRetort = self.messageDictionary.get("defending axe","")
            else:
                weaponRetort = self.messageDictionary.get("defending weapon","")
            weaponRetort = weaponRetort.format(self.ItemName, weapon)
            retort = self.messageDictionary.get("defending retort","")
            self.ItemMatch = self.Leaving

        retort = weaponRetort + retort.format(self.ItemName, weapon)
        self.instructionsToPlayer = message + retort

    def ignoring(self, *args):
        self.data.setLastTouch(self.mapObject)
        
        message = self.messageDictionary.get("ignoring status","")
        self.status = message.format(self.ItemName)
        message = self.messageDictionary.get("ignoring","")
        retort = self.messageDictionary.get("ignoring retort","")
        self.instructionsToPlayer = message.format(self.ItemName) + retort.format(self.ItemName)
        self.sound = self.messageDictionary.get("ignoring sound","")

        self.looping = False

    def sleeping(self, *args):
        self.data.setLastTouch(self.mapObject)

        message = self.messageDictionary.get("sleeping status","")
        self.status = message.format(self.ItemName)
        message = self.messageDictionary.get("sleeping","")
        retort = self.messageDictionary.get("sleeping retort","")
        self.instructionsToPlayer = message.format(self.ItemName) + retort.format(self.ItemName)
        self.sound = self.messageDictionary.get("sleeping sound","")

        self.ItemMatch = self.Sleeping
        self.looping = False

    def leaving(self, *args):
        if not self.ItemHasLeft:
            self.ItemHasLeft = True
            self.ItemMatch = self.NoLongerHere
            timers = self.data.getResource("timers")
            timers.timerCentral.addTimer("UndrawItem", 1, 0, self.mapObject.undraw)
        else:
            self.sound = ""
            self.status = ""
            self.instructionsToPlayer = ""
        self.looping = False
            
    def exploding(self, *args):
        self.mapObject.Disappear()
        
        message = self.messageDictionary.get("exploding status","")
        self.status = message.format(self.ItemName)
        message = self.messageDictionary.get("exploding","")
        retort = self.messageDictionary.get("exploding retort","")
        self.instructionsToPlayer = message.format(self.ItemName) + retort.format(self.ItemName)
        self.sound = self.messageDictionary.get("exploding sound","")

        self.ItemMatch = self.Leaving     
        self.looping = False
 
    def unhide(self, *args):
        self.mapObject.unhide()
        
        message = self.messageDictionary.get("unhide status","")
        self.status = message.format(self.ItemName)
        message = self.messageDictionary.get("unhide","")
        retort = self.messageDictionary.get("unhide retort","")
        self.instruction = message.format(self.ItemName) + retort.format(self.ItemName)
        self.sound = self.messageDictionary.get("unhide sound","")

        self.ItemMatch = self.Ignoring
        self.looping = False
                    
    def hide(self, *args):
        self.mapObject.hide()

        message = self.messageDictionary.get("hide status","")
        self.status = message.format(self.ItemName)
        message = self.messageDictionary.get("hide","")
        retort = self.messageDictionary.get("hide retort","")
        self.instruction = message.format(self.ItemName) + retort.format(self.ItemName)
        self.sound = self.messageDictionary.get("hide sound","")

        self.ItemMatch = self.Ignoring      
        self.looping = False     
            
    def noLongerHere(self, *args):
        self.looping = False

    def anythingElse(self, *args):
        self.ItemMatch = self.Ignoring
        self.idleCounter += 1
        
        # If this keeps happening, the Item should leave
        if self.idleCounter > 4:
            self.data.setLastTouch(self.mapObject)
            instructionsToPlayer = self.messageDictionary.get("leaving","")
            if len(instructionsToPlayer) > 0:
                self.instructionsToPlayer = instructionsToPlayer.format(self.ItemName)
            self.ItemHasLeft = False # Just to make sure
            self.ItemMatch = self.Leaving
        self.looping = False
        
    def displayResult(self):
        # Display any sound, instruction or status provided by the item
        if len(self.instructionsToPlayer) > 0: 
            instructions = self.data.getResource('instructions')
            if instructions is not None: 
                instructions.newSection(self.instructionsToPlayer)
                self.instructionsToPlayer = ""
        if len(self.status) > 0: 
            statusBar = self.data.getResource('statusBar')
            if statusBar is not None: 
                statusBar.set(self.status)
                self.status = ""
        if len(self.sound) > 0: 
            if not self.ItemHasLeft:
                soundMixer = self.data.getResource('soundMixer')
                if soundMixer is not None: 
                    soundMixer.playSound(self.sound)
                    self.sound = ""
        self.data.canvas.update()

    def activate(self, *args):
        """ Function to activate the Item. Matching can setup the next matching so loop until no more matching is needed. """
        if self.chaseCounter > 0: return # No activation while chasing
        self.looping = True
        self.data.stopMoving()
        self.mapObject.dictionary["Action"]="Activate"
        if self.player is None: self.player = self.data.getResource('player')
        nextActivity = self.ItemMatch
        if len(args) > 0: # Next activity to do provided as optional parameter
            if isinstance(args[0],int):
                try:
                    nextActivity = args[0]
                    if nextActivity not in self.actions:
                        nextActivity = self.Ignoring
                except:
                    pass

        # Loop the item's activity until itis done doig things
        while self.looping:
            self.lastItemMatch = self.ItemMatch
            if nextActivity is None:
                self.looping = False
            else:
                self.ItemMatch = nextActivity
                action = self.actions.get(self.lastItemMatch, self.anythingElse)
                action(*args)
                self.displayResult()
            if self.looping:
                nextActivity = self.ItemMatch
            
        # Loop ends here
    # Activate ends here