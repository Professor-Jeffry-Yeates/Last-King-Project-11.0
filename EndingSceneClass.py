__version__ = '8.0'
from CoffeeCanvas  import *
from CoffeeColors import *
from MapClass import *
from InstructionClass import *
# Used for email
# from asyncio import start_server
# from gettext import find
# from tarfile import LENGTH_LINK
# from telnetlib import NOP
# from datetime import datetime
# import win32com.client # may need: pip install pywin32  (may need to update pip)

class EndingSceneClass():
    """ 
    Holds all code needed to initialize, run, and close out the ending scene.
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
        self.dictionary = dict( **kwargs)
        self.nextFunction = self.dictionary.get("returnFunction", self.defaultReturn) 

        self.x = x
        self.y = y
        self.width = width
        self.height = height

        # Place objects and input use response
        self.questPlacement = self.dictionary.get("senarioInstructions", [0,0,0,0])
        self.finalMessagePlacement = self.dictionary.get("finalMessage", [0,0,0,0])

        # Code divided historically
        self.gameEndsReturnHome()
        self.finalMessage()
        self.canvas.update()

    # Set up the game is over, display an ending
    def gameEndsReturnHome( self, *args):
        # set something so when moving back to the entrace is called via after, we don't return to that: .after_cancel(id)
        timers = self.data.getResource("timers")
        timers.timerCentral.stop()

        # Copy the current instruction contents while instructions exist
        if ( instructions := self.data.getResource('instructions')):
            adventureText = instructions.get()

        # Remove most of the existing canvases
        for resourceName in ['playersMap','badges', 'statusBar', 'instructions', 'questionArea']:
            if ( resource := self.data.getResource(resourceName)):
                if hasattr(resource, 'undraw'):
                    resource.undraw()
                elif hasattr(resource, 'undrawMap'):
                    resource.undrawMap()
        if ( rewardBox := self.data.getResource('rewardBox')):
            rewardBox.undrawTitle()

        # Make a new map (which is the original map)
        quiz = self.data.getResource('quiz')
        self.senarioMapDictionary = {'x':self.x, 'y':self.y, 'width': self.width, 'height': self.height, 'mouseOnly':False,
                'mapImage':quiz["SenarioMap"], 'mapPath':quiz["SenarioMap Path"] }
        tags = self.dictionary.get('tags', "scenario")
        self.senarioMapDictionary['tags'] = tags
        self.map = MapClass(self.canvas, data=self.data, **self.senarioMapDictionary)

        # Movement has been lost somehow, so reinstate it
        

        # place the player back into their house
        targetCircleLocation = quiz.get("Target Location", (0,0))
        self.map.os_x_adjustment, self.map.os_y_adjustment = self.canvas.window.returnMacOSAdjustment()
        self.setupMap(alternativeDotStart=targetCircleLocation)

        # Set up a new instruction canvas with the copied adventure text plus epilogue
        self.questInstructions = InstructionClass( self.canvas, self.data, *self.questPlacement, text=adventureText, label="Adventury Diary")
        self.data.setResource('questInstructions', self.questInstructions)
        quiz = self.data.getResource('quiz')
        epilogueEnding = quiz.get("Epilogue", "You have completed the quest!")
        epilogText = self.data.makeTheEpilogue(epilogueEnding)
        self.questInstructions.newSection(epilogText)

        # Save the gameText into a file named "GameResult.txt in the current working directory
        self.data.writeGameResult("Game is Over", includeErrors=True)

    def OK_buttonSelected(self, *args):
        self.messageCanvas.undraw()
        self.canvas.widget.focus_set()

    # Set up any initial major map and the player dot or the map at the end with the player home
    def setupMap(self, targetCircleLocation=None, playerDotLocation='Center', alternativeDotStart=None):

        # This is the player's dot
        spotSizeRadius = 6
        senarioMapPlayer = Circle(self.map.canvas, -spotSizeRadius, -spotSizeRadius, spotSizeRadius, spotSizeRadius, fill="Lime")
        if targetCircleLocation is not None:
            circleLocation = self.map.convertStandardToMapCoordinates(targetCircleLocation[0], targetCircleLocation[1] )
            self.targetObject = MapCircle(self.map, circleLocation, 20, fill=None, outline="Red", width=3, action=self.playerReachesTarget,
                                argumentDictionary=self.argumentDictionary )

        if type(playerDotLocation) == str: # Right now "Center" is the only selection
            coord = self.map.getCurrentCenterLocation()
        else:
            coord = playerDotLocation
        
        # Mac OS is slow with tkinter so player moves farther
        self.map.os_x_adjustment, self.map.os_y_adjustment = self.canvas.window.returnMacOSAdjustment()

        self.map.setCenterObject( senarioMapPlayer, coord[0], coord[1])
        showPath = self.dictionary.get('showPath', False)

        # For debugging, show where player can travel on the map (takes several minuites)
        if showPath: self.map.showPathOnMap()

        # Display any NPC on the map
        quiz = self.data.getResource('quiz')
        localNPCs = quiz.get("NPCs",[])
        for npc in localNPCs:
            npcLocation = self.map.convertStandardToMapCoordinates(npc[1], npc[2])
            action = self.data.translateAction(npc[3])
            npcImage = MapImage(self.map.canvas, npcLocation[0], npcLocation[1], path=self.quiz["Objects Path"], image=npc[2], action=action)

        # Put the player on top
        self.map.setCenterObjectToTop()

    def finalMessage(self): # 300, 300, 400, 200
        title = "Game Completed"
        standardFont = ("TKDefaultFont", 12)
        (x, y, width, height) = self.map.getFourDimensions(self.finalMessagePlacement)
        height += 20
        width += 20
        self.messageCanvas = Canvas(self.canvas, x=x, y=y, width=width, height=height, background="Mist")
        OKButton(self.messageCanvas, Point(width-62,height-32), Point(width-2,height-2), OkText=" OK ",
                                 action=self.OK_buttonSelected, squaricle=True)

        text="You have completed the adventure! Your adventure has been saved to a file named 'GameResult.txt' \
and you can read about it in the instruction window. Turn in this GameResult file for grading. \
Close the game window to exit. Select 'OK' to close this popup, but you can wander around \
Seecyu land all you want. Watch out for trolls!"

        # Text box on the canvas holding the final message
        standardFormat = dict( sticky="ew", font=standardFont, padx=5, pady=5 )
        frameFormat = dict( sticky="full", relief=tk.SOLID, borderwidth=0,
                           font=(standardFont[0], standardFont[1], 'bold italic'))
        self.messageFrame = LabelFrame( self.messageCanvas, frameFormat, text=title,
                                       x=0, y=0, width=width, height=180, rowweights=1,
                                       columnweights=1)
        self.messageBar = TextBox(self.messageFrame, standardFormat, textFont=(standardFont[0], standardFont[1], 'italic'),
                                 relief="flat", wrap="word",
                                 scrolling=True, kind="vertical", readOnly=True)
        self.messageBar.setReadOnly(True)
        self.messageBar.set( text )
        
    def processClosing(self):
        self.map.undraw()
        self.canvas.update()
        self.map = None
        self.data.removeResource("scenarioMap")
        self.nextFunction()
               
    def defaultReturn(self, *args):
        """ Initial value for the return function so something is there. Overridden with the actual function."""
        return
    

# Activate if emailing or result requested
# def emailButtonSelected(window, statusBar, title):
#     """Called when email button is clicked - not tested"""
#     datestring = datetime.datetime.today().strftime('%Y-%m-%d')
#     contents = "Quiz Results for Quizzes:\n"
#     try:
#         # List all checkboxes which are checked
#         visibleCheckBoxWidgetDictionary = window.returnWidgets(limitTo=[ControlCheckBoxes])
#         for widgetName, widget in visibleCheckBoxWidgetDictionary.items():
#                 boxChecked = widget.value[widgetName]
#                 if boxChecked: contents += f"{widgetName}\n"
#         contents += "\n"

#         # Get all the answers and details for those quizzes
#         allWidgetDictionary = window.listVisibleActivatedWidgets()
#         numberOfQuestions = len(allWidgetDictionary)
#         correctAnswers = 0
#         for widgetTuple in allWidgetDictionary.values():
#             (value,answer,correct) = widgetTuple
#             if correct: correctAnswers += 1

#         # Results provided
#         if numberOfQuestions == 0:
#             contents += f"{datestring}: No questions answered correctly (0%) for quizzes"
#         elif numberOfQuestions == correctAnswers:
#             contents += f"{datestring}: All {numberOfQuestions} questions answered correctly (100%) for quizzes"
#         else:
#             grade = 100*(correctAnswers / numberOfQuestions) if numberOfQuestions > 0 else 0
#             contents += f"{datestring}: {correctAnswers} correct out of {numberOfQuestions} ({round(grade,2)}%) for quizzes"
#     except:
#         contents += f"Error: Unable to get the quiz results on {datestring}\n"

#     mailReciepient = "jeyeates@ccu.edu"
#     try:
#         outlook = win32com.client.Dispatch('outlook.application')
#         mail = outlook.CreateItem(0) # 0 is a mail item
#         mail.To = mailReciepient
#         mail.subject = title
#         mail.BodyFormat = 1 # Plain text
#         mail.Body = contents
#         mail.Send()
#         time.sleep(1) # Just to give it time, maybe not needed
#     except:
#         contents += "Error: Unable to send the email so no"
#     statusBar.set( f"{contents}\nEmail sent to {mailReciepient}")