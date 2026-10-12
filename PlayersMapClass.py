__version__ = "8.0"
from MapClass import *
from PlayerClass import *

class PlayersMapClass():
    def __init__(self, canvas, data, x, y, width, height, **kwargs):
        """ Bring in the dungeon map, question area, player, and mini-map after any beginning scene.
        This is the map the player plays on.
        PARAMETERS:
         canvas:     where to draw graphics
         data:       all game data
         arguments:  x,y, width, height of the class on the canvas
         dictionary: Any needed kwargs
                     'displayObjects'  Default is to display all objects. Used in debugging to see everything.
                     'displayDarkness' Default is to display any darkness. Used in debugging to see the map.
                     'mouseOnly'       Mouse only = None means no user input on the map. other specific values.
                     'returnFunction'  Function to call when done
                     'coverMap'        True/False on automatic black cover over map during its creation
         """
        self.canvas = canvas
        self.data = data.setResource('playersMap', self)
        self.dictionary = dict(**kwargs)
        self.displayObjects  = self.dictionary.get('displayObjects', True)
        self.displayDarkness = self.dictionary.get('displayDarkness', True)
        self.mouseOnly = self.dictionary.get('mouseOnly', False)
        self.returnFunction = self.dictionary.get("returnFunction", self.defaultReturn) 
        quiz = self.data.getResource('quiz')
        self.safeColors = quiz.get("Safe Colors", []) # Other safe colors for movement

        # Create a simple canvas to hold the map (possibly provide a black cover to hide map being constructed)
        self.coverMap = self.dictionary.get('coverMap', False)
        self.tags = self.dictionary.pop('tags', "playersMap")
        self.mapDictionary = {'x':x, 'y':y, 'width': width, 'height': height, 'coverMap':self.coverMap,
                         'mapImage':quiz["Map"], 'mapPath':quiz["Map Path"], 'safeColors':self.safeColors}
        self.map = MapClass(self.canvas, data=self.data, **self.mapDictionary)
        data.setResource('map', self.map)

        showPath = self.dictionary.get('showPath', False)
        if showPath: 
            self.map.showPathOnMap(self.canvas) # Used by debugging to show the path on the map, takes time to create

    def setupMap(self, *args,):
        """Set up the map in the dungeon"""
        player = self.data.getResource('player')
        badges = self.data.getResource('badges')
        data = self.data.getResource('data')

        # Display objects before and after the player object is positioned. Non-display is used in debugging.
        if self.displayObjects: 
            data.displayPreplayerObjects(self.map, displayDarkness=self.displayDarkness)    
        player.positionPlayerOnTheMap() # Set the player to the correct position on the map and make it the top item
        badges.updatePositioning()
        self.map.setCenterObjectToTop()
        self.map.recenterCoverMap()
        if self.displayObjects: 
            data.displayPostplayerObjects(self.map)  
                
        # Once everything is positioned, make the mini-map.
        coords = self.dictionary['miniMapCoordinates']
        minimapDictionary = {'x':coords[0], 'y':coords[1], 'height': coords[2],'width': coords[3]  } 
        self.miniMap = MiniMapClass(self.map, **minimapDictionary)
        self.map.removeCoverMap()
        timers = self.data.getResource("timers")
        timers.registerMap( self.map )
         
    def undraw(self):
        """ Remove all the graphics"""
        if self.miniMap is not None:
            self.miniMap.undrawMap()
            self.miniMap = None
        if self.map is not None:
            self.map.undrawMap()
            self.map = None
            
    def defaultReturn(self, *args):
        return
    