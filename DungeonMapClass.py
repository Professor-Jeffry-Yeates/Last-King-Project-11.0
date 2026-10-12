__version__ = '8.0'
from CoffeeCanvas  import *
from CoffeeColors import *
from MapClass import *
from InstructionClass import *
from PlayersMapClass import PlayersMapClass
from InstructionClass import *
from QuestionAreaClass import *
from BadgesClass import *
from GameTimerClass import *
from StatusClass import StatusClass
from RewardClass import RewardClass

class DungeonMapClass():
    """ 
    Holds all code needed to initialize, run, and close out the dungeon scene.
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
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.dictionary = dict( **kwargs)
        self.nextFunction = self.dictionary.get("returnFunction", self.defaultReturn) 
        quiz = data.getResource('quiz')
        size = data.getResource("size")

        # Create GUI
        self.instructions = InstructionClass( canvas, data, *size("instructions"), 
                        label=quiz["Frame Label"], text=quiz["Entry"]) 
        beginningCopyright = 'Copyright all code and graphics to Jeff Yeates 2025. Licensed music and sound effects from Digital Juice and the General 5000. Graphic elements from Incarnate.'
        self.statusBar = StatusClass( canvas, data, *size("statusBar"), text=beginningCopyright)        
        self.rewardBox = RewardClass(canvas,  data, *size("rewardBox"), wins=quiz["Coin Goal"]) 
        showPath = self.dictionary.get("showPath", False)
        self.playersMap = PlayersMapClass(canvas, data, *size("playersMap"), miniMapCoordinates=size("miniMap"), 
                        mouseOnly=None, showPath=False, coverMap=True, returnFunction=self.processClosing,
                        displayObjects=True, displayDarkness=True )
        self.badges = BadgesClass( canvas, data, *size("badges")) 
        self.player = PlayerClass(data, self.playersMap ) 
        self.questionArea = QuestionAreaClass( canvas, data, *size("questionArea"), 
                        additionalHeight=800, additionalWidth=1600, TryLater=True)
        
        # Connect data with the map contents and update the map with objects (including the minimap)
        data.connectMapAndObjects()
        data.setExitingFunction(self.processGameExit)
        
        # Mac OS is slow with tkinter so player moves farther
        self.playersMap.map.os_x_adjustment, self.playersMap.map.os_y_adjustment = self.canvas.window.returnMacOSAdjustment()
        self.playersMap.setupMap()
        
        # Start timing
        timers = self.data.getResource("timers")
        timers.loadTorches()
        
        if ( debugging := data.getResource('debugging')):
            debugging.setDebuggingGraphics(self.questionArea.canvas)
            
        # Darkness gets misplaced sometimes, so review all darkness and reposition where needed
        
        
    def processFinishGame(self, *args, **wargs):
        """Record the score as it is, then ask the last question."""
        rewardStatus = self.rewardBox.currentStatus()
        gold = rewardStatus["gold"]
        silver = rewardStatus["silver"]
        copper = rewardStatus["copper"]
        quiz = self.data.getResource('quiz')
        coinGoal = quiz["Coin Goal"]
        torchesLeft = self.player.getHistory('Torches_Left', 0)
        if coinGoal == 0: coinGoal = 1 # Protect from a div/0 error
        gameScorePercentage = (min(1.0,int(gold/coinGoal)) + min(1.0,int(silver/coinGoal)) + min(1.0,int(copper/coinGoal))+ 0.1)*33.4
        gameScore = int(gameScorePercentage)
        gameWon = True if rewardStatus["coinsCollected"] else (gameScore > 0)
        self.player.recordHistory(GameScore=gameScore, Percentage=gameScorePercentage, GameWon=gameWon) 

        # Determine which ending to do next
        if gameWon:
            self.gameWon()
        elif torchesLeft <= 0:
            self.gameForcedToEnd()
        else:
            self.gameLost(self) 
        self.canvas.update()

        # Setup the last question 
        lastQuestionObject = self.data.makeLastQuestion(returnFunction=self.processClosing)
        self.questionArea.implementQuestion(lastQuestionObject)

    def gameWon(self):
            self.instructions.newSection("\nYou have completed the game! Well done! You can continue playing but you should exit before all your torches run out (or you might never leave)!")
            self.statusBar.set("You have completed the game! Well done!")
            self.instructions.setBackground("LightGreen")
            self.statusBar.setBackground("LightGreen")
            self.canvas.update()
                        
    def gameLost(self):
            self.instructions.newSection("\nYou have run out of torches and the game is over! The darkenss decends like disease on the dying. However, the denziens of he dungeon had pity on you as you bumped into their stuff trying to exit, so they led you back to the entrance. You might be missing some coins now!")
            self.data.removeTreasure(Gold=randint(0,3), Silver=randint(0,2), Copper=randint(0,1))
            self.statusBar.set("You have finished the game! Better luck next time!")
            self.instructions.setBackground("LightRed")
            self.statusBar.setBackground("LightRed")
            self.canvas.update()
                        
    def gameForcedToEnd(self):
            self.instructions.newSection("\nYou have run out of torches and the game is over! The darkenss decends like disease on the dying. The denziens of the dungeon stole all your gold but they did lead you back to the entrance.")
            self.data.removeTreasure(Gold="All")
            self.statusBar.set("You have finished the game and won (if a bit poorer)!")
            self.instructions.setBackground("LightBlue")
            self.statusBar.setBackground("LightBlue")
            self.canvas.update()

    def setupForLastQuestion(self):
        # Stop everything which is not needed for this last moral question
        if (debugging:= self.data.getResource('debugging')): debugging.stop()
        self.canvas.root.unbind("<Escape>")
        self.playersMap.map.canvas.root.unbind("<Escape>")
        self.data.stopMoving()
        timers = self.data.getResource("timers")
        timers.timerCentral.stop()
        self.badges.stop()
        self.questionArea.stop()

        # Bring some of the darkness back (some lose their darkness??) with no actions
        for name in ["D47","D46","D45","D44","D38","D39","D6","D7","D8","D55","D56","D57"]:
            # Place the objects back into the map
            objectDictionary = self.data.findMapObject(name=name)
            if objectDictionary is not None:
                mapObject = objectDictionary["MapObject"]
                mapObject.drawn = False
                mapObject.draw()
                mapObject.clearActions()
                self.data.fillInWithDarkenss(mapObject) # D46 lost its color
        self.canvas.update()

        # Move the player to the final location
        coord = self.data.quiz.get("Final Location", "Target Location" )
        self.playersMap.map.moveCenterObjectToPosition(coord[0], coord[1])
        self.canvas.update()

    def processGameExit(self, *args, **wargs):
        # To get here the game is ready to exit!
        # Ways to exit the game box:
        # 1) Torches have run out
        # 1) The player entered the exit box and:
        # 3)     There are no more questions
        # 4)     Enough coins were collected
        
        self.player.recordHistory(AlreadyExited=True)
        gameOver = self.data.recordIfGameCompleted()
        self.setupForLastQuestion()
        self.processFinishGame()
        self.data.startTime = None
        self.canvas.update()
        
    def processClosing(self, *args):
        self.canvas.update()
        Sleep(1) # So they can read the result of their answer
        if ( debugging:= self.data.getResource('debugging')): debugging.stop()
        if self.playersMap is not None:
            self.playersMap.undraw()
            self.playersMap = None
            self.canvas.update()
        self.data.removeResource("scenarioMap")
        self.nextFunction()
    
    def defaultReturn(self, *args):
        return
    