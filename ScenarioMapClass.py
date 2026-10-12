__version__ = "11.0"
from CoffeeCanvas import *
from CoffeeColors import *
from MapClass import *
from InstructionClass import *
import socket
# Used for email
# from asyncio import start_server
# from gettext import find
# from tarfile import LENGTH_LINK
# from telnetlib import NOP
# from datetime import datetime
# import win32com.client # may need: pip install pywin32  (may need to update pip)

class ScenarioMapClass():
    """ Bring in the Senario/CCU map for the student to move to its location and add a circle over the target. Once the circle is reached, the map
    will remove this map and set up the game.
    
    Holds all code needed to initialize, run, and close out the scenario scene.
    PARAMETERS:
         canvas:     where to draw graphics
         data:       all game data
         arguments:  x,y, width, height of the class on the canvas
         dictionary: Any needed kwargs
         
    Step 1: Place everything needed into this class
    Step 2: Place the retrieval of sizes and instantiation of this class into its own scene class. EX:
        class sceneFour():
           def __init__(self, canvas, data, returnFunction):
               size = data.getResource("size")
               scene = EndingSceneClass(canvas, data, *size("scenarioMap"), 
                       finalMessage=size["enterStudent"],
                       senarioInstructions=size("scenarioInstructions"), 
                       returnFunction=returnFunction, showPath=gameSetup.showPath )
    Step 3: Instantiate a scenario class with the scene and the scene to call next. Ex:
        senarioOne = ScenarioClass(sceneOne, nextScenario=senarioTwo)
    Step 4: You may need to do this in reverse order to previous scenes are created before access
    Step 5: Call the first scenario, which then instantiates and runs the scene. Ex:
        senarioOne.startScene(canvas, data)
        canvas.mainloop() 
    """
    
    def __init__(self, canvas, data, x, y, width, height, **kwargs):
        self.canvas = canvas
        self.data = data.setResource('scenarioMap', self)
        quiz = self.data.getResource('quiz')
        self.dictionary = dict( **kwargs)
        self.nextFunction = kwargs.get("returnFunction", self.defaultReturn) 
        
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
        # Place student query objects and setup to input user response
        coinGoal = quiz.get("Coin Goal", 10)
        instructions = quiz["Quest"]
        instructionText = instructions.format(coinGoal)
        questText = instructionText + " " + quiz["CCU Quest"]
        self.circleSize = 20
        self.questPlacement = self.dictionary.get("senarioInstructions", [0,0,0,0])
        self.questInstructions = InstructionClass( canvas, data, *self.questPlacement, text=questText, label="Quest Instructions")
        self.data.setResource('questInstructions', self.questInstructions)
        self.setupBigMap()

    def setupBigMap(self):
        quiz = self.data.getResource('quiz')
        self.senarioMapDictionary = {'x':self.x, 'y':self.y, 'width': self.width, 'height': self.height, 
                         'mapImage':quiz["SenarioMap"], 'mapPath':quiz["SenarioMap Path"] }
        tags = self.dictionary.get('tags', "scenario")
        self.senarioMapDictionary['tags'] = tags

        self.map = MapClass(self.canvas, data=self.data, **self.senarioMapDictionary)
        self.argumentDictionary={"data":self.data, "map":self.map, "scenario":self}
        targetCircleLocation = quiz.get("Target Location", (0,0))
        playerDotLocation = quiz.get("Splash Location", "Center" )
        
        self.setupMap( targetCircleLocation=targetCircleLocation, playerDotLocation=playerDotLocation)

        self.miniCompass = None
        coords = self.dictionary.get('miniCompassCoordinates',None)
        if coords is not None:
            miniCompassDictionary = {'x':self.x+coords[0], 'y':self.y+coords[1], 'height': coords[2],'width': coords[3], 'background':"Cyan" }
            self.miniCompass = MiniCompassClass(self.map, **miniCompassDictionary)
            self.miniCompass.setTarget(self.targetObject)
            self.miniCompass.setPlayer(self.map.centerObject)
        timers = self.data.getResource("timers")
        timers.registerMap( self.map )

    # Set up any initial major map and the player dot or the map at the end with the player home
    def setupMap(self, targetCircleLocation=None, playerDotLocation='Center', alternativeDotStart=None):

        # This is the player's dot
        spotSizeRadius = 6
        senarioMapPlayer = Circle(self.map.canvas, -spotSizeRadius, -spotSizeRadius, spotSizeRadius, spotSizeRadius, fill="Lime")
        if targetCircleLocation is not None:
            circleLocation = self.map.convertStandardToMapCoordinates(targetCircleLocation[0], targetCircleLocation[1] )
            self.targetObject = MapCircle(self.map, circleLocation, self.circleSize, fill=None, outline="Red", width=3, action=self.processClosing,
                                argumentDictionary=self.argumentDictionary )

        if type(playerDotLocation) == str: # Right now "Center" is the only selection
            coord = self.map.getCurrentCenterLocation()
        else:
            coord = playerDotLocation
        self.map.setCenterObject( senarioMapPlayer, coord[0], coord[1])
        showPath = self.dictionary.get('showPath', False)

        # For debugging, show where player can travel on the map (takes several minuites)
        if showPath: 
            self.map.showPathOnMap(self.canvas, coord=coord)

        # Display any NPC on the map
        quiz = self.data.getResource('quiz')
        localNPCs = quiz.get("NPCs",[])
        for npc in localNPCs:
            npcLocation = self.map.convertStandardToMapCoordinates(npc[1], npc[2])
            action = self.data.translateAction(npc[3])
            npcImage = MapImage(self.map.canvas, npcLocation[0], npcLocation[1], path=self.quiz["Objects Path"], image=npc[2], action=action)

        # Put the player on top
        self.map.setCenterObjectToTop()
        self.canvas.update()
        
        # Mac OS is slow with tkinter so player moves farther
        self.map.os_x_adjustment, self.map.os_y_adjustment = self.canvas.window.returnMacOSAdjustment()
                           
    def processClosing(self, *args):
        if ( debugging:= self.data.getResource('debugging')): debugging.stop()
        
        # Prevent stored movements from try to move on a removed map,
        # remove the centerObject so it doesn't try to move, remove the map, and any
        # access to the remote map.
        if self.miniCompass is not None:
            self.map.remoteMap = None
            self.miniCompass.undraw()
            self.miniCompass = None
            
        if map is not None:
            timers = self.data.getResource("timers")
            timers.clearAutomaticMouseMovements()
            self.questInstructions.undraw()
            self.map.undrawMap()
            self.map = None
            
        self.canvas.update()
        self.data.removeResource("scenarioMap")
        self.nextFunction()

    def defaultReturn(self, *args):
        return
    
