__version__ = '8.0'
class ScenarioClass():
    """ Stores a GUI scene to display, and upon its completion, runs the next scenario or exits.
    The scene class remains uninstantiated until scenario is called, the .nextFunction() is the internal
    .scenarioSegue() function called next. This class depends upon a common canvas, size, and data class.
    Only the first scenario called needs the parameters canvas, data, size as they are saved & passed on.
    """
    def __init__(self, sceneClass, nextScenario=None):
        self.currentScene = sceneClass
        self.nextScenario = nextScenario
        self.canvas = None
        self.data = None

    def scenarioSegue(self):
        if self.nextScenario == None:
            self.canvas.root.quit()
        else:
           self.nextScenario.startScene(self.canvas, self.data)

    def startScene(self, canvas, data):
        self.canvas = canvas
        self.data = data
        self.currentScene(canvas, data, returnFunction=self.scenarioSegue)


# class SceneClass():
#     """ This is an inherited class and not instantiated by itself.
#     The child class holds all code needed to run a 'scene'. This is an independent
#     GUI using a data and canvas class.  When the scene is ready
#     to exit, it removes its GUI and then runs the stored .nextFunction(). 
#     While .nextFunction is initialized as a default return here, it is set by parameter. 
#     SceneClass as an uninstantiated class is stored in a ScenarioClass object. 
#     The .nextFunction() will be an internal ScenarioClass function which  
#     calls the next senario. SceneClass is instantiated within the SenarioClass 
#     when it is called called and not before. It must run its own initializing & exiting code."""
       
#     def defaultReturn(self, *args):
#         return
    
#     def __init__(self, canvas, data, nextFunction=None):
#         self.canvas = canvas
#         self.data = data
#         self.nextFunction = self.defaultReturn
#         if nextFunction != None:
#             self.nextFunction = nextFunction