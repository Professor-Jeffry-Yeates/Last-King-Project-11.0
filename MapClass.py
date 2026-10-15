__version__ = "11.0"
import threading, os, math, queue
import tkinter as tk
import random, math
from CoffeeBean import *
from CoffeeCanvas import *
from MultitaskingClasses import ProgressBarClass

# Identifies each possible color in the path map
MAP_BLACK = 0
MAP_RED = 1
MAP_GREEN = 2
MAP_BLUE = 4
MAP_YELLOW = MAP_RED + MAP_GREEN
MAP_CYAN = MAP_GREEN + MAP_BLUE
MAP_MAGENTA = MAP_RED + MAP_BLUE
MAP_WHITE = MAP_RED + MAP_GREEN + MAP_BLUE

MACOS_PAUSE = 30
standardFont = ("TKDefaultFont", 12)
standardFormat = dict( sticky="fullwidth", borderwidth=0, background="White", font=standardFont )
frameFormat = dict( sticky="full", relief=tk.SOLID, borderwidth=1, font=(standardFont[0], standardFont[1], 'bold italic'), pady=5)
plainFrameFormat = dict( sticky="full", font=(standardFont[0], standardFont[1], 'bold italic'), pady=5)

class MapInterface():
    def __init__(self, map, *arguments, **dictionary):
        """Initialize the MapInterface Mixin class.  This is a Python mixin class that provides the map() function to the object.
        # Certain arguments are processed separately or processed later as they
        #   are not part of standard Tkinter.  Acts like an "interface" in other languages.
        It will store function use and other values in the object it is in.
        An idea: standard commands in a list, ["fade","remove"]  or ['fade','trigger','name of object','remove],
        or ["fadedirection","delay",10,"untouched",'fadein','reset']"""
        self.map = map
        self.data = None # Data object so actions can affect anything
        self.question = None # Current question dictionary
        self.right = 0 # Results of answering the question (beyond success, accessible by all reward and penalty functions)
        self.wrong = 0
        self.questionFunctionsInitialized = False # True if the question has been initialized, affect answering later
        self.providedQuestion = None
        self.interactive = dictionary.get('interactive',True) # Can interact with other objects
        self.invisibleObject = dictionary.get('invisible',False) # Invisible object that can interact with other objects
        self.transport = dictionary.get('transport', False) # Can be traveled over like a path
        if self.invisibleObject: self.interactive = True
        self.argumentDictionary = dictionary.get('argumentDictionary', {})
        self.noFailure = False # If True, no failure function is called

    def addAction(self, action):
        if action != None:
            if type(action) == str:
                actionList = action.split(',')
                for activity in actionList:
                    defaultAction = self.data._retrieveFunctionFromAction(activity)#   self._getAction(activity)
                    if defaultAction != None and callable(defaultAction): 
                        self.actions.append(defaultAction)
                        self.interactive = True
            elif callable(action):
                self.actions.append(action)
                self.interactive = True
            elif type(action) == list:
                for eachAction in action:
                    if eachAction == None: continue
                    if type(eachAction) == str:
                        actionList = eachAction.split(',')
                        for activity in actionList:
                            defaultAction = self.data._retrieveFunctionFromAction(activity) #   self._getAction(activity)
                            if defaultAction != None and callable(defaultAction): 
                                self.actions.append(defaultAction)
                                self.interactive = True
                    elif callable(eachAction):
                        self.actions.append(eachAction)
                        self.interactive = True
    def clearActions(self):
        """Clear all actions for this object"""
        self.actions.clear()
        self.interactive = False

    def callActions(self, *args):
        """Call all functions in the self.actions[] list in order"""
        if len(self.actions) > 0:
            for function in self.actions:
                if isinstance(function, list):
                    for nestedFunction in function:
                        if nestedFunction != None:
                            nestedFunction(self, *args)
                elif function != None:
                    function(self, *args)
                    
    def getOriginalImagePixel(self, x, y, opacity=False):
        """Returns a list [r,g,b] with the RGB color values for pixel (x,y)
        r,g,b are in range(256) """
        value = self.originalImage.get(x,y) 
        if type(value) ==  type(0):
            return [value, value, value]
        elif type(value) == type((0,0,0)):
            return list(value)
        else:
            return list(map(int, value.split())) 
    
    def addItem(self, item):
        """Add an item to the inventory"""
        if item not in self.items:
            self.items.append(item)
            # Update the canvas or display the item
            # (Implementation depends on how items are represented visually)

class MapImage( SmartImage, MapInterface):
    def __init__(self, map, *args, **kwargs):
        super().__init__(map.canvas, *args, **kwargs)
        MapInterface.__init__(self, map, *args, **kwargs)
        self.PILimage = None if self.image == None else PILImage.open(self.fullPath)
         
class MapCircle( Circle, MapInterface):
    def __init__(self, map, *args, **kwargs):
        canvas = map.canvas
        super().__init__(canvas, *args, **kwargs)
        MapInterface.__init__(self, map, *args, **kwargs)

class MapRectangle( Rectangle, MapInterface):
    def __init__(self, map, *args, **kwargs):
        canvas = map.canvas
        super().__init__(canvas, *args, **kwargs)
        MapInterface.__init__(self, map, *args, **kwargs)

class MapPolygon( Polygon, MapInterface):
    def __init__(self, map, *args, **kwargs):
        canvas = map.canvas
        super().__init__(canvas, *args, **kwargs)
        MapInterface.__init__(self, map, *args, **kwargs)

class PhantomMapClass(MapInterface):
    """A phantom map object that does nothing, used when no map object is provided but one is needed to hold a question"""
    def __init__(self, data, *args, **kwargs): #self, parent, map, name="Phantom"):
        
        self.parent = args[0] if len(args) > 0 else data
        self.map = data.map
        self.npc = kwargs.get("npc",True)
        if self.npc:
            self.name = self.parent.name
        else:
            self.name = kwargs.get("name",'object')
        self.PILimage = None 
        super().__init__(self, data.map, *args, **kwargs)
        self.data = data   
        self.map = data.map
        self.dictionary = {}
        
    # Negate these functions associated with a mapObject
    def addAction(self, action): pass
    def getOriginalImagePixel(self, *args, **kwargs): return [0,0,0]
    def draw(self): pass
    def undraw(self):  self.parent.phantomObject = None
    def delete(self):  self.parent.phantomObject = None
    def move(self, *args, **kwargs): pass

class LastQuestionClass(PhantomMapClass):
    """Last question asked"""
    def __init__(self, data, *args, **kwargs): 
        super().__init__(data, self, *args, npc=False, name="Last Question", **kwargs)
        self.question = kwargs.get("question", None)
        if self.question is not None: self.question["ProvidedObject"] = False
        self.noFailure = kwargs.get("noFailure", True)

class BasicMapClass():
    """A class to create a map with scrolling and object movement.  If no scrolling provide it is a plain canvas.
    Below are the available options for the dictionary defining canvas characteristics:"""

    def logError(self, *args):
        """Log string messages to a log file."""
        with open("log.temp", "a") as log_file:
            for arg in args:
                log_file.write(arg)
                log_file.write("\n")
        pass
    logError = staticmethod(logError)

    def __init__(self, topCanvas, **kwargs):
        DEFAULT_MAP_SIZE = 500 # default map-square on the screen
        DEFAULT_MOVEMENT = 1

        dictionary = dict(**kwargs)
        self.movement = dictionary.get('movement', DEFAULT_MOVEMENT) # Movement increment
        self.scrollFractionalIncrement = float(dictionary.get('increment', float(DEFAULT_MOVEMENT))) # Scroll fractional increment, move when > 1
        self.scrollIncrement = DEFAULT_MOVEMENT
        self.os_y_adjustment = 0 # MacOS is very slow
        self.os_x_adjustment = 0
        self.mouseOnly = dictionary.get('mouseOnly', False) # When True, only mouse input is accepted, otherwise mouse and keys
        self.scrollWidth = dictionary.get('scrollWidth', None) # Width of scrollable part of canvas.  Can be much larger than width
        self.scrollHeight = dictionary.get('scrollHeight', None) # Height of scrollable part of canvas.  Can be much larger than height
        self.mapImageName = dictionary.get('mapImage', None) # Main background map 
        self.tags = "Unknown" if self.mapImageName == None else self.mapImageName
        self.mapPathName = dictionary.get('mapPath', None) # Optional path map for the main map
        self.visibleWidth = dictionary.get('width', DEFAULT_MAP_SIZE) # Width of visible part of canvas
        self.visibleHeight = dictionary.get('height', DEFAULT_MAP_SIZE) # Height of visible part of canvas
        self.visibleWidth = int(self.visibleWidth)
        self.visibleHeight = int(self.visibleHeight)
        self.background = dictionary.get('background', "White") # Background color of canvas
        self.x = dictionary.get('x', None) # Initial and absolute positioning in a larger canvas
        self.y = dictionary.get('y', None) 
        self.wasd_keys_allowed = topCanvas.wasd_keys_allowed # Additional key input beside arrow keys
        self.mouseOnly = dictionary.get('mouseOnly', False) # When True, only mouse input is accepted, otherwise mouse and keys
        self.x_summary = 0.0 # Movement may be fractional that builds up to an integer movement
        self.y_summary = 0.0 #  as the mini-map is probably smaller than the main map
        self.positioning = None # Positioning used to track movement (big map only)
        self.data = dictionary.get('data', None) # Data object to use for actions and questions
        self.flyingAllowed = False # True if the player can fly(ignores all collisions and terrain)
        self.followCenterPath = dictionary.get('followCenterPath', False) # If True, only the center point of the object is checked for path movement, not the edge points.  This is used for objects that are small enough to fit within the path lines, such as a player icon.

        # Setup initial map dimensions
        self.width = self.visibleWidth
        self.height = self.visibleHeight
        self.image = None 
        self.pathImage = None
        self.imageID = None
        
        # Init for any remote maps or minimaps that scroll in concert with this one
        self.remoteMap = None # Connection to a remote map moving in concert to this one
        self.mainMap = None # Connection to the main map moving in concert with it

        # If a background map is provided, use
        if self.mapImageName != None:
            try:
                self.image = tk.PhotoImage(file=self.mapImageName)
                self.pathImage = self.image # Default is the path image when the same as the map imageself.pathImage = self.Image # Default is the path image when the same as the map image
                self.width = self.image.width()
                self.height = self.image.height()
                self.scrollWidth = int(self.width)
                self.scrollHeight = int(self.height)
            except:
                self.image = NotImplemented

        # Configure the rectangle of the entire scrolling area
        halfWidth = self.width // 2
        halfHeight = self.height // 2
        self.imageUpper_x = halfWidth
        self.imageUpper_y = halfHeight
        self.MaxTop = int(-halfHeight)
        self.MaxBottom = int(halfHeight)
        self.MaxLeft = int(-halfWidth)
        self.MaxRight = int(halfWidth)
 
        # Rectangle limits where the object can move to, but will adjust later for any object size
        self.MaxTopEdge = self.MaxTop
        self.MaxBottomEdge = self.MaxBottom
        self.MaxLeftEdge = self.MaxLeft
        self.MaxRightEdge = self.MaxRight

        # Initialize scrolling and check if there is scrolling 
        self.horizontalScrollAvailable = False
        self.verticalScrollAvailable = False
        self.scrollingAvailable = False
        if self.scrollWidth != None and self.scrollHeight != None:
            self.horizontalScrollAvailable = True
            self.verticalScrollAvailable = True
            self.scrollingAvailable = True

        # Configure the rectangle where scrolling will occur (otherwide the center object just moves without scrolling)
        self.MaxScrollTop = int(self.MaxTop + self.visibleHeight//2)
        self.MaxScrollBottom = int(self.MaxBottom - self.visibleHeight//2)
        self.MaxScrollLeft = int(self.MaxLeft + self.visibleWidth//2)
        self.MaxScrollRight = int(self.MaxRight - self.visibleWidth/2)
        self.middleTuple = int(self.visibleWidth/2),int(self.visibleHeight/2)

        # Optional center graphic element to move over the map.
        self.centerObject = None 
        self.centerObjectWidth = 0
        self.centerObjectHeight = 0
        self.objectPosition = None # Location to start the central object

        # Initialize user input
        self.looping = False
        self.userKeyInput = False
        self.mouseEvent = None
        self.x_adjustment = 0
        self.y_adjustment = 0
        self.keys = dict.fromkeys(('Left', 'Right', 'Up', 'Down'))
        WASDkeys = dict.fromkeys(('a','d','w','s'))
        if self.wasd_keys_allowed: self.keys.update(WASDkeys)
        self.special = False # Special key input that is not movement, example "x" key for debugging movement
        self.specialList = []

        # Construct the parent canvas and the map
        self.canvas = Canvas(topCanvas, x=self.x, y=self.y, width=self.visibleWidth, height=self.visibleHeight, background="Black")
        self.canvas.bindingAllowed = topCanvas.bindingAllowed # Place into instantiation

        coverMap = dictionary.get('coverMap', False) # If True, the map is covered until completed
        if coverMap: # A canvas can cover a canvas, not a Rectangle
            self.makeCoverMap(0, 0, self.width, self.height)        
        canvas = self.canvas.widget
        if self.scrollingAvailable:
            canvas.configure(xscrollincrement=self.movement, yscrollincrement=self.movement)
            canvas.configure(scrollregion=(self.MaxLeft, self.MaxTop, self.MaxRight, self.MaxBottom)) 
        if self.image != None:
            anchor = "nw" 
            self.imageID = canvas.create_image(-self.imageUpper_x, -self.imageUpper_y, anchor=anchor, image=self.image)
    
    def getCurrentCenterLocation(self):
        return (int(self.scrollWidth//2),int(self.scrollHeight//2))

    def getPixel(self, x, y, opacity=False):
        """Returns a list [r,g,b] with the RGB color values for pixel (x,y)
        r,g,b are in range(256) """
        value = self.image.get(x,y) 
        if type(value) ==  type(0):
            responseList = [value, value, value]
        elif type(value) == type((0,0,0)):
            responseList = list(value)
        else:
            responseList = list(map(int, value.split())) 
        if opacity:
            number = self.image.transparency_get(x,y)
            if isinstance(number,bool): number = 255
            responseList.append(number)
        return responseList

    def getMapPathColor(self, number):
        """Returns the color name for a given number in the path map"""
        if number == MAP_BLACK: return "Black"
        elif number == MAP_RED: return "Red"
        elif number == MAP_GREEN: return "Green"
        elif number == MAP_BLUE: return "Blue"
        elif number == MAP_YELLOW: return "Yellow"
        elif number == MAP_CYAN: return "Cyan"
        elif number == MAP_MAGENTA: return "Magenta"
        elif number == MAP_WHITE: return "White"
        else:
            return "Black"

    def makeCoverMap(self, *args, **kwargs): # "Initializing..."
        (x, y, width, height) = self.getFourDimensions(args)
        text = kwargs.get('text', "Initializing")
        background = kwargs.get('background', "Black")
        self.coverMapCanvas = Canvas(self.canvas, x=x, y=y, width=width, height=height, background=background)
        self.coverMapMessage = Text(self.coverMapCanvas, self.width/2, self.height/2, text=text, font=("Papyrus", 24 ), color="White")   

    def recenterCoverMap(self):
        """Recenter the cover map canvas to the center of the main map"""
        if self.coverMapCanvas is not None:
            x = int(self.width/2 - self.coverMapCanvas.width/2)
            y = int(self.height/2 - self.coverMapCanvas.height/2)
            self.coverMapCanvas.widget.place(x=x, y=y)

    def removeCoverMap(self):
        if self.coverMapCanvas is not None:
            self.coverMapCanvas.undraw()

    def processHitObject(self, mapObjectHit, *moves):
        """Process the object hit by the center object:
            mapObjectHit is the object hit by the center object or None
            move is the direction of movement, 'Up', 'Down', 'Left', 'Right'"""
        objectHitStatus = False # Assume no hit occurred
        if mapObjectHit is not None:
            if mapObjectHit.interactive:# OK, good interactive object
                if mapObjectHit.transport: # If it can transport then assume it is not a hit
                    objectHitStatus = False # Still false
                else:
                    # If the last object hit is the same as the current one ....
                    lastObjectHit = self.data.getLastTouch() # Get the last object hit
                    if lastObjectHit is not None and lastObjectHit.id == mapObjectHit.id:
                        actionText = mapObjectHit.dictionary.get('Action', None)
                        if actionText is not None:
                            objectHitStatus = False # This object's Use is linked to an action (like a NPC) so make sure the action occurs
                            self.goalCoordinates = None # Stop more automatic movement on a hitting it again
                        else:
                            objectHitStatus = False # Same as last hit, still False
                            return objectHitStatus
                    objectHitStatus = True # Otherwise, if it can't transport the user, assume its a hit
                    if not mapObjectHit.invisibleObject: self.goalCoordinates = None # Stop more automatic movement on a hitting visible object

                # Check for actions whether or not there is a hit as the object is good and interactive
                if len(mapObjectHit.actions) > 0:

                    # Call the actions for the object hit whether a singleton or in a list of functions
                    for function in mapObjectHit.actions:
                        if isinstance(function, list) or isinstance(function, tuple):
                            for nestedFunction in function:
                                if nestedFunction != None: # Did not use callable() as it prevented viable functions
                                    nestedFunction(mapObjectHit, moves)
                        elif function is not None:
                            function(mapObjectHit, *moves)
                            
                # Call any object modifications for the object hit 
                try:
                    modifications =  mapObjectHit.dictionary.get("Modify",None)
                    if modifications is not None:
                        for eachModificationPair in modifications:
                            function, objectModified = eachModificationPair
                            if function is callable and objectModified is not None:
                                function(objectModified, mapObjectHit, *moves)
                except:
                    pass # If there is an error with the modifications, ignore it and move on.
        
    def checkSafeListMovement(self, directionList, standardCheck=True):
        """Check if the object can move in multiple chosen directions"""
        success = False
        widgetFound = None
        x_movement, y_movement, x_adjustment, y_adjustment = 0,0,0,0
        noMovement = (success, widgetFound, y_movement, x_movement)

        # Required elements
        if directionList is None or len(directionList) == 0: return noMovement
        if self.canvas.movementHalted: return noMovement 
        if self.centerObject is None: return noMovement 

        # Get the bounding box for the center object
        try:
            x1, y1, x2, y2 = self.canvas.widget.bbox(self.centerObject.id)
            x_width  = int(abs(x1-x2)/2)
            y_height = int(abs(y1-y2)/2)
        except:
            return noMovement
            
        # Get the new position(s) for the movement into x and/or y directions
        up,down,left,right,special   = False,False,False,False,False # Certain combos are ignored, example not both up and down key presses
        for eachDirection in directionList:
            match eachDirection:
                case 'Up':
                    up = True
                    y_movement -= (self.movement + self.os_y_adjustment )
                case 'Down':
                    down = True
                    y_movement += (self.movement + self.os_y_adjustment )
                case 'Left':
                    left = True
                    x_movement -= (self.movement + self.os_x_adjustment )
                case 'Right':    
                    right = True
                    x_movement += (self.movement + self.os_x_adjustment )
                    
                case "Control_L": # Turn on special debugging
                    if self.canvas.development:
                        special = True
                        if self.special:
                            self.special = False
                            for item in self.specialList: item.delete()
                            self.specialList.clear()
                            self.canvas.update()
                        else:
                            self.special = True
                        if (timers := self.data.getResource("timers")): timers.cleanKeyMovements()

        # No or contradictory key combinations (and all keys with them) are ignored, example not both up and down key presses
        if not any((up,down,left,right,special)): return noMovement # No movement or special key provided
        if (up and down) or (left and right): return noMovement
            
        # Checking the center of the object only uses one point 
        x_center = x1 + int(abs(abs(x1)-abs(x2))/2)
        y_center = y1 + int(abs(abs(y1)-abs(y2))/2)
        if left or right: x_center += x_movement
        if up or down: y_center += y_movement

        # Keep movement of the center object in bounds on the map by checking its center moving out of bounds
        left_limit   = x_center + x_movement 
        top_limit    = y_center + y_movement 
        right_limit  = x_center + x_movement 
        bottom_limit = y_center + y_movement 
        if left and  left_limit   < self.MaxLeftEdge: return noMovement
        if up and  top_limit    < self.MaxTopEdge: return noMovement
        if right and right_limit  > self.MaxRightEdge : return noMovement
        if down and bottom_limit > self.MaxBottomEdge: return noMovement
        
        # If not checking for color movement or not a standard check, return True success with movement now, but no widget found
        if not self.safeMovementCheck or not standardCheck or self.flyingAllowed: 
            return True,widgetFound,x_movement,y_movement
        
        # Get the color of the top most object at the point, but ignore the center object.
        # If it does not have a color, make it the background color.  A blank color is invisible
        # and does not count as None or no color. Invisible object's special code will run instead of other object code
        # if touched, but they do not count toward safe travel.  If the color is not in the safe colors list, return False.
        # Notice: specialObjects will run there own code when touched by the center object

        # get the color of the point from the path, not the map
        x,y = self.adjustForPixelArray(x_center, y_center)
        width = int(self.scrollWidth)
        index = x + y * width
        length = len(self.pathPixels)
        if index > length:
            return noMovement # error, our path array is probably 1 row too large
            
        # Check if the color on the path allows movement
        colorOnPath = self.pathPixels[index] 
        success = False
        if colorOnPath == self.singleSafeColor:
            success = True 
        elif colorOnPath in self.safeColors:
            success = True

        # If so, we might move if not blocked, check if we hit a widget. For this we need to look at the leading point of the movement
        if success:

            # Get the leading point
            x,y = x_center, y_center
            if left: x = x1 + x_movement 
            if up: y = y1 + y_movement 
            if down: y = y2 + y_movement 

            # Check that point for having a widget (not the background and not the center object)
            objectList = self.getObjectsInfoAt(x,y, ignoreObject=self.centerObject)
            if len(objectList) > 0: 

                # Check the top widget's characteristics to see what a hit does 
                id = objectList[0] 
                if id > 1: # continue # Background

                    # Get the widget object based on its id
                    foundApossibleWidget = None
                    widget = self.canvas.items.get(id,None)

                    # Widget found. We hit a widget, check what it can do for a successful hit. 
                    if widget != None:
                        success = False

                        # Actively interactive (which includes invisible widgets) are automatically found
                        invisibleObject = False
                        if hasattr(widget, 'interactive'):
                            if widget.interactive or widget.invisibleObject:
                                foundApossibleWidget = widget
                                success = True
                                invisibleObject = widget.invisibleObject

                        # Invisible pixel checking. For Pillow Images, check colors in the image itself 
                        if hasattr(widget, 'PILimage'):
                            try:
                                c,d,_,_ = self.canvas.widget.bbox(id)
                            except:
                                pass
                            else:
                                a = abs(  abs(c) - abs(x) )
                                b = abs(  abs(d) - abs(y) )
                                _,_,_,alpha = widget.PILimage.getpixel( (a,b) )
                                if alpha <= 40: 
                                    if not invisibleObject:
                                        foundApossibleWidget = None # Transparent pixel, so no widget found 
                                        success = True
                                else: 
                                    success = widget.transport

                    # Done with widget checking, was one found? 
                    if foundApossibleWidget != None: widgetFound = foundApossibleWidget

        # Special debugging for movement, shows the color and points being checked
        if self.special:
            outlineColor = self.getMapPathColor(colorOnPath)
            pointA = Circle(self.canvas, x_center, y_center, 2, fill="Lime", outline=outlineColor, width=1)
            self.specialList.append(pointA)
            self.canvas.update()
            
        # On no success, do not pass out the offsets used. No success can still return any widget found
        if not success and not widgetFound: x_movement,y_movement = 0,0
        return (success,widgetFound,x_movement,y_movement)
        #return objectHitStatus

    def moving(self, direction=None, standardCheck=True): 
        if direction == None: return False, None
        success,item = self.movingList([direction], standardCheck=standardCheck)
        return success, item
    
    def movingList(self, directionList, standardCheck=True, smoothMovement=False): 
        if directionList == None or len(directionList)==0: return False, None
        smoothing = smoothMovement and len(directionList) > 1

        # Check for a safe move
        success,item,x_movement,y_movement = self.checkSafeListMovement(directionList, standardCheck=standardCheck)

        # Regardless of a safe move, was different object hit (not the last one again)?
        if item != None: 
            itReallyDidHit = self.processHitObject(item, directionList[0])
            self.data.setLastTouch(item)
            if itReallyDidHit: 
                success = False # Regardless of its previous value, it is now assumed False

        # No movement but we could have hit something and not moved as it was right next to us
        if x_movement == 0 and y_movement == 0: return success, item 
        
        # Move will happen and has been checked as valid. 
        if success:

            # There must be a valid center object to move it
            if self.centerObject is None: return False, None # The centerObject has been removed, so no movement
            try:
                left,top,right,bottom = self.canvas.widget.coords(self.centerObject.id)
            except:
                return False, None # The centerObject has been removed but its id is still there, so no movement
            
            # Move may be OK, but keep track that you can't scroll the center object when near the edges of the map
            x_center = left + abs(left-right)/2
            y_center = top + abs(top-bottom)/2
            self.horizontalScrollAvailable = self.MaxScrollRight > x_center > self.MaxScrollLeft
            self.verticalScrollAvailable = self.MaxScrollTop < y_center < self.MaxScrollBottom

            # What to do on direction
            vertical, horizontal = False, False
            for direction in directionList:
                match direction:
                    case 'Up':
                        vertical = True
                    case 'Down':
                        vertical = True
                    case 'Left':
                        horizontal = True
                    case 'Right':
                        horizontal = True

            
            # Move the center object and taking in account scrolling
            if smoothing: # Try to smooth diagonal movement when scrolling
                self.canvas.root.update_idletasks()

            self.canvas.widget.move(self.centerObject.id, x_movement,y_movement)
            self.objectPosition = (self.objectPosition[0] + x_movement, self.objectPosition[1] + y_movement)
            if self.positioning is not None: self.positioning()

            # Scrolling
            if vertical:
                if self.scrollingAvailable and self.verticalScrollAvailable: 
                    y_movement = int(y_movement)
                    self.canvas.widget.yview_scroll(y_movement,'units')
                    self.y_adjustment += y_movement
            if horizontal:
                if self.scrollingAvailable and self.horizontalScrollAvailable: 
                    x_movement = int(x_movement)
                    self.canvas.widget.xview_scroll(x_movement,'units')
                    self.x_adjustment += x_movement
            if smoothing:
                self.canvas.update(MACOS_PAUSE)

            # Control of any remote or minimap (but they can't call themselves, 
            # the minimap can scroll without a center object)
            if self.remoteMap != None:     
                for direction in directionList:
                    if direction == 'Up':       
                        if bottom + self.visibleHeight/2 < self.MaxBottom:
                            self.remoteMap.moving('Up')

                    elif direction == 'Down':            
                        if top - self.visibleHeight/2 > self.MaxTop:
                            self.remoteMap.moving('Down')

                    elif direction == 'Left':            
                        if right + self.visibleWidth/2 < self.MaxRight:
                            self.remoteMap.moving('Left')

                    elif direction == 'Right':            
                        if left - self.visibleWidth/2 > self.MaxLeft:
                            self.remoteMap.moving('Right')
            
        return success, item

    def dragging(self, newLocation=None, standardCheck=True): # TODO: Original position needed somehow
        """Attempt to move to the new location provided as (x,y) tuple or interact with an 
        object at that location. Not called in loopForUI(self): as movement is direct to the location.
        Check that the new location is on a path (if a path is available) and process any hits
        on objects. If it is not on a path, then it will soon move back to
        the original position (and/or run a not-on-path function). However, also check if another object 
        has been hit. If it has and the objects interact (perhaps some 'target' resolution)
        then resolve the contact with functions from both objects. If there is no hit but the
        object is on the a path, it moves without interactions (and may have a function for this).
        Otherwise if the objects hit but do not interract either a miss function on the dragged 
        object is run or you just move back to the original position. 
        That could be the default miss function. Default not-on-path is return to the original position."""
        # NOTE: NewLocation is the absolute location on the canvas. Dragging is in ActionInterface.
        # NOTE: Must connect to a canvas where dragging is checked. Perhaps a dictionary is needed.
        if newLocation == None: return False, None

        # Replaces checkSafeMovement(newLocation, standardCheck=standardCheck)
        success,item,location = self.checkSafeDragging(newLocation, standardCheck=standardCheck)
        if item != None: 
            # Replaces self.processHitObject(item, location)
            itReallyDidHit = self.processDraggingHitObject(item, location)
            self.data.setLastTouch(item)
            if itReallyDidHit: 
                success = False # Regardless of its previous value, it is now assumed False
        if success:
            success = False
            canvas = self.canvas.widget        

            if self.shape is not None:
                try:
                    left,top,right,bottom = canvas.coords(self.shape.id)
                except:
                    return False, None # The object has been removed, so no movement
                
                goodMovement = False
                if goodMovement:
                    # Keep where you have moved
                    if self.positioning is not None: self.positioning()
                    success = True

            # Scrolling (the minimap can scroll without a center object)
            if False: #vertical:
                if self.scrollingAvailable and self.verticalScrollAvailable: 
                    y_movement = int(y_movement)
                    canvas.yview_scroll(y_movement,'units')
                    self.y_adjustment += y_movement
                    success = True
            if False: #horizontal:
                if self.scrollingAvailable and self.horizontalScrollAvailable: 
                    x_movement = int(x_movement)
                    canvas.xview_scroll(x_movement,'units')
                    self.x_adjustment += x_movement
                    success = True

            # Control of any remote or minimap (but they can't call themselves)
            # The compass doesn't move correctly when stored mouse moves are stored
            # while moving.
            if self.remoteMap != None:     
                self.remoteMap.jump(location)
        else:
            # Move back to the previous location
            pass

        return success, item

    def jump(self, x, y, objectToMove=None):
        """NOT WORKING Move an object to the given location"""
        canvas = self.canvas.widget
        goalCoordinates = (x,y)

    def flying(self):
        pass

    def setFlying(self,flyStatus):
        self.flyingAllowed = flyStatus

    def remoteJump(self, x, y):
        """Move the remote map to the same location as this map"""
        self.jump(x,y)

    def getDimensions(self):
        """Return the dimensions of the canvas"""
        a,b,c,d = map(lambda x: int(x), (self.MaxLeftEdge, self.MaxTopEdge, self.MaxRightEdge, self.MaxBottomEdge))
        return a,b,c,d

    def setCenterObjectToTop(self):
        canvas = self.canvas.widget
        ids = canvas.find_all()
        last = len(ids) - 1
        tag = self.centerObject.tag
        while ids[last] != self.centerObject.id:
            canvas.tag_raise(tag)
            ids = canvas.find_all()
           
    def setCenterObject(self, object, x=None, y=None, alreayPositioned=False):
        """Set the optional object to  the map coordinates, optional starting location.
        Record the object's width and height for movement calculations."""
        self.centerObject = object
        canvas = self.canvas.widget
        tag = "player"
        self.centerObject.tag = tag
        canvas.addtag_withtag(tag, object.id)
        self.objectPosition = self.middleTuple

        # Get the unplaced bbox and place it in the center (no scrolling info)
        if not alreayPositioned:
            bbox = canvas.bbox(self.centerObject.id)
            self.centerObjectWidthOffset = abs(bbox[0]-bbox[2])/2
            self.centerObjectHeightOffset = abs(bbox[1]-bbox[3])/2
            object.x = self.objectPosition[0] - self.centerObjectWidthOffset
            object.y = self.objectPosition[1] - self.centerObjectHeightOffset
            canvas.moveto(self.centerObject.id, object.x, object.y) # Moves it to the center of the screen
            object.p1 = Point(object.x-self.centerObjectWidthOffset,
                          object.y-self.centerObjectHeightOffset)
            object.p2 = Point(object.x+self.centerObjectWidthOffset,
                          object.y+self.centerObjectHeightOffset)

            # If a specific position is given automatically move there so scrolling is correct
            if (x != None and y != None):
                self.moveCenterObjectToPosition(x, y)

            # Draw and reset the edge boundaries for the center object to include object size
            self.centerObject.draw()
            self.MaxTopEdge += self.centerObjectHeightOffset
            self.MaxBottomEdge -= self.centerObjectHeightOffset
            self.MaxLeftEdge += self.centerObjectWidthOffset
            self.MaxRightEdge -= self.centerObjectWidthOffset

    def moveCenterObjectToPosition(self, x, y):
        if (x != None and y != None):
            moveX = x - int(self.scrollWidth/2 )
            moveY = y - int(self.scrollHeight/2  )
            try:
                bbox = self.canvas.widget.bbox(self.centerObject.id)
            except:
                pass # No movement possible
            else:
                timers = self.data.getResource("timers")
                mouseMoves = timers.determineMouseMoves((moveX,moveY), bbox)
                self.performAutomaticMovement(mouseMoves, showMovement=False)
                bbox = self.canvas.widget.bbox(self.centerObject.id)
                x1 = bbox[0] + (bbox[2]-bbox[0])//2
                y1 = bbox[1] + (bbox[3]-bbox[1])//2
                self.objectPosition = (x1,y1)
    
    def getObjectsInfoAt(self, x, y, ignoreObject=None):
        """Find the IDs and color of all objects at the given coordinates in reverse order.
        If an ignoreId is given, it is not included in the list."""
        objectList = []
        canvas = self.canvas.widget
        ids = canvas.find_overlapping(x, y, x, y)
        if ids and len(ids) > 1: # If only 1 it is the background so no checking needed
            # Get the id and color of the object in reverse order (highest first)
            count = -(len(ids)+1)
            for i in range(-1,count,-1): # Backwards to get top element first
                checkId = ids[i]
                if ignoreObject != None:
                    if checkId != ignoreObject.id:
                        objectList.append(checkId)
        return objectList

    # Called only by the centerObject when moving to a location without graphicsMove with the saved direction
    def performAutomaticMovement(self, moves, standardCheck=False, showMovement=False):
        UU = ord('U')
        DD = ord('D')
        LL = ord('L')
        RR = ord('R')
        while len(moves) > 0:
            diagonalMove = False
            direction = moves.pop(0)
            if direction == 0: break # Stop at the end of the list

            nextDirection = moves[0] if len(moves) > 0 else None
            if nextDirection is not None:
                if (direction == UU and nextDirection == LL) or (direction == LL and nextDirection == UU):
                    diagonalMove = True
                    self.movingList(['Up','Left'], standardCheck=standardCheck)
                    if len(moves) > 0: moves.pop(0) # Remove the next direction as it has been processed
                elif (direction == UU and nextDirection == RR) or (direction == RR and nextDirection == UU):
                    diagonalMove = True
                    self.movingList(['Up','Right'], standardCheck=standardCheck)
                    if len(moves) > 0: moves.pop(0) # Remove the next direction as it has been processed
                elif (direction == DD and nextDirection == LL) or (direction == LL and nextDirection == DD):
                    diagonalMove = True
                    self.movingList(['Down','Left'], standardCheck=standardCheck)
                    if len(moves) > 0: moves.pop(0) # Remove the next direction as it has been processed
                elif (direction == DD and nextDirection == RR) or (direction == RR and nextDirection == DD):
                    diagonalMove = True
                    self.movingList(['Down','Right'], standardCheck=standardCheck)
                    if len(moves) > 0: moves.pop(0) # Remove the next direction as it has been processed

            if not diagonalMove:
                if direction == UU: # Remote movement use a byte array for U, D, L, R
                    self.moving('Up', standardCheck=standardCheck)
                elif direction == DD:
                    self.moving('Down', standardCheck=standardCheck)
                elif direction == LL:
                    self.moving('Left', standardCheck=standardCheck)
                elif direction == RR:
                    self.moving('Right', standardCheck=standardCheck)
                if showMovement: 
                    self.canvas.update(MACOS_PAUSE)

    def getFourDimensions(self, arguments):
        "Extract coordinates from the arguments and return them as a tuple, often as (x,y,width,height)."
        newList = []
        length = len(arguments)
        for index in range(length):
            newList.append(arguments[index])
        resultTuple = tuple(newList)
        return resultTuple  
    
    def convertStandardToMapCoordinates(self, *args):
        """ Adjusts the (x,y) from standard (0,0) top left coordinates to the map coordinates"""
        pointUse = False
        if len(args) == 0: return []
        if len(args) == 1:
            if isinstance(args[0], Point):
                pointUse = True
                point = args[0]
                x = point.x
                y = point.y
            elif len(args[0]) == 2:
                x = args[0][0]
                y = args[0][1]
            else:
                return []     
        else:
            x = args[0]
            y = args[1]  
        adjusted_x = self.MaxLeft + x
        adjusted_y = self.MaxTop + y
        if pointUse:
            return Point(adjusted_x, adjusted_y)
        else:
            return (adjusted_x,adjusted_y)
         
    def convertMapCoordinatesToStandard(self, *args):
        """ Adjusts the (x,y) from map coordinates (-,-,++)to the standard top left coordinates(0,0)"""
        pointUse = False
        if len(args) == 0: return []
        if len(args) == 1:
            if isinstance(args[0], Point):
                pointUse = True
                point = args[0]
                x = point.x
                y = point.y
            elif len(args[0]) == 2:
                x = args[0][0]
                y = args[0][1]
            else:
                return []     
        else:
            x = args[0]
            y = args[1]  
        adjusted_x = x - self.MaxLeft
        adjusted_y = y - self.MaxTop
        if pointUse:
            return Point(adjusted_x, adjusted_y)
        else:
            return (adjusted_x,adjusted_y)

    def undrawMap(self):
        for button in ["<Button-1>","<KeyPress>","<KeyRelease>"]:
            try:
                self.canvas.widget.unbind(button)
            except:
                pass
        try:
            self.canvas.widget.destroy()
            if self.remoteMap != None: 
                self.remoteMap.undrawMap()
        except:
            pass
        
    def loadScrollInformation(scrollInfo):
        pass

class MapScrollInformation():
    def __init__(self, map):
        self.mapName = map.mapImageName
        
class MapClass(BasicMapClass):
    """ A class to create a map with scrolling and object movement.  If no scrolling provide it is a plain canvas.
    Below are the available options for the dictionary defining canvas characteristics.
    For a standard map, make a byte array to hold basic color information from the path file.
    Use this to check for safe movement.
    0 = black which is out of bounds
    1 = red
    2 = green
    3 = yellow
    4 = blue
    5 = cyan
    6 = magenta
    7 = white which is the normmal path
    """
    def __init__(self, topCanvas, **dictionary):
        super().__init__(topCanvas, **dictionary)
        self.data = dictionary.get('data', None) # Data object to record history
        self.singleSafeColor = MAP_WHITE # Default color for safe movement
        self.safeColors = dictionary.get("safeColors", []) # Other safe colors for movement
        self.mapPathName = dictionary.get('mapPath', None) # Path map for the main map
        self.pathPixels = None # Overwritted with byte contents of the path file.  Determines safe paths.  8 Colors used.
        self.safeMovementCheck = False
        if self.mapPathName != None:
            try:
                if self.mapPathName is not None:
                    self.pathPixels = self.loadPathMapBytearray(self.mapPathName, self.scrollHeight, self.scrollWidth)
                    if len(self.pathPixels) > 0:
                        self.safeMovementCheck = True
                    else:
                        pilImage = self.loadMapPathImage(self.mapPathName)
                        if pilImage is not None:
                            self.pathPixels = self.makePathByterrayFromImage( topCanvas, pilImage, self.scrollHeight, self.scrollWidth,)
                            self.safeMovementCheck = (len(self.pathPixels) > 0)
                        if self.safeMovementCheck:
                            self.savePathMapBytearray(self.mapPathName, self.pathPixels, self.scrollHeight, self.scrollWidth)
            except:
                self.pathPixels = []

    def adjustForPixelArray(self, x, y):
        """Adjust the (x,y) coordinates for the pixel array"""
        adjusted_x = int(x + self.imageUpper_x)
        adjusted_y = int(y + self.imageUpper_y)
        return (adjusted_x, adjusted_y)
    
    def showPathOnMap(self, canvas, coord=None):
        self.placeMapInImage(canvas, self.pathImage, self.pathPixels, self.mapPathName, self.mapImageName, coord=coord)

    def restartMap():
        pass

    def addSafeColor(self, color):
        if color not in self.safeColors:
            self.safeColors.append(color)
    def removeSafeColor(self, color):
        found = False
        for i in range(len(self.safeColors)):
            if self.safeColors[i] == color:
                del self.safeColors[i]
                found = True
                break
        return found
    
    def makePathByterrayFromImage( self, canvas, PILpathImage, height, width ):
        pathWidth,pathHeight = PILpathImage.size
        if width != pathWidth or height != pathHeight:
            BasicMapClass.logError(f"Path image size of {height}x{width} must be the same size as the map image of {pathWidth}x{pathHeight}")
            pathPixels = []

        # get the color for each pixel in the image
        else:
            pathPixels = bytearray(width * height)
            data = PILpathImage.getdata()
            increment = height*width
            progressBar = ProgressBar( canvas, text="Building map's path", increment=increment )
            
            for count,item in enumerate(data):
                progressBar.step()
                r = 1 if item[0] > 200 else 0
                g = 2 if item[1] > 200 else 0
                b = 4 if item[2] > 200 else 0
                number = r + g + b
                pathPixels[count] = number
                
            progressBar.close()
        return pathPixels 

    def loadPathMapBytearray(self, fileName, requiredHeight, requiredWidth):
        playersMapPixels = []
        mapByteName = fileName + ".mapdata"
        if os.path.exists(mapByteName):
            try:
                # Open the map file and read the pixel data
                with open(mapByteName, "rb") as f:
                    size = requiredHeight * requiredWidth
                    playersMapPixels = bytearray(size)
                    playersMapPixels = f.read(size)  # Read the pixel data
            except Exception as e:
                playersMapPixels = []
                BasicMapClass.logError(f"Error loading map bytearray from {mapByteName}: {e}")
        else:
            BasicMapClass.logError(f"Error no bytearray name provided.")
        return playersMapPixels
        
    def savePathMapBytearray(self, fileName, byteData, width, height):
        if len(fileName) == 0 or len(byteData) == 0:
            BasicMapClass.logError("No file name or byte data provided for saving the map path bytearray.")
        elif width <= 0 or height <= 0:
            BasicMapClass.logError("Invalid width or height for saving the map path bytearray.")
        else:
            if fileName.endswith(".mapdata"):
                mapByteName = fileName
            else:
                mapByteName = fileName + ".mapdata"
            try:
                # Open the map file and read the pixel data
                size = width * height
                with open(mapByteName, "wb") as f:
                    #f.write(pack('ii', width, height))  # Write width and height
                    f.write(byteData[:size])  # Ensure we only write the expected number of bytes
            except Exception as e:
                BasicMapClass.logError(f"Could not save the map path byte data {mapByteName}: {e}")

    def loadMapPathImage(self, mapPath):
        """Load the map image from a file and return it."""
        if mapPath is None: return None
        if os.path.exists(mapPath):
            try:
                mapImage = PILImage.open(mapPath)
            except Exception as e:
                mapImage = None
                BasicMapClass.logError(f"Error loading map image {mapPath}: {e}")
        return mapImage

    def placeMapInImage(self, canvas, pathImage, pathPixels, mapPathName, mapImageName, coord=None):

            # pilPathImage = PILImage.open(mapPathName)
            # r,g,b = pilPathImage.split()
            # mask_r = r.point(lambda i: i > 0 and 255)
            # mask_g = g.point(lambda i: i > 0 and 255)
            # mask_b = b.point(lambda i: i > 0 and 255)

            # mapImage = PILImage.open(mapImageName)
            # source = mapImage.split()
            # source[0].paste(r, None, mask_r)
            # source[1].paste(g, None, mask_g)
            # source[2].paste(b, None, mask_b)
            # newImage = PILImage.merge(mapImage.mode, source)
            # pathImage = ImageTk.PhotoImage(newImage)

            pathWidth = pathImage.width()
            pathHeight = pathImage.height()
            
            progressBar = ProgressBar( canvas, text="Placing path into map", increment=pathWidth, coord=coord )
            maximum = len(pathPixels)
            for x in range(pathWidth):
                progressBar.step()
                for y in range(pathHeight):
                    lookingAt = x + y * pathWidth
                    if lookingAt >= maximum:
                        colorInPath = 0 # No path
                    else:
                        colorInPath = pathPixels[lookingAt]

                    match colorInPath:
                        case 0: # Black, no path
                            pass #self.pathImage.put("#000000", (x,y))
                        case 1: # Red
                            pathImage.put("#ff0000", (x,y))
                        case 2: # Green
                            pathImage.put("#00ff00", (x,y))
                        case 3: # Yellow
                            pathImage.put("#ffff00", (x,y))
                        case 4: # Blue
                            pathImage.put("#0000ff", (x,y))
                        case 5: # Cyan
                            pathImage.put("#00ffff", (x,y))
                        case 6: # Magenta
                            pathImage.put("#ff00ff", (x,y))
                        case 7: # White
                            pathImage.put("#ffffff", (x,y)) 
                        case _:
                            pass

            progressBar.close()

class MiniMapClass(BasicMapClass):
    def __init__(self, mainMap, **kwargs):
        self.canvas = mainMap.canvas.parent
        dictionary = dict(**kwargs)
        super().__init__(self.canvas, mouseOnly=None, **dictionary)

        self.mainMap = mainMap
        mainMap.remoteMap = self
        self.safeMovementCheck = False

        self.scrollHeight = self.visibleHeight # height and width are provided in a mini-map
        self.scrollWidth = self.visibleWidth
        self.scrollingAvailable = False
        
        # Insure the estmated dimensions are non-zero so no Divide by zero
        height = mainMap.height if mainMap.height > 0 else 1.0
        width =  mainMap.width if mainMap.width > 0 else 1.0
        self.widthRatio = self.visibleWidth/width
        self.heightRatio = self.visibleHeight/height  
        
        # Movement is a fraction of the normal movement, also, the minimap rectangle does not
        # move out of the map as the player moves to an edge. Therfore we need our own
        # movement increment and keep track of the virtual and actual x,y position.
        self.scrollIncrement = 0.001 + float(mainMap.scrollFractionalIncrement) * self.heightRatio

        # If no map provide, make a miniture of the main map
        pixelOffset = 2 # magic number
        if self.mapImageName is None:
            ratio = int(height/self.visibleHeight)
            self.image = mainMap.image.subsample(ratio, ratio)
        else: # Map provided
            self.image = tk.PhotoImage(file=self.mapImageName)
        self.mapImage = Image(self.canvas, pixelOffset+self.visibleWidth/2, pixelOffset+self.visibleHeight/2, image=self.image, state='normal')
        self.visibleHeight = self.image.height()
        self.visibleWidth = self.image.width()

        ## Estimate the visible square size
        self.squareSize = float(mainMap.MaxBottom / mainMap.height) * self.visibleHeight / 1.4142135     
        self.halfSize = self.squareSize/2
        
        # Calculate the upper left point of the rectangle using the player's center & correct ratio on the minimap
        x,y = self.mainMap.centerObject.objectPosition
        extimated_x = x * self.widthRatio - self.halfSize
        estimated_y = y * self.heightRatio - self.halfSize
        
        # Adjust the rectangle so it does not leave the visible map when you get near an edge
        if estimated_y + self.squareSize > self.visibleHeight:
            estimated_y = self.visibleHeight - self.squareSize
        elif estimated_y < 0:
            estimated_y = 0
            
        if extimated_x + self.squareSize > self.visibleWidth:
            extimated_x = self.visibleWidth - self.squareSize
        elif extimated_x  < 0:
            extimated_x = 0
        
        x1 = int( extimated_x)
        x2 = int(extimated_x + self.squareSize)
        y1 = int( estimated_y)
        y2 = int(estimated_y + self.squareSize)
        self.virtual_x = x1 + self.halfSize
        self.virtual_y = y1 + self.halfSize
        
        square = Rectangle(self.canvas, x1, y1, x2, y2, outline="Red", fill=None)
        self.setCenterObject( square, alreayPositioned=True)
        mainMap.canvas.update()

    def compressMapWithObjects(self, mainMapInput, mimiMapOutput):       
        '''Compress the main map with objects to a mini-map'''
        offset = int(mimiMapOutput.width/2)
        mainMapWidth = mainMapInput.scrollWidth
        mainMapHeight = mainMapInput.scrollHeight
        x_count = int(mainMapWidth/mimiMapOutput.width)
        y_count = int(mainMapHeight/mimiMapOutput.height)

        colorCollection = []
        centerObject = None if mainMapInput.centerObject == None else mainMapInput.centerObject
        for y in range(mimiMapOutput.height):
            for x in range(mimiMapOutput.width):
                for x1 in range(x*x_count, (x+1)*x_count):
                    for y1 in range(y*y_count, (y+1)*y_count):
                        color = mainMapInput.getWidgetPixelColor(x1, y1, ignoreObject=centerObject)
                        if color != None: colorCollection.append(color)
                color = self.canvas.colors.Blend(*colorCollection)
                colorCollection.clear()
                if color == None: continue
                mimiMapOutput.mapImage.setPixel(x+offset, y+offset, color)
            pass
            print(f"Loop y={y}")
        pass

    # def handle_minimap_complete(self, result):
    #     self.canvas.update()
       
    def checkSafeListMovement(self, directionList, standardCheck=True):
        """Check if the object can move in multiple chosen directions"""
        success = False
        widgetFound = None
        self.movement = self.scrollIncrement
        x_movement, y_movement = 0,0
        noMovementTuple = (success, widgetFound, y_movement, x_movement)

        # Required elements
        if directionList is None or len(directionList) == 0: return noMovementTuple
        if self.canvas.movementHalted: return noMovementTuple 
        if self.centerObject is None: return noMovementTuple 

        # Get the bounding box for the center object, if any
        try:
            x1, y1, x2, y2 = self.canvas.widget.bbox(self.centerObject.id)
        except:
            return noMovementTuple
        
        # Get the new position(s) for the movement into x and/or y directions
        up,down,left,right   = False,False,False,False # Certain combos are ignored, example not both up and down key presses
        success = True
        for eachDirection in directionList:
            match eachDirection:
                case 'Up':
                    up = True
                    y_movement -= self.movement
                case 'Down':
                    down = True
                    y_movement += self.movement
                case 'Left':
                    left = True
                    x_movement -= self.movement
                case 'Right':    
                    right = True
                    x_movement += self.movement

        # Track the virtual movement
        self.virtual_x += x_movement 
        self.virtual_y += y_movement
        
        # Keep movement in bounds on the map
        left_limit   = self.virtual_x - self.halfSize
        top_limit    = self.virtual_y - self.halfSize 
        right_limit  = self.virtual_x + self.halfSize
        bottom_limit = self.virtual_y + self.halfSize  
        if left:
            if left_limit   < 0: success = False
        elif up:
            if top_limit    < 0: success = False
        elif right:
            if right_limit  > self.width : success = False
        elif down:
            if bottom_limit > self.height: success = False

        return (success,widgetFound,x_movement,y_movement)


    def moving(self, direction=None, standardCheck=True): 
        if direction == None: return False, None
        success,item = self.movingList([direction], standardCheck=standardCheck)
        return success, item
    
    def movingList(self, directionList, standardCheck=True): 
        if directionList == None or len(directionList)==0: return False, None
        
        # Check for a safe move
        success,item,x_movement,y_movement = self.checkSafeListMovement(directionList, standardCheck=standardCheck)

        # No movement but we could have hit something and not moved as it was right next to us
        if x_movement == 0 and y_movement == 0: return success, item 
        
        # Move will happen and has been checked as valid. 
        if success:

            # There must be a valid center object to move it
            if self.centerObject is None: return False, None # The centerObject has been removed, so no movement
            try:
                left,top,right,bottom = self.canvas.widget.coords(self.centerObject.id)
            except:
                return False, None # The centerObject has been removed but its id is still there, so no movement
            
            # Move may be OK, but keep track that you can't scroll the center object when near the edges of the map
            x_center = left + abs(left-right)/2
            y_center = top + abs(top-bottom)/2
            self.horizontalScrollAvailable = self.MaxScrollRight > x_center > self.MaxScrollLeft
            self.verticalScrollAvailable = self.MaxScrollTop < y_center < self.MaxScrollBottom

            # Move the center object and include scrolling
            self.canvas.widget.move(self.centerObject.id, x_movement,y_movement)
            self.objectPosition = (self.objectPosition[0] + x_movement, self.objectPosition[1] + y_movement)
            if self.positioning is not None: self.positioning()

        return success, item

class MiniCompassClass():
    """A mini compass for the map.  Replaces a miniMap.  It is a small rectangle with a red line in the middle pointing to the location to travel to.
    """
    def __init__(self, mainMap, **kwargs):
        self.mainMapParent = mainMap.canvas.parent
        self.mainMap = mainMap
        self.data = mainMap.data
        mainMap.remoteMap = self
        self.tags = kwargs.pop('tag', "miniCompass")
        self.dictionary = dict(**kwargs)
        
        self.visibleWidth = self.dictionary.get('width', 50) # Width of visible part of canvas
        self.visibleHeight = self.dictionary.get('height', 50) # Height of visible part of canvas
        self.background = self.dictionary.get('background', None) # Background color of canvas
        self.compassColor = self.mainMap.canvas.colors.ComplementColor(self.background, "Black")
        self.x = self.dictionary.get('x', None) # Initial and absolute positioning in a larger canvas
        self.y = self.dictionary.get('y', None) 
        self.target = self.dictionary.get('target', None) # Target object to point to
        self.player = self.dictionary.get('player', None) # Player object to point to
        self.a = 0
        self.b = 0

        # Configure the rectangle of the entire area
        self.MaxTop = 0
        self.MaxBottom =  self.visibleHeight
        self.MaxLeft =  0 
        self.MaxRight =  self.visibleHeight
        self.lastAngle = -90.0
        
        self.automaticQueueing = False
        self.automaticDelayHappened = False

        # Construct the parent canvas and the map
        canvasDictionary = dict(x=self.x, y=self.y, width=self.visibleWidth, height=self.visibleHeight, background=self.background)
        self.canvas = Canvas(self.mainMapParent, **canvasDictionary)
        self.canvas.bindingAllowed = False 

        # segments is a list of ((start_x, start_y), (end_x, end_y)) for each compass line
        width = self.visibleWidth
        height = self.visibleHeight
        segmentLength = int(min(self.visibleWidth,self.visibleHeight)/10)
        segmentGap = int(segmentLength/2)

        cx, cy = width / 2, height / 2
        radius = min(width, height) / 2
        segments = []
        for i in range(12):  # 12 segments, every 30 degrees
            angle_rad = math.radians(i * 30)
            start_x = cx + (radius - segmentLength - segmentGap) * math.cos(angle_rad)
            start_y = cy + (radius - segmentLength - segmentGap) * math.sin(angle_rad)
            end_x = cx + (radius - segmentGap) * math.cos(angle_rad)
            end_y = cy + (radius - segmentGap) * math.sin(angle_rad)
            segments.append(((start_x, start_y), (end_x, end_y)))

        # Draw any map design
        for line in segments:
            start, end = line
            Line( self.canvas, start[0], start[1], end[0], end[1], fill='Black', width=2)

        ## Draw the center arrow on the map (draw around the center)
        center_x = width / 2
        polygon = [center_x, segmentGap, 
                   center_x - segmentGap, height - segmentGap,
                   center_x, height - 5*segmentGap,
                   center_x + segmentGap, height - segmentGap]
        self.arrow = Polygon(self.canvas, polygon, outline="", fill="Red")
        
        # Coordinate initial arrow pointing
        if self.player is not None and self.target is not None:
            self.initialMoving() # Insure the correct moving is called

    def setPlayer(self, player):
        self.player = player
        if self.target is not None:
            self.moving()

    def setTarget(self, target):
        self.target = target
        if self.player is not None:
            self.moving()

    # This overrides the standard map moving
    def moving(self, *args):
        if self.target is not None and self.player is not None:
            targetLocation = self.target.getCenter()
            playerLocation = self.player.getCenter()
            dx = targetLocation.x - playerLocation.x
            dy = targetLocation.y - playerLocation.y
            angleInRadians = math.atan2(dy, dx)
            rotationInDegrees = math.degrees(angleInRadians)  
            rotation = rotationInDegrees - self.lastAngle
            self.arrow.rotate(rotation)  
            self.lastAngle = rotationInDegrees

    def initialMoving(self):
        self.moving()
        self.canvas.update()

    def undraw(self):
        self.canvas.undraw()

class MinimapCompressor():
    def __init__(self, mainmap):
        self.mainmap = mainmap
        self.sourceQueue = queue.Queue() # Main map to be compresssed
        self.destinationQueue = queue.Queue() # Mini-map destination
        self.compression_thread = threading.Thread(target=self._compression_worker, daemon=True)
        self.compression_thread.start()

    def _compression_worker(self):
        """Worker thread that handles image compression"""
        while True:
            #try:
                # Get image data from queue
                source_image_data = self.sourceQueue.get()
                if source_image_data is None:  # Poison pill to stop the thread
                    break

                # Loop through all points in the image data to compress with object graphics
                destination_image_data = self.destinationQueue.get()
                self.compressMapWithObjects(self.mainmap, self.mainmap.remoteMap)
       
                self.mainmap.canvas.widget.event_generate("<<minimapComplete>>", when="tail", data=destination_image_data)

                # # Convert bytes to PIL Image & Compress the image
                # image = Image.open(io.BytesIO(image_data))
                # output = io.BytesIO()
                # image.save(output, format='PNG', optimize=True, quality=85)
                # compressed_data = output.getvalue()
                
            # except Exception as e:
            #     print(f"Error in compression worker: {e}")
            #     self.result_queue.put(None)
            # finally:
            #    self.sourceQueue.task_done()
            #    self.destinationQueue.task_done()

    def stop(self):
        """Stop the compression thread"""
        self.sourceQueue.put(None)
        self.compression_thread.join() 
 
    def compressMapWithObjects(self, mainMap, mimiMap):       
        '''Compress the main map with objects to a mini-map'''
        if mainMap == None or mimiMap == None: return
        
        if mimiMap.width == 0: mimiMap.width = 1
        if mimiMap.height == 0: mimiMap.height = 1
        offset = int(mimiMap.width/2)
        mainMapWidth = mainMap.scrollWidth
        mainMapHeight = mainMap.scrollHeight
        x_count = int(mainMapWidth/mimiMap.width)
        y_count = int(mainMapHeight/mimiMap.height)

        colorCollection = []
        centerObject = None if mainMap.centerObject == None else mainMap.centerObject
        for y in range(mimiMap.height):
            for x in range(mimiMap.width):
                for x1 in range(x*x_count, (x+1)*x_count):
                    for y1 in range(y*y_count, (y+1)*y_count):
                        color = mainMap.getWidgetPixelColor(x1, y1, ignoreObject=centerObject)
                        if color != None: colorCollection.append(color)
                color = self.canvas.colors.Blend(*colorCollection)
                colorCollection.clear()
                if color == None: continue
                mimiMap.mapImage.setPixel(x+offset, y+offset, color)
            pass
        pass