__version__ = '11.0'
from CoffeeBean import *
from CoffeeCanvas import *
from MapClass import *
from PlayerClass  import *
from VocabularyClass import *
from DatabaseClasses import *
from datetime import *
import random, pathlib
import PythonSafeNodeVisitorClass 
import sys

class QuestionAreaClass():
    """Sets up an area for questions to be asked"""
    
    # Standard formatting dictionaries
    standardFont = ("TKDefaultFont", 12)
    frameFormat = dict( sticky="full", relief=tk.SOLID, borderwidth=1, font=(standardFont[0], standardFont[1], 'bold italic'), pady=5)
    standardFormat = dict( sticky="fullwidth", borderwidth=0, background='white', font=standardFont )
    headerTitleFormat = dict( sticky="fullwidth", borderwidth=0, background='white', font=(standardFont[0], standardFont[1], 'italic underline') )
    columnTitleFormat = dict( sticky="fullwidth", borderwidth=0, background='white', font=(standardFont[0], standardFont[1], 'italic') )
    labelFormatDictionary = dict(sticky=tk.LEFT, justify=tk.LEFT, borderwidth=0, background="White", font=standardFont )
    pictureFormatDictionary = dict(sticky=tk.TOP, relief=tk.GROOVE, justify=tk.LEFT, pady=(0,10) )
    headingFormatDictionary = dict( sticky="fullwidth", bg="LightGray", relief="solid", borderwidth=1 )
    buttonFormat = dict( padx=5, pady=5, borderwidth=1, font=standardFont)

    def __init__(self, canvas, data, *args, **kwargs):
        """     
        PARAMETERS:
         canvas:     where to draw graphics
         data:       all game data
         arguments:  x,y, width, height of the class on the canvas
         kwargs:    'TryLater'
                    'additionalHeight'
                    'additionalWidth'
         """
        self.parentCanvas = canvas
        self.canvas = None # Local canvas to be creared here
        self.data = data.setResource('questionArea', self)
        self.mapInUse = self.data.getResource('map')
        self.showTryLater = kwargs.get('TryLater', True)
        additionalHeight = kwargs.get('additionalHeight', 0)
        additionalWidth = kwargs.get('additionalWidth', 0)

        title = "Question Area"
        self.questionActive = False
        self.question = None
        self.mapObject = None
        self.widget = None
        self.frameForQuestions = None
        self.correctFunction = None
        self.secondTryFunction = None
        self.failureFunction = None
        self.submitProcessingFunction = None
        self.actualQuestionObject = None
        self.tries = 1
        self.answerSlot = 0
        self.answerLaterSlot = 1
        self.discardSlot = 2
        self.clearSlot = 3
        self.removableObjects = []
        self.parentCanvas.window.removeWidgets()

        # Get the positioning of the question area
        (self.x,self.y,self.width,self.height) = self.coordinatesFromArguments(args)

        # Frame contents
        self.buttonsVisible = True
        self.buttonOffset = 50
        self.canvasOffset = self.buttonOffset + 20
        frameHeight = self.canvasOffset
        questionAreaFormat = dict( sticky="full", relief=tk.SOLID, borderwidth=2, 
                                  font=(standardFont[0], standardFont[1], 'bold italic'), columnweights=1 )
        self.questionFrame = LabelFrame( self.parentCanvas, questionAreaFormat, text=title, x=self.x, y=self.y, 
                                        width=self.width, height=frameHeight, background="White") 

        frameFormat = dict( sticky="full", borderwidth=0 )#, relief=tk.SOLID)
        self.buttonFrame = Frame( self.questionFrame, frameFormat, columnweights=6, rowweights=1, 
                                 height=self.buttonOffset, background="White")

        # Button area
        self.grade_button = Button( self.buttonFrame, self.buttonFormat, background="Cyan", 
                                   text='Answer', coord=(0,self.answerSlot), sticky=tk.LEFT, action=self.on_grade)
        self.answerLater_button = None
        if self.showTryLater:
            self.answerLater_button = Button( self.buttonFrame, self.buttonFormat, background="LightYellow", 
                                       text='Answer Later', coord=(0,self.answerLaterSlot), sticky=tk.LEFT, action=self.on_answerLater)
            #self.answerLater_button.setCommand(self.on_answerLater)

        self.discard_button = Button( self.buttonFrame, self.buttonFormat, background="LightRed", 
                                   text='Discard', coord=(0,self.discardSlot), sticky=tk.LEFT, action=self.on_discard)

        # Canvas for questions
        width = self.width - 6
        height = self.height - self.canvasOffset - 5
        scrollingWidth = width + additionalWidth
        scrollingHeight = height + additionalHeight
        x = self.x
        y = self.y + self.canvasOffset

        self.scrollFrame = Frame(self.parentCanvas,  x=x, y=y, width=width+20, height=height+20, background=self.parentCanvas.colors["White"])
        self.scrollFrame.widget.pack_propagate(False)  # Prevent the frame from resizing to fit its contents
        
        canvasDictionary = dict(width=width, height=height, x=x, y=y, cursor="arrow", borderwidth=1, relief=tk.FLAT, 
                          scrollingregion=(0,0,scrollingWidth, scrollingHeight), confine=True)
        self.tags = kwargs.get('tags', "questionArea")

        self.canvas = Canvas(self.parentCanvas,  
                                background="Mist",
                                highlightbackground='Black', 
                                highlightcolor='Black',
                                **canvasDictionary ) 
        
        # Share the color dictionary
        self.canvas.colors = self.parentCanvas.colors
        
        # Setup scrolling
        self.canvas.widget.configure(xscrollincrement=10, yscrollincrement=10)

        # Additional width is optional
        if additionalWidth > 0:
            xscroll = ttk.Scrollbar(self.scrollFrame.widget, orient=tk.HORIZONTAL)
            xscroll.pack(side=tk.BOTTOM, fill=tk.X)
            xscroll.config(command=self.canvas.widget.xview)
            self.canvas.widget.configure(xscrollcommand=xscroll.set)

        yscroll = ttk.Scrollbar(self.scrollFrame.widget, orient=tk.VERTICAL)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        yscroll.config( command=self.canvas.widget.yview)
        self.canvas.widget.configure(yscrollcommand=yscroll.set)
        
        self.canvas.widget.configure(scrollregion=self.canvas.widget.bbox("all"))

        # Bind configuration events to the canvas' scroll bars with the scroll region provided
        self.canvas.widget.bind('<Configure>', lambda e: self.canvas.widget.configure(scrollregion=self.canvas.widget.bbox("all")))

        # Needed to keep debugging panel in its place below it, mist is a fine color
        Rectangle(self.canvas, 0,0, scrollingWidth, scrollingHeight, fill="Mist", width=0)
        
        # Set the function called for grading (can be changed depending on the question) and initial buttons are greyed out 
        self.resetGradeButton()
        self.hideButtons()
        self.canvas.update()

    def coordinatesFromArguments(self, args):
        if len(args) == 2:
            x,y = args[0]
            width,height = args[1] 
        elif len(args) >= 4:
            x,y,width,height = args[0],args[1],args[2],args[3]
        elif type(args[0]) == tuple:
            x,y = args[0]
            width,height = args[2],args[3]
        else:
            x,y = args[0],args[1]
            width,height = args[2]
        return x,y,width,height

    def undraw(self):
        self.stop()
        self.questionFrame.destroy()
        self.canvas.undraw()
        self.scrollFrame.destroy()

    def addEditingElement(self, item):
        if item is not None:
            self.removableObjects.append(item)
            
    def removeEditingElements(self):
        for item in self.removableObjects:
            if item is not None: 
                item.delete()
        self.removableObjects.clear()
        self.canvas.update()
        
    def on_grade(self, *args):
        """Called when grade button is clicked"""
        if not self.questionActive: 
            return # Phantom calls are coming in after processing
        
        # Gather resources
        #response is success (default False), optional: right (0,1), wrong(1,0), cleanup (T/F)
        statusBar = self.data.getResource('statusBar')
        success, right, wrong, cleanup  = self.submitProcessingFunction(self.canvas.window, statusBar) # Was gradeButtonSelected()
        self.mapObject.right = right
        self.mapObject.wrong =  wrong

        # Stop all movement while answering the question
        self.mapInUse.canvas.movementHalted = True

        # Track if we are on a first or second attempt and if 2nd attempts are allowed
        secondTry = None # self.question.get('Second Try', None)
        self.tries -= 1
        if self.question is None:
            self.tries = 0

        # Successful answer (based on the value(s) of the widgets in the question area)
        elif success:

            # Process function(s) for success, they can be in a list or multiple single functions in a list
            providedList = self.question['Success']
            if providedList is not None:
                actionList = providedList.copy()
                for action in actionList: 
                    if action is not None: 
                        if type(action) == list: 
                            for subAction in action:
                                if subAction is not None:
                                    subAction(self.mapObject) # Pass in the map object
                        elif self.mapObject is not None:
                            action(self.mapObject)
            self.tries = 0 # No more tries

        # Get ready to check for 2nd tries if allowed
        elif self.tries == 1 and secondTry is not None and len(secondTry) > 0:
            self.question['Success'] = secondTry

        # Check for failure function(s)
        elif self.question is not None: 
            providedList = self.question['Failure'] 
            if providedList is not None:
                actionList = providedList.copy()
                for action in actionList: 
                    if action is not None: 
                        if type(action) == list:
                            for subAction in action:
                                if subAction is not None:
                                    subAction(self.mapObject)
                        elif self.mapObject is not None:
                            action(self.mapObject)
            self.tries = 0
        
        # Failure but no failure message provided - should not occur
        else:
            self.tries = 0 
            if self.widget is not None:
                try:
                    self.widget.destroy() # Get rid of any question hanging around (it does happen)
                    self.widget = None
                except:
                    self.widget = None # If it isn'tthere, no problem

        # No more tries, so clean up the question area unless this questions clean up aftr itself
        if cleanup: self.clearAfterQuestion()
        
    def clearAfterQuestion(self):
        self.removeEditingElements()
        if self.tries <= 0:
            if self.canvas.window.numberOfWidgets() > 0:
                self.canvas.window.removeWidgets()
            if self.frameForQuestions is not None:
                try:
                    if self.frameForQuestions.widget is not None:
                        self.frameForQuestions.widget.destroy()
                except:
                    pass # If it is already removed, fine
        self.questionActive = False

        # If this questions finished the game, let the user know
        rewardBox = self.data.getResource('rewardBox')
        gameIsComplete = rewardBox.checkForGameOver()
        self.mapInUse.canvas.movementHalted = False
        
        # More to cleanup if the game is active 
        if not gameIsComplete:
            self.problemSumbit = self.gradeButtonSelectedStandard # Reset to normal
            self.hideButtons()
        self.canvas.update()
    
    def on_answerLater(self, *args):
        """ The mapObject contains the question, available to be selected later"""
        # Gather resources
        self.questionActive = False
        map = self.data.getResource('map')
        if map is not None: map.canvas.movementHalted = True

        # If there are widgets then there was a question to answer
        self.removeEditingElements()
        numberOfWidgets = self.canvas.window.numberOfWidgets()
        if numberOfWidgets > 0:
            message = "Answer that later"
            self.canvas.window.removeWidgets()
            self.frameForQuestions.widget.destroy()

        # Otherwise the "Answer Later" button was selected but there is nothing to answer later
        else:
            message = "Nothing to answer"
            statusBar = self.data.getResource('statusBar')
            if statusBar is not None: statusBar.set(message)

            # Insure if a stray question was hanging around that it is removed
            if self.frameForQuestions is not None:
                try:
                    if self.frameForQuestions.widget is not None:
                        self.frameForQuestions.widget.destroy()
                        self.frameForQuestions.widget = None
                        self.frameForQuestions = None
                except:
                    self.frameForQuestions = None # If already removed, fine

        map.canvas.movementHalted = False
        self.resetGradeButton()
        self.hideButtons()
        self.canvas.update()

    def stop(self):
        """Close down the question area"""
        self.questionActive = False
        map = self.data.getResource('map')
        if map is not None: map.canvas.movementHalted = True
        self.removeEditingElements()
        if self.canvas.window.numberOfWidgets() > 0:
            self.canvas.window.removeWidgets()
        self.removeUnusedButtons()
        self.canvas.update()

    def resetButtonSelected(self, window, statusBar):
    #    """Called when reset button is clicked, or after Save"""
        for widget in window.widgets:
            if widget.activated:
                widget.clear()
        statusBar.set( f"All values reset")

    def gradeButtonSelectedStandard(self, window, statusBar):
    #    """Called when grade button is clicked"""
        #datestring = datetime.today().strftime('%Y-%m-%d')s
        right, wrong = 0,0
        if len(window.widgets) == 0:
            statusBar.set( f"There are no questions to answer")
            success = False
        else:
            invalidValues = window.validateVisibleActivatedWidgets()
            if len(invalidValues) == 0:
                statusBar.set( f"That was answered correctly")
                success = True
                right = 1
            else:
                success = False
                wrong = 1
                warning = ""
                useComma = False
                if isinstance(invalidValues, list):
                    for widget in invalidValues:
                        names = widget.getTitle()
                        if isinstance(names, str):
                            if useComma:
                                warning += f", {names}"
                            else:
                                warning = f"{names}"
                            useComma = True
                        else:
                            warning ="Unknown error:"
                elif isinstance(invalidValues, dict):
                    number = len(invalidValues)
                    warning = "incorrect answer" if number == 1 else "incorrect answers"
                    missing = "part" if number == 1 else "parts"
                statusBar.set( f" Missed {len(invalidValues)} {missing} of the question with {warning}")
        cleanup = True
        return success, right, wrong, cleanup

    def on_discard(self, *args):
        """Question is discarded"""
        self.removeEditingElements()
        if self.frameForQuestions is not None:
            try:
                if self.frameForQuestions.widget is not None:
                    self.frameForQuestions.widget.destroy()
                    self.frameForQuestions.widget = None
                    self.frameForQuestions = None
            except:
                self.frameForQuestions = None # If already removed, fine

            # No more tries, so clean up the question area
            self.tries = 0 
            self.questionActive = False
            map = self.data.getResource('map')
            if map is not None: map.canvas.movementHalted = True
            if self.canvas.window.numberOfWidgets() > 0:
                self.canvas.window.removeWidgets()

            if self.mapObject is not None: self.mapObject.undraw()
            map.canvas.movementHalted = False

            # If this questions finished the game, let the user know
            statusBar = self.data.getResource('statusBar')
            statusBar.set( "Discarded question!")
            rewardBox = self.data.getResource('rewardBox')
            if rewardBox is not None: rewardBox.checkForGameOver()
        self.resetGradeButton()
        self.hideButtons()
        self.canvas.update()

    def replaceSubmitProcessingFunction(self, code):
        """ This can be specific to a type of problem. Always reset to the default when done."""
        self.submitProcessingFunction = code
        
        
    def resetGradeButton(self):
        """Reset the submit/grade processing function to the standard handler.

        Use this after `replaceSubmitProcessingFunction` has been called to
        restore the default grading behavior (`gradeButtonSelectedStandard`).
        """
        self.submitProcessingFunction = self.gradeButtonSelectedStandard

    def hideButtons(self):
        if ( button := self.grade_button): button.widget.config(state=tk.DISABLED)
        if ( button := self.answerLater_button ): button.widget.config(state=tk.DISABLED)
        if ( button := self.discard_button): button.widget.config(state=tk.DISABLED)

    def revealButtons(self):
        if ( button := self.grade_button): button.widget.config(state=tk.NORMAL)
        if ( button := self.answerLater_button ): button.widget.config(state=tk.NORMAL)
        if ( button := self.discard_button): button.widget.config(state=tk.NORMAL)
    
    def removeUnusedButtons(self):
        if ( button := self.answerLater_button ): button.undraw()
        if ( button := self.discard_button): button.undraw()
        self.discard_button = None
        self.answerLater_button = None

    def makeStoryLine(self, mapObject):
        # Set up the descriptions using random phrases
        story = ""
        firstLine = ""
        secondLine = ""
        
        # Story line depends on the map object
        if mapObject is None: # Probably caught before this, but added as protection
            return story
        
        elif hasattr(mapObject,'npc') and mapObject.npc == True:
            # Questions as from a NPC 
            npc = mapObject.parent
            name = npc.dictionary.get("Special",mapObject.name)
            kind = npc.dictionary["Name"]
            color = npc.dictionary["Color"]
            firstLine =  f"{name}, the {color} {kind}, has question for you. "
            definition = "You feel some {1} motivation that is {2} you to answer"
            options = "adv_unusual,verb_compelling"
            secondLine = self.data.vocab.complete(definition, options, name )
            
        elif type(mapObject) == str and len(mapObject) > 0:
            # Non-object questions from something besides an NPC (referred to by name) do not have a mapObject, just a name
            name = mapObject
            definition =  "The {0} has a {1} disguised as a question for you"
            options ="noun_riddle"
            firstLine = self.data.vocab.complete(definition, options, name ) 
            definition = "You feel some {1} motivation that is {2} you to answer"
            options = "adv_unusual,verb_compelling"
            secondLine = self.data.vocab.complete(definition, options, name )
            
        elif hasattr(mapObject, 'name'):
            # Object questions have a mapObject with a type and location
            name = mapObject.name
            definition =  "There is a {1} on the {0}" #""
            options ="noun_riddle,{0}_verb_usage"
            firstLine = self.data.vocab.complete(definition, options, name ) 
            definition = "You feel some {1} {2} that is {3} you to answer it's question! You step closer"
            options = "adv_unusual,noun_invisible_force,verb_compelling"
            secondLine = self.data.vocab.complete(definition, options, name )
        story = firstLine + secondLine
        return story
    
    # Sterling;Shilling(2)
    def sterlingPhrase(self, reward):
        rewardText = ""
        moneyList = reward.lower().split(";")
        for eachMoney in moneyList:
            rewardCoins = ""
            coin,number = self.data._extractParameter(eachMoney)
            if coin is not None and number is not None:
                if isinstance(number, str): number = int(number)
                useNumber = min(max(number,0),1000)
                if useNumber > 0:
                    if coin == "pence":
                        rewardCoins = f"{useNumber} pence"
                    elif coin == "shilling":
                        rewardCoins = f"{useNumber} shilling"
                    elif coin == "pound":       
                        rewardCoins = f"{useNumber} quid"    
                    else:
                        continue     
                if len(rewardText) > 0:
                    rewardText += ", " + rewardCoins
                else:
                    rewardText = rewardCoins
        return rewardText
    
    def bountyPhrase( self, reward ):
        rewardText = ""
        moneyList = reward.lower().split(";")
        for eachMoney in moneyList:
            rewardCoins = ""
            coin,number = self.data._extractParameter(eachMoney)
            if coin is not None and number is not None:
                if isinstance(number, str): number = int(number)
                useNumber = min(max(number,0),1000)
                if useNumber > 0:
                    if coin == "gold":
                        rewardCoins = f"{useNumber} gold"
                    elif coin == "silver":
                        rewardCoins = f"{useNumber} silver"
                    elif coin == "copper":       
                        rewardCoins = f"{useNumber} copper"    
                    else:
                        continue     
                    plural = " piece" if useNumber == 1 else " pieces"
                if len(rewardText) > 0:
                    rewardText += ", " + rewardCoins + plural
                else:
                    rewardText = rewardCoins  + plural
        return rewardText

    def rewardAndPenaltyText(self,  title, name, question ):
        reward = question.get("Reward","")
        penalty = question.get("Penalty", "")
        rewardText = ""
        penaltyText = ""
        
        # Determine the title for the question
        sentence = "Title: "
        titleLength = len(title) if title is not None else 0
        nameLength = len(name) if name is not None else 0
        if nameLength > 0:
            sentence += name
            if titleLength > 0:
                sentence += " or " + title
        elif titleLength > 0:
            sentence += title
        else:
            sentence = "Unknown question"
        
        # Determine in any reward information
        if reward is not None:
            if isinstance(reward, str) and len(reward) > 0:
                rewardText = reward
                
                # Figure the reward first
                if reward.startswith("Sterling"):
                    rewardText = self.sterlingPhrase( reward)
                elif reward.startswith("Bounty"):
                    rewardText = self.bountyPhrase( reward)         
        
        # Determine in any penalty information
        if penalty is not None:
            if isinstance(penalty, str) and len(penalty) > 0:
                penaltyText = penalty
                if penalty.startswith("Sterling"):
                    penaltyText = self.sterlingPhrase( penalty)
                elif penalty.startswith("Bounty"):
                    penaltyText = self.bountyPhrase( penalty)     
                    
        # Add in any reward or penalty information
        rewardExists = len(rewardText) > 0  
        penaltyExists = len(penaltyText) > 0         
        if rewardExists:
            sentence += f" ({rewardText}"
            if penaltyExists:
                sentence += f" or lose {penaltyText})"
            else:
                sentence += ")"
        elif penaltyExists:        
            sentence += f" (lose {penaltyText} if missed)"
        return sentence
    
    def implementQuestion(self, mapObject, randomize=False):
        """Provided with a map object which contains the question, implement it in the question area."""
        vocab = self.data.getResource('vocabulary')
        # Users can only have one active question at a time and the mapObject must be useful
        if self.questionActive: 
            message = self.data.getResource('message')
            if message: message.set("....Oops, you haven't answered the first question yet!")
            return
        
        # There may be no more objects or questions available
        if mapObject is None:
            if (message := self.data.getResource('message')):
                message.set("There is no more treasure to be found!")
            return        
        # There may be no more objects or questions available
        if mapObject.question is None:
            if (message := self.data.getResource('message')):
                message.set("There are no more questions!")
            return

        # Setup for a question 
        self.mapObject = mapObject
        self.question = mapObject.question
        
        # Additional information
        titleCheck = self.question.get('Title', None)
        nameCheck = self.question.get('Name', None)
        if ( player := self.data.getResource("player")):
            player.lastQuestionObject = mapObject
        if ( instructions := self.data.getResource("instructions")):
            text = f'\nQuestion asked: {mapObject.question["Title"]}.  '
            text = vocab.cleanUpPunctuation(text)
            instructions.newSection(text)
        
        # Setup for a valid question with a Type
        questionType = self.question["Type"].lower().strip().replace(" ","")
        if questionType is None:
            message = self.data.getResource('message')
            if message: message.set(f"....Oops, the question {nameCheck} titled {titleCheck} has no type and is not written correctly!")
            return
            
        if nameCheck is None or titleCheck is  None:
            message = self.data.getResource('message')
            if message: message.set("....Oops, the question is missing the name or title and is not written correctly!")
            return
            
        """THIS SECTION DESCRIBE HOW TO USE QUESTIONS
        #Automatically format a form based on data (from a JSON file).
        #PARAMETERS:
        #    data: A dictionary of data from a JSON file
        #    form: The frame used as a form to be formatted with the data
        #    randomizeAndLimit=None is an override of all data to randomize and limit the number of quiz questions
        #    graphicFolder=None is the folder localion of any graphic file referenced from the current working directory 
        #The top level elements in the JSON file are:
        #    "Title": "Name on the form" which can have the success valur follow in in parens
        #    "Name": "Name of the table" used in grading
        #    "Search Tags": Easier search field, Name is usually sufficient unlass it is duplicated and you need to search
        #    "Type": Type of question, such as True False, Check Box, Radio Button, etc... including tables of popups
        #            T/F is a form of Radio Button.
        #    "Success" not "Points": points for the question (metal coins of Gold, Silver, Copper)
        #    "Failure" not "Points": Optional - points removed on wrong answer (metal coins of Gold, Silver, Copper)
        #    "Instructions": General instructions for the questions (optional)
        #    "Text": Question or specific answer instructions
        #    "Options": [   Various type-specific questions and answers. Optional for T/F questions. Can be any number of elements.
        #        { "Item": 1, "text": "Freesac leaves" },  Item is optional, actual text by itself is required but does not need 'text' key
        #        { "Item": 2, "text": "Freesac fruit" },
        #        { "Item": 3, "text": "Freesac bark" },
        #        { "Item": 4, "text": "Freesac roots" }
        #    "Answer": Optional - The answer to the question, or the first item if absent. If an integer is provided instead then
        #                         that is the item's position in the list of options, starting at 0. Note text is returned
        #                         so numbers will be text of that number, not an actual number.
        #Table Specific Elements:
        #    "TableName": "Name of the table" used in grading, yes, duplicated temporarily
        #    "Headers": ["Header1", "Header2", ...] for the table show up first and do not use data
        #    "Choices": default is 5, the maximum number of choices to choose from (fewer may be available)
        #    "MaxColumn": default is 10001, the maximum number of widgets on a row
        #    "Continuous": default is False, continue placing widgets in a row until maxColumn is reached
        #    "Vertical": default is False, tables list vertically, not horizontally
        #    "PicturePath": default is None, the path to the folder with pictures
        #    "Table": [ [row1], [row2], ... ] describes the layout for each column in the form as a table
        #    "Columns": [ [column1], [column2], ... ] where each is a row of data with elements placed into columns
        #The "Table" entries are as follows: 
        #    "Row" is a row number and does not draw out of the data
        #    "Frame" is a frame to hold other elements (not implemented)
        #    "Heading" is a formatted label for a heading.  Usually used once before the tabls and columns are diaplayed
        #    "Label" is text that is displayed and does not contain any choices for an answer in conjunction with a combo box
        #    "Combo" is a combobox for choosing from possible answers
        #    "Picture" is a picture displayed rather than text used in conjunction with a combo box
        #    "Group" allows the data to be placed in a column of data to be accessed as needed, not displayed
        #    "Criteria" allows the data to be placed in a column of data to be accessed as needed, not displayed
        #    Colors for "fg" and "bg" or other Tkinter parameters in pairs can follow the preceeding parameters for 
        #        formatting if they are displayable, however, Comboboxes may not format as expected 
        #The "Combo" popup elements are "COMBO", question name (used in grading), width of column, and:
        #    "UNIQUE" if only unique values are to be used in the possible answers
        #    "criteria" followed by the column is to be used to find matching criteria in other columns for unique answers
        #    "group" followed by a column is to be used to find matching groups in the group column for unique answers
        #    "choose" multiple choice values from the line of data are used as possible unique answers with the answer listed first
        #    "ORDERED" as the second item in a "choose" list will keep the order of the choices if the answer is in the list
        #    Colors for "fg" and "bg" or other Tkinter parameters in pairs can follow the preceeding parameters for 
        #        formatting, however, Comboboxes may not format as expected 
        """
        
        # OK, we have the a start to a question
        statusBar = self.data.getResource('statusBar')
        statusBar.add( f"\nThe question is {nameCheck} concerning {titleCheck}")
        self.questionActive = True
        map = self.data.getResource('map')
        if map is not None: map.canvas.movementHalted = True

        # A separate frame is needed for the question area (it gets deleted when the question is done)
        questionFrame = self.canvas
        frameFormat = dict( sticky="full", relief=tk.SOLID, borderwidth=1, pady=5)
        self.frameForQuestions = Frame(questionFrame, frameFormat, background="Mist", 
                                       padx=3, pady=3, sticky=tk.LEFT, coord=(2,0), x=1,y=1)
        
        # The title of the question along with its reward and optional penalty
        title = self.rewardAndPenaltyText( titleCheck, nameCheck, self.question)

        # Approximate how many rows the instructions will take
        instructions = self.question.get("Instructions", "")
        rows = 0 
        if len(instructions) > 0: rows += 1
        if len(self.question.get("Options", [])) > 0: rows += 1
        if len(self.question.get("Columns", [])) > 0: rows += 1

        # Place the instructions into the next available row, not available: font=(standardFont[0], standardFont[1], 'bold italic'), 
        plainFrameFormat = dict( sticky="full", pady=5)
        localFrame = Frame(self.frameForQuestions, plainFrameFormat, columnweights=1, rowweights=rows)
        rows, columns = 0, 0
        if len(title) > 0: # removed <cr> from end of title
            self.titleLabel = Label(localFrame, text=title, sticky="ew", anchor=tk.NW, justify=tk.LEFT, grid=(rows, columns), 
                               borderwidth=0, width=self.width-5, 
                               background="Mist", font=(standardFont[0], standardFont[1], 'bold' ))
        self.canvas.update()
        
        # Put the whole story together
        story = self.makeStoryLine( mapObject )
        fontSize = 12
        storyFormat = dict( padx=5, pady=5, font=("TKDefaultFont", fontSize, 'italic'), 
                           background="Mist") # No sticky="ew"
        localLabelUsed = len(instructions) > 0 and questionType != "codecheck"
        storyHeight = 4 if localLabelUsed else 3
        storyWidth = int((self.width)/fontSize) + 1
        
        # Here is the story. Insure this text box is not mistaken as one of the questions
        if len(story) > 0:
            storyTextBox = TextBox(localFrame, storyFormat, text=story, pack=True,
                                 relief="flat", wrap="word", width=storyWidth, height=storyHeight,
                                 scrolling=False, readonly=True)
        self.canvas.update()
        
        # Question instructions follow
        if localLabelUsed:
            instructionLabel = Label(localFrame, text=instructions, sticky="w", anchor=tk.NW, 
                                     justify=tk.LEFT,  grid=(rows, columns), borderwidth=0, width=self.width-5, 
                                     background="Mist", font=(standardFont[0], standardFont[1]) )
            rows += 1
        self.canvas.update()
        self.revealButtons()

        # Now match with the type of question. These each handle their own code
        self.actualQuestionObject = None
        if self.data.debugging: # When debugging, errors should be obvious
            somethingFound = self.useSpecificQuestion( questionType, localFrame, rows)
        else:
            try:
                somethingFound = self.useSpecificQuestion( questionType, localFrame, rows)
            except:
                somethingFound = False
                if ( message := self.data.getResource('message') ):
                    message.set(f"....Oops, that treasure mysteriously disappeared!")
                self.data.logError(f"Error implementing question {nameCheck} titled {title} of type {questionType}")

        if somethingFound:
            self.revealButtons()
        self.canvas.update()

    def useSpecificQuestion(self, questionType, localFrame, rows):
        """ Here are the possible question types to choose from."""
        somethingFound = True
        match questionType:
            case "checkbox":
                self.actualQuestionObject = CheckboxQuestionClass(self.canvas, self.question, localFrame, rows)
            case "radiobuttons":
                self.actualQuestionObject = RadioButtonQuestionClass(self.canvas, self.question, localFrame, rows)
            case "combobox":
                self.actualQuestionObject = PopupQuestionClass(self.canvas, self.question, localFrame)
            case "picture":
                ##                                                  canvas, data,  questionArea, localFrame, rows, **kwargs
                self.actualQuestionObject = TableQuestionClass(self.canvas, self.question, self, localFrame, rows, maxHeight=200, maxColumn=5 )
                widget = self.actualQuestionObject.tableFrame.widget
                height = widget.winfo_reqheight() + 500
                width = widget.winfo_reqwidth()
                localFrame.widget.config(width=width, height=height)
            case "codecheck":
                self.actualQuestionObject = CodeEditorClass(self, self.question, localFrame, rows)
            case "table":
                ##                                                  canvas, data,     questionArea, localFrame, rows, **kwargs
                self.actualQuestionObject = TableQuestionClass(self.canvas, self.question, self,    localFrame, rows)
            case "popup":
                self.actualQuestionObject = PopupQuestionClass(self.canvas, self.question, localFrame)
            case "truefalse":
                self.actualQuestionObject = RadioButtonQuestionClass(self.canvas, self.question, localFrame, rows, randomize=False)
            case "yesorno":
                self.actualQuestionObject = RadioButtonQuestionClass(self.canvas, self.question, localFrame, rows, randomize=False)
            case "multiplechoice":
                self.actualQuestionObject = RadioButtonQuestionClass(self.canvas, self.question, localFrame, rows)
            case "multipleanswer":
                self.actualQuestionObject = CheckboxQuestionClass(self.canvas, self.question, localFrame, rows)
            case "multipleselect":
                self.actualQuestionObject = CheckboxQuestionClass(self.canvas, self.question, localFrame, rows)
            case _:
                somethingFound = False
        return somethingFound

###############################################################################
# Following are the classes for each type of question

class RadioButtonQuestionClass():
    def __init__(self, canvas, dataDictionary, localFrame, rows, **kwargs):
        self.canvas = canvas
        randomize = kwargs.get("randomize", True)
        vertical = kwargs.get("vertical", True )
        self.question = dataDictionary
        standardFormat = dict( sticky="left", borderwidth=0, background="White", font=standardFont )

        text = dataDictionary.get("Text", "Select:")
        name = dataDictionary.get("Name", text)
        title = dataDictionary.get("Title", "Radio Buttons")

        radioOptions = dataDictionary.get("Options", [])
        defaultBooleanOrder = True
        questionType = dataDictionary["Type"].lower().strip().replace(" ","")
        if len(radioOptions) == 0:
            if questionType == "yesorno":
                radioOptions = ["Yes","No"]
                title = f"{radioOptions[0]}/{radioOptions[1]} Question"
                defaultBooleanOrder = False
            elif questionType == "truefalse":
                radioOptions = ["True","False"]
                title = "True/False Question"
                defaultBooleanOrder = False
                
        firstOptionCanBeTheAnswer = radioOptions[0] if len(radioOptions) > 0 else None
        answer = dataDictionary.pop("Answer", firstOptionCanBeTheAnswer)
        if isinstance(answer, int):
            number = answer
            if 1 <= number <= len(radioOptions):
                answer = radioOptions[number-1]
        elif isinstance(answer, str) and len(answer) == 0:
            answer = firstOptionCanBeTheAnswer
                
        if randomize: 
            random.shuffle(radioOptions)
        elif not defaultBooleanOrder: 
            radioOptions.reverse() # Will be reversed going into the question code
        
        width = self.canvas.width
        self.question = ValidRadioBox(localFrame, radioOptions, standardFormat, coord=(rows,0), vertical=vertical, 
                               text=text, name=name, answer=answer, title=title, maxwidth=width)

class CheckboxQuestionClass():
    """Any number of questions with a checkbox"""
    def __init__(self, canvas, dataDictionary, localFrame, rows, **kwargs):
        self.canvas = canvas
        randomize = kwargs.get("randonmize", False)
        checkboxOptions = dataDictionary.get("Options", [])
        
        answer = dataDictionary.get("Answer", [])
        if len(answer) > 0:
            if isinstance(answer[0], int):
                newList = []
                for number in answer:
                    if type(number) != int: continue
                    if 1 <= number <= len(checkboxOptions):
                        text = checkboxOptions[number-1]
                        newList.append(text)
                dataDictionary["Answer"] = newList
        answer = dataDictionary["Answer"]

        if randomize: random.shuffle(checkboxOptions)
        else: checkboxOptions.reverse()

        vertical = kwargs.get("vertical", True )
        self.question = dataDictionary
        standardFormat = dict( sticky="left", borderwidth=0, font=standardFont )
        text = dataDictionary.get("Text", "Select:")
        name = dataDictionary.get("Name", text)
        title = dataDictionary.get("Title", "CheckBoxes")
        
        success = dataDictionary.get("Success", None)
        if success: title += f" ({success})"
        width = self.canvas.width
        
        self.question = CheckBoxes(localFrame, checkboxOptions, standardFormat, coord=(rows,0), vertical=vertical, 
                            text=text, name=name, answer=answer, title=title, maxwidth=width)
"""_summary_
   #{
   #"Title": "1.5: Cables",
   #"TableName": "Cables",
   #"Headers":[" Row ","Abbreviation","Media ","Description "],
   #"Table": [
   #    "ROW",
   #    "LABEL",
   #    ["COMBO", "Media", 34,"Unique"],
   #    ["COMBO", "Desc", 80,"Unique"]
   #],
   #"Columns":[
   #    ["DAC","Direct Attach Copper", "Copper wire connector used to connect network devices"],
   #    ["Coaxial","Coaxial Cable", "High capacity shielded cable used for cable TV and internet"],
   #    ["Fiber Optic","Fiber Optic Cable", "Fiber cable used for high-speed data transmission"],
   #    ["Fiber Channel","Fiber Channel Cable", "Fiber loss-less high-speed data transfer protocol for commercial storage"],
   #    ["SPF","Small Form-factor Pluggable", "Small hot-pluggable (copper or fiber) connector used with network devices"],
   #    ["SFP+","Small Form-factor Pluggable Plus", "Small hot-pluggable connector for faster and longer connections"],
   #    ["QSFP","Quad Small Form-factor Pluggable", "Double fiber pairs (4 total) for high-speed hot-pluggable data transmission"],
   #    ["QSFP+","Quad Small Form-factor Pluggable Plus", "Double fiber pairs for higher-speed/distance connectors"],
   #    ["SC","Subscriber connector", "Fiber connector (push-lock mechanism) used to connect network devices"],
   #    ["LC","Lucent connector", "Small form-factor fiber connector used to connect network devices when disconnection is needed"],
   #    ["ST","Straight Tip", "Fiber connector  (early bayonet-lock mechanism) used to connect network devices"],
   #    ["BNC","Bayonet Neill-Concelman", "Coaxial connector using a Bayonet mount (push & twist)"],
   #    ["RJ-11","Registered Jack-11", "4-wire jack for twisted pair connector used to connect phones"],
   #    ["RJ-45","Registered Jack-45", "8-wire jack for twisted pair connector used to connect network devices"]
   #]
   #}
   #{
   #"Title": "4.2: Troubleshooting Methodology",
   #"TableName": "Trouble",
   #"Headers":["Category","Troubleshoting Concept","Description"],
   #"Table": [
   #  ["COMBO", "Category", 15, "GROUP", 3],
   #  "LABEL",
   #  ["COMBO", "Desc", 75, "GROUP", 3],
   #   "GROUP" ],
   #"Columns": [
   #["Step 1","Identify the problem","Identify the problem being methodical and logical","Step"],
   #["Identify","Gather information","Visit physically and check: documentation, logs, vendor sites, & forums","Identify"],
   #["Identify","Duplicate the problem", "If possible, you or the user should duplicate the problem", "Identify"],
   #["Identify","Question users","Ask open questions (not yes/no), encourage their words and avoid assumptions, ","Identify"],
   #["Identify","Determine if anything has changed","Ask details of if it ever worked or what has changed since it worked last","Identify"],
   #["Identify","Approach multiple problems individually","Multiple symptoms may be one problem but approach them one at a time","Identify"],
   #["Step 2","Theory of cause","Establish a theory of probable cause based on your research","Step"]
   #}
   #{
   #        "ID": 4,
   #        "Title": "Who is on the team?",
   #        "Type": "Multiple Select",
   #        "Order": "Random",
   #        "Question": "Who is on the team?",
   #        "Choices": ["Joe", "Babe", "Bob", "Abbott","Costello"],
   #        "Answer": ["Joe", "Babe"],
   #        "Points": 2
   #    },
   #    {
   #        "ID": 5,
   #        "Title": "What is on the team?",
   #        "Type": "True or False",
   #        "Format": "Popup",
   #        "Question": "The team's logo is a turkey",
   #        "Answer": false,
   #        "Points": 3,
   #        "Coin": "Gold"
   #    }
   #    {
   #"Title": "OSI Model - Multiple Choice",
   #"TableName": "General",
   #"Headers":["Row ","Multiple Choice Questions","Multiple Choice Answers (choose one)"],
   #"Table": [
   #  "ROW",
   #  "LABEL",
   #  ["COMBO", "Question", 30,"CHOOSE", 55]],
   #"Columns": [ 
   #["The CRC mechanism in Ethernet allows for the retransmission of damaged frames.","False,ORDERED,True,False"],
   #["At which OSI layer is the concept of a port number introduced?", "Transport,ORDERED,Physical,Data Link,Network,Transport,Session,Presentation,Application" ],
   #["At which layer of the OSI model is no header encapsulation applied?", "Physical,ORDERED,Physical,Data Link,Network,Transport,Session,Presentation,Application" ],
   #["Which grade of fiber have a 62.5 micron core?","Single mode fiber,Multimode fiber"]
   #}
   #{   
   #"Title": "1.4: IPv4 Classes",
   #"TableName": "IPv4",
   #"Headers":["Row ","IPv4 Network Class", "Beginning Octet","Default Subnet Mask","Number of Networks", "Max Hosts per Network"],    
   #"Table": [
   #    "ROW",
   #    "LABEL",
   #    ["COMBO", "Octet", 12,"Unique"],
   #    ["COMBO", "Mask", 16,"Unique"],
   #    ["COMBO", "Network", 16,"Unique"],
   #    ["COMBO", "Host", 16,"Unique"]
   #],
   #"Columns":[
   #    ["Class A","1-127",  "255.0.0.0",    "126",   "16,777,214"],
   #    ["Class B","128-191","255.255.0.0",  "16,384",    "65,534"],
   #    ["Class C","192-223","255.255.255.0","2,097,152",    "254"],
   #    ["Class D","224-239","None",          "None",       "None"],
   #    ["Class E","240-255","None",          "None",       "None"]
   #]
   #}
   #{
   #"Title": "1.5: Cable Pictures",
   #"TableName": "Connector",
   #"Vertical": true,
   #"Continuous": true,
   #"MaxColumn": 2,
   #"PicturePath": "StandardCablePictures",
   #"Table": [
   #  "HEADING",
   #  ["COMBO", "Pic", 7, "Criteria", 3],
   #  "PICTURE",
   #  "CRITERIA"],
   #  "MeaningOfColumns": "General group title shown, name to match, file, selection group name",
   #"Columns": [
   #["Twisted Pair","Ethernet cable", "TwistedPair", "Cat"],
   #["Cat 1",       "Door bell","Cat1", "Cat"],
   #["Cat 3",       "Telephone", "Cat3", "Cat"]
   #}
   #        {
   #"Type": "CodeCheck",
   #"Language":"SQL",
   #"File":"Problem_01.txt",
   #"Success":"Silver",
   #"Second Try":"Copper",
   #"Penalty":"Copper"
   #}     
   #,{
   #  "Filename":"Problem__2",
   #  "Type": "CodeCheck",
   #  "Language":"Python",
   #  "Name": "Problem #2",
   #  "Title": "What are the possibilities?",
   #  "Instructions": "Set the variable called 'answer' equal to the calculations.",
   #  "Answer":5,
   #  "Return":5,
   #  "Arguments":[900,5],
   #  "Dictionary":{"each":"to his own"},
   #  "Code":"def myFunction(a,b):\nz = math.sqrt(7000)\nz = int(3) + float(a + z)\nx = max(7,min(2,9000 + b))\ny = ((b * x**3)/(x-b))/a\nanswer = 5\nc = sum([1,2,3,4,5])\nc = True\nc = 'abcdefg'\nb = c[2:-1]\nreturn answer\n"
   #  }
   #  {
   #"Title": "What are the Possibilities?",
   #"Type": "CodeCheck",
   #"Language": "Python",
   #"Category": "Math",
   #"PostReGex":['.* answer .*=','.* return .*answer'],
   #"Required":["answer"],
   #"Variables": ["answer"],
   #"Parameters":[5000,99],
   #"Return":15,
   #"Instructions": "Set the variable called ~answer~ equal to the provided sum function (near line 6) and return it."
   #}
   #def myFunction(a,b):
   #   #z = math.sqrt(7000)
   #   #z = int(3) + float(a + z) 
   #   #x = max(7,min(2,9000 + b))
   #   #y = ((b * x**3)/(x-b))/a
   #   #answer = sum([1,2,3,4,5])
   #   #c = True
   #   #c = 'abcdefg'
   #   #b = c[2:-1]
   #   #return answer
   #   #{
   #"Title": "What's Up, Dep?",
   #"Type": "CodeCheck",
   #"Language":"SQL",
   #"Name": "Problem #5",
   #"Database":"Sample",
   #"Instructions": "Return the whole department table.",
   #"Code":"",
   #"Return":"dept_no,dept_name,location\nd1,Research,Dallas\nd2,Accounting,Seattle\nd3,Marketing,Dallas"
   #}
   #{
   #"Title": "Join the Party?",
   #"Type": "CodeCheck",
   #"Language":"SQL",
   #"Name": "Problem #10",
   #"Database":"Sample",
   #"Instructions": "Join the employee and department tables on their common column",
   #"Answer":"select * from employee join department on department.dept_no = employee.dept_no"
   #}
   #sect * from employee join department on department.dept_no = employee.dept_no
   #-----------------------------
   #emno,emp_fname,emp_lname,dept_no,dept_no,dept_name,location
   #25,"Elsa                ","Bertoni             ","d2  ","d2  ","Accounting               ","Seattle                       "
   #90,"Elke                ","Hansel              ","d2  ","d2  ","Accounting               ","Seattle                       "
   #102,"Ann                 ","Jones               ","d3  ","d3  ","Marketing                ","Dallas                        "
   #186,"John                ","Barrimore           ","d1  ","d1  ","Research                 ","Dallas                        "
   #258,"Matthew             ","Smith               ","d3  ","d3  ","Marketing                ","Dallas                        "
   #289,"Sybill              ","Moser               ","d1  ","d1  ","Research                 ","Dallas                        "
   #296,"James               ","James               ","d2  ","d2  ","Accounting               ","Seattle                       "
   #
   #"Type": "CodeCheck",
   #"Language":"SQL",
   #"File":"SQL_Problem_01.txt",
   #"Success":"Silver",
   #"Second Try":"Copper",
   #"Penalty":"Copper"
   #    
   #
   #"Type": "CodeCheck",
   #"Language":"SQL",
   #"File":"SQL_Problem_01.txt",
   #"Success":"Gold",
   #"Penalty":"Silver"
   # 
   """
class PopupQuestionClass():
    def __init__(self, canvas, dataDictionary, localFrame, **kwargs):
        self.canvas = canvas
        randomize = kwargs.get("randomize", True)
        self.question = dataDictionary
        background = self.canvas.background 
        standardFormat = dict( sticky="fullwidth", borderwidth=0, background=background, font=standardFont )
        popupOptions = dataDictionary.get("Options", [])
        
        if randomize: random.shuffle(popupOptions)
        else: popupOptions.reverse()

        text = dataDictionary.get("Text", "Select just one:")
        name = dataDictionary.get("Name", text)
        answer = dataDictionary.get("Answer", None)
        title = dataDictionary.get("Title", "Popup") 

        width = self.canvas.width
        self.question = ComboBox(localFrame, popupOptions, standardFormat, 
                          text=text, name=name, answer=answer, title=title, maxwidth=width) 

    """Automatically format a form based on data (from a JSON file).
    #    Count how many groups are needed for column data.  The data's rows are lists of column data,
    #       but the table is layed out in a series of columns, so the data must be converted from a row to groups for each colmun.
    #    PARAMETERS:
    #        data: A dictionary of data from a JSON file
    #        form: The form to be formatted with the data
    #        randomizeAndLimit=None is an override of all data to randomize and limit the number of quiz questions
    #        graphicFolder=None is the folder localion of any graphic    file referenced from the current working directory
    #
    #    The top level elements in the JSON file are:
    #        "Title": "Name on the form"
    #        "TableName": "Name of the table" used in grading
    #        "Headers": ["Header1", "Header2", ...] for the table show up first and do not use data
    #        "Choices": default is 5, the maximum number of choices to choose from (fewer may be available)
    #        "MaxColumn": default is 10001, the maximum number of widgets on a row
    #        "Continuous": default is False, continue placing widgets in a row until maxColumn is reached
    #        "Vertical": default is False, tables list vertically, not horizontally
    #        "PicturePath": default is None, the path to the folder with pictures
    #        "Table": [ [row1], [row2], ... ] describes the layout for each column in the form as a table
    #        "Columns": [ [column1], [column2], ... ] where each is a row of data with elements placed into columns
    #
    #    The "Table" entries are as follows: 
    #        "Row" is a row number and does not draw out of the data
    #        "Frame" is a frame to hold other elements (not implemented)
    #        "Heading" is a formatted label for a heading.  Usually used once before the tabls and columns are diaplayed
    #        "Label" is text that is displayed and does not contain any choices for an answer in conjunction with a combo box
    #        "Combo" is a combobox for choosing from possible answers
    #        "Picture" is a picture displayed rather than text used in conjunction with a combo box
    #        "Group" allows the data to be placed in a column of data to be accessed as needed, not displayed
    #        "Criteria" allows the data to be placed in a column of data to be accessed as needed, not displayed
    #        Colors for "fg" and "bg" or other Tkinter parameters in pairs can follow the preceeding parameters for 
    #            formatting if they are displayable, however, Comboboxes may not format as expected 
    #
    #    The "Combo" popup elements are "COMBO", question name (used in grading), width of column, and:
    #        "UNIQUE" if only unique values are to be used in the possible answers
    #        "criteria" followed by the column is to be used to find matching criteria in other columns for unique answers
    #        "group" followed by a column is to be used to find matching groups in the group column for unique answers
    #        "choose" multiple choice values from the line of data are used as possible unique answers with the answer listed first
    #        "ORDERED" as the second item in a "choose" list will keep the order of the choices if the answer is in the list
    #        Colors for "fg" and "bg" or other Tkinter parameters in pairs can follow the preceeding parameters for 
    #            formatting, however, Comboboxes may not format as expected 
    """      
class TableQuestionClass(): 
    
    standardFont = ("TKDefaultFont", 12)
    frameFormat = dict( sticky="full", relief=tk.SOLID, borderwidth=1, font=(standardFont[0], standardFont[1], 'bold italic'), pady=5)
    standardFormat = dict( sticky="fullwidth", borderwidth=0, background='white', font=standardFont )
    popupFormat = dict( sticky="fullwidth", background='white', font=standardFont )
    headerTitleFormat = dict( sticky="fullwidth", borderwidth=0, background='white', font=(standardFont[0], standardFont[1], 'italic underline') )
    columnTitleFormat = dict( sticky="fullwidth", borderwidth=0, background='white', font=(standardFont[0], standardFont[1], 'italic') )
    labelFormatDictionary = dict(sticky=tk.LEFT, justify=tk.LEFT, borderwidth=0, background="White", font=standardFont )
    pictureFormatDictionary = dict(sticky=tk.TOP, relief=tk.GROOVE, justify=tk.LEFT, pady=(0,10) )
    headingFormatDictionary = dict( sticky="fullwidth", bg="LightGray", relief="solid", borderwidth=1 )
    headingDictionary = dict( bg="LightGray", sticky="fullwidth", relief="solid", borderwidth=1 )
    labelDictionary = dict(sticky=tk.LEFT, justify=tk.LEFT, borderwidth=0, background="White", font=standardFont )
    
    def __init__(self, canvas, data, questionArea, localFrame, rows, **kwargs):
        
        # Save parameters
        self.canvas = canvas
        self.questionArea = questionArea
        self.data = data
        self.tableOriginalForm = localFrame
        self.tableRows = rows
        self.tableFormatting = kwargs
        
        # Global values
        self.tableColumn = 0
        self.tableRow = 0
        self.tableImages = []
        self.tableModel = None
        
        # Set up the major variables based on values from the JSON file/dictionary
        self.practice = data.get("Practice", False)
        self.tableChoices = data.get("Choices", 5) # How many possible answers to choose from
        self.tableName = data.get("TableName", "Unknown") # Used when grading to identify a missing answer
        self.continuous = data.get("Continuous", False) # Continue placing widgets in a row until maxColumn is reached
        self.vertical = data.get("Vertical", False) # Tables list vertically, not horizontally
        self.providedPicturePath = os.getcwd()
        if ( quiz := questionArea.data.getResource('quiz')):
            self.providedPicturePath = quiz.get("Picture Folder", self.providedPicturePath)
        
        # Picture and layout settings
        self.maxWidth = self.tableFormatting.pop("maxWidth",None)
        self.maxHeight = self.tableFormatting.pop("maxHeight",None)
        self.maxColumn = self.tableFormatting.pop("maxColumn", 6) # Maximum number of widgets on a row
        
        table = data["Table"]
        tableLength = len(table)   
        
        # Use a table grading system
        self.questionArea.replaceSubmitProcessingFunction(self.gradeButtonSelectedTable)
             
        # Check for randomizing columns
        randomizeAndLimit = kwargs.get("randomandlimit", None)
        if randomizeAndLimit is not None:
            size = randomizeAndLimit if isinstance(randomizeAndLimit, int) else len(data["Columns"]) 
            if size <= 0: size=None
            data["Columns"] = self.randomSelectionFrom(data["Columns"], size=size)

        # Collect all column data in groups in the group list
        group = self.collectGroups( data )
        self.tableFrame = Frame( localFrame, pack=True)
        
        # Complete the setup of the form and tables
        self.resetRow()
        self.resetColumn()
        
        # Make and Place any headers on top
        self.headerList = self.makeAnyHeader(data)
        self.canvas.update()

        # Loop for each row of data and format each row's entries/columns according to the table instructions for each group/column
        dataPointCount = len(group[0])
        for dataPoint in range(dataPointCount):
            groupCounter = 0
            entryDepth = 0

            # For each element/column in the row of data, identify what it is, then create it
            for entryNumber in range(tableLength):
                tableEntry = table[entryNumber]
                entrysGroup = group[groupCounter]

                # Each different kind of row element is handled differently
                elementName = tableEntry[0].lower() if isinstance(tableEntry, list) else tableEntry.lower()
                match elementName:

                    # This is a row number and does not draw out of the data
                    case "row":
                        rowNumber = dataPoint+1
                        (row,column) = self.currentCoordinates()
                        self.makeLabel(rowNumber, coord=(row,column)) ##, background=None)

                    case 'heading': # Formatted label for a heading
                        localDictionary = self.setupLabel( tableEntry )
                        for key,value in self.headingDictionary.items():
                            localDictionary[key] = value
                        self.makeLabel(entrysGroup[dataPoint], **localDictionary)

                    # "Label" or ["Label", "fg","Red"]
                    case "label":
                        #  Anything else are pairs for a dictionary (but translate any color into a usable one).
                        localDictionary = self.setupLabel( tableEntry )
                        self.makeLabel(entrysGroup[dataPoint], **localDictionary)

                    # Combobox, ex: ["Combo", "Topo", 80, "Unique", "fg","Cyan"] or ["Combo", "Topo", 80, "Criteria", 3]
                    case "combo":
                        (groupColumn, choicesList, localDictionary) = self.setupValidComboBox(tableEntry, entrysGroup, group, dataPoint)
                        item = self.makeValidTableComboBox(groupColumn, dataPoint, choicesList, tableEntry[1], **localDictionary)
                        item.setName(f"Row {dataPoint+1} {tableEntry[1]}")
                    # Picture displayed rather than text, ex: ["Picture", optional path] (it will expand to fill the column)
                    # The file name is the name of the file in the picture directory.
                    case "picture":
                        (picture, localDictionary) = self.setupComboPicture(tableEntry, entrysGroup, dataPoint) 
                        if self.maxWidth is not None : localDictionary["maxWidth"] = self.maxWidth
                        if self.maxHeight is not None : localDictionary["maxHeight"] = self.maxHeight
                        found = False
                        if os.path.exists(picture):
                            try:
                                    self.makeComboPicture(picture, **localDictionary ) 
                                    found = True
                            except:
                                pass
                        if not found:
                            self.makeComboPicture("No Picture Warning.png", **localDictionary ) 

                # Get the next positions for the group, row and column based on what was displayed last
                if elementName not in ['row','frame']: groupCounter += 1
                if elementName not in ['criteria','group','frame']: self.nextPosition(self.vertical)
                if elementName not in ['criteria','group','frame','row']: entryDepth += 1

            # Possibly reset the row and other things for each new data point
            self.nextDataPointPosition(self.vertical, self.continuous, entryDepth)
        self.canvas.update()

    def randomSelectionFrom(self,  list, including=None, size=None):
            randomList = list.copy()
            random.shuffle(randomList)
            randomListSize = len(randomList)
            newList = []

            if including is None:
                keeper = None
            elif isinstance(including, int):
                if including < 0 or including >= randomListSize:
                    keeper = str(including)
                    newList.append(keeper)
                else:
                    keeper = list[including]
                    newList.append(keeper)
            else:
                keeper = including
                newList.append(keeper)

            length = size if size is not None else randomListSize
            if length > randomListSize: length = randomListSize
            for i in range(randomListSize):
                if len(newList) >= length: break
                item = randomList[i]
                if item != keeper and item not in newList:
                    newList.append(item)
            random.shuffle(newList)
            return newList
        
    def collectUniqueValues(self, answers):
            uniqueValues = []
            for value in answers:
                if value not in uniqueValues:
                    uniqueValues.append(value)
            return uniqueValues
    def setuptables(self, form, model, choices, **dictionary):
            self.tableFrame = form
            self.tableOriginalForm = form
            self.tableModel = model
            self.tableChoices = choices
            self.tableFormatting.clear()
            self.tableFormatting = dictionary.copy()
    def resetForm(self):
            self.tableFrame = self.tableOriginalForm
    def updateForm(self, newForm):
            self.tableForm = newForm
    def setupValidComboBox(self, tableEntry, entrysGroup, group, dataPoint):
            # Arguments: "Combo", abbrev, width, criteria, criteria-group-column, **wargs

            choicesList = []
            localComboDictionary = dict()

            # Setup position for widget
            entryLength = len(tableEntry)
            if entryLength >= 3:
                width = tableEntry[2]
                (row,column) = self.currentCoordinates()
                localComboDictionary = {"coord":(row,column), "width":width}

                # Use all remaining parameters in the table entry 
                if entryLength > 3:
                    first = 3
                    keyword = tableEntry[first].lower()

                    #"""Criteria uses another column in the group to find a match in columns 1 & 2 for specific matching criteria.
                    # Criteria can be text, a number representing the start of Column range from that column to the number of choices,
                    # empty string meaning use all values in columns 1 & 2, or missing entirely which defaults to an empty string.
                    # After the 'Criteria' keyword is used then next element must be the zero-based column to use for the criteria.
                    # "Group" is similar to criteria except the group colummn contains the specific matching criteria or the
                    # column number holding the matching criteria."""

                    # If unique, collect all unique values from the possible answers.
                    if keyword == "unique":
                        choicesList = self.collectUniqueValues(entrysGroup)
                        first += 1

                    elif keyword == "choose" and entryLength >= 5:
                        first += 1
                        localComboDictionary['width'] = int(tableEntry[first])
                        first += 1
                        stringOfChoices = entrysGroup[dataPoint]
                        choicesList = stringOfChoices.split(',')
                        entrysGroup[dataPoint] = choicesList[0] # First element is the correct choice, change element in choicesList
                        if choicesList[1].lower() == "ordered":
                            del choicesList[0]
                            del choicesList[0]
                        else:
                            random.shuffle(choicesList) # Shuffle the choices

                    # For "criteria", find all elements in group columns 1 & 2 that match the criteria and add matching columns to the choices list.
                    elif keyword == "criteria" and entryLength >= 5:
                        first += 1
                        criteriaColumnNumber = tableEntry[first]
                        first += 1

                        # Insure data is valid to look for criteria
                        groupLength = len(entrysGroup)
                        if 0 <= dataPoint < groupLength:
                            criteriaColumnLength = len(group[criteriaColumnNumber] )
                            if 0 < criteriaColumnLength <= groupLength:
                                criteria = group[criteriaColumnNumber][dataPoint]

                                # Integer criteria is a range of columns to use
                                if isinstance(criteria, int):
                                    limit = min(criteria+self.tableChoices, len(entrysGroup))
                                    for index in range(criteria, limit):
                                        choicesList.append(entrysGroup[index])
                                    choicesList = self.collectUniqueValues(choicesList)

                                # Empty criteria means use all values in columns 1 & 2
                                elif len(criteria) == 0:
                                    choicesList = self.collectUniqueValues(entrysGroup)

                                # Otherwise, use text criteria to find any matching values in columns 1 & 2
                                else:
                                    for eachElement in range(0, groupLength):
                                        if criteria in group[0][eachElement]:
                                            choicesList.append(entrysGroup[eachElement])
                                            continue
                                        if criteria in group[1][eachElement]:
                                            choicesList.append(entrysGroup[eachElement])
                                    choicesList = self.collectUniqueValues(choicesList)

                    # For "group", find all elements in the group column that match the group-criteria and add matching columns to the choices list.
                    # Group elements can be a string, a number or string of a number representing the start of Column range from that column to the 
                    # number of choices, empty string meaning use all values in the group column, or missing entirely which defaults to an empty string.
                    elif keyword == "group" and entryLength >= 5:
                        first += 1
                        groupColumnNumber = tableEntry[first]
                        first += 1

                        # Insure data is valid to look for group-criteria
                        groupLength = len(entrysGroup)
                        if 0 <= dataPoint < groupLength:
                            groupColumnLength = len(group[groupColumnNumber] )
                            if 0 < groupColumnLength <= groupLength:
                                groupCriteria = group[groupColumnNumber][dataPoint]
                                if isinstance(groupCriteria, int):
                                    try:
                                        groupCriteriaColumn = int(groupCriteria)
                                        if 0 <= groupCriteriaColumn < groupColumnNumber:
                                            groupCriteria = group[groupCriteriaColumn][dataPoint]
                                        else:
                                            groupCriteria = ""
                                    except:
                                        groupCriteria = ""
                                elif isinstance(groupCriteria, str):
                                    if groupCriteria.isnumeric():
                                        groupCriteriaColumn = int(groupCriteria)
                                        if 0 <= groupCriteriaColumn < groupColumnNumber:
                                            groupCriteria = group[groupCriteriaColumn][dataPoint]

                                # Otherwise, use the group-criteria to find any matching values in the group column
                                if len(groupCriteria) > 0:
                                    for eachElement in range(0, groupLength):
                                        currentGroup = group[groupColumnNumber][eachElement]
                                        if groupCriteria == currentGroup:
                                            choicesList.append(entrysGroup[eachElement]) ###
                                    choicesList = self.collectUniqueValues(choicesList)
                                else:
                                    choicesList = self.collectUniqueValues(entrysGroup)

                        # Insure there are enough choices to use up to 100 tries
                        count = 0
                        while len(choicesList) < self.tableChoices:
                            newListElement = self.randomSelectionFrom(group[groupColumnNumber], size=1)
                            if isinstance(newListElement, list): newListElement = newListElement[0]
                            if isinstance(newListElement, str):
                                if newListElement.isnumeric():
                                    newListElement = int(newListElement)
                            if isinstance(newListElement, int):
                                if newListElement < 0 or newListElement >= len(group[groupColumnNumber]): continue
                                newListElement = group[groupColumnNumber][newListElement]
                            if newListElement not in choicesList and len(newListElement) > 0:
                                choicesList.append(newListElement)
                            count += 1
                            if count > 100: break

                    #  Anything else are pairs to be added to the dictionary (but translate any color into a usable color).
                    for pair in range(first, entryLength, 2):
                        ##if pair+1 >= entryLength: break
                        key = tableEntry[pair]
                        value = tableEntry[pair+1]
                        if key in ["fg","bg"]:
                            value = self.canvas.colors.get(value, value)
                        localComboDictionary[key]=value

            return (entrysGroup, choicesList, localComboDictionary)
    def makeValidTableComboBox(self, entrysGroup, id, possibilities, abbrev, **dictionary ):
            #standardFormat = dict( sticky="fullwidth", borderwidth=0, background="White", font=standardFont )
            formatting = self.popupFormat.copy() ##comboFormat.copy()
            formatting["justify"] = tk.LEFT
            formatting["correct"] = entrysGroup[id]
            formatting["name"] = f'{abbrev} {id} {self.tableModel}'
            formatting.update(dictionary)
            # entrysGroup[id] not in possibilities:
            selections = self.randomSelectionFrom(possibilities, including=entrysGroup[id], size=self.tableChoices)
            if self.practice:
                item = ValidTableComboBox(self.tableFrame, selections, **formatting ) 
            else:
                item = TableComboBox(self.tableFrame, selections, **formatting ) 
            return item
    def setupLabel(self, labelEntry ):
            (row,column) = self.currentCoordinates()
            localLabelDictionary = {"coord":(row,column)}
            localLabelDictionary.update(self.labelFormatDictionary)

            if isinstance(labelEntry, list):
                for pair in range(1, len(labelEntry), 2):
                    key = labelEntry[pair]
                    value = labelEntry[pair+1]
                    if key in ["fg","bg"]:
                        value = self.canvas.colors.get(value, value)
                    localLabelDictionary[key]=value
            return localLabelDictionary
    def makeLabel(self, text, **dictionary ): 
            formatting = self.columnTitleFormat.copy()
            formatting["justify"] = tk.CENTER
            formatting.update(self.tableFormatting)
            for key,value in dictionary.items():
                formatting[key] = value
            useText = text if isinstance(text,str) else str(text)
            item = Label(self.tableFrame, text=useText, **formatting) ## pady=3, removed
            return item

    def setupComboPicture(self, tableEntry, entrysGroup, dataPoint ): 
            elementIsList = isinstance(tableEntry, list)
            if elementIsList and len(tableEntry) >= 2:
                picturePath = tableEntry[1]
            elif self.providedPicturePath is not None:
                picturePath = self.providedPicturePath
            else:
                picturePath = os.getcwd()

            fileName = entrysGroup[dataPoint]
            if fileName.find(".") < 0: fileName += ".gif"
            picture = os.path.join(picturePath, fileName )

            (row,column) = self.currentCoordinates()
            localPictureDictionary = {"coord":(row,column)}
            return (picture, localPictureDictionary)

    def makeComboPicture(self,  picture, **dictionary ):  # Needs to include the coord() parameter
        pilImage = PILImage.open(picture)
        
        # Check for changing the width or height
        maxWidth = dictionary.pop("maxWidth",0)
        maxHeight = dictionary.pop("maxHeight",0)
        if maxWidth > 0 or maxHeight > 0:
            width = min(pilImage.width, maxWidth)
            height = min(pilImage.height, maxHeight)
            if width > 0:
                size = width/pilImage.width
            else:
                size = height/pilImage.height
            newWidth = int(pilImage.width * size)
            newHeight = int(pilImage.height * size)
            pilImage = pilImage.resize([newWidth,newHeight])
            
        photoImage = ImageTk.PhotoImage(pilImage)
        self.tableImages.append(photoImage) # They must be stored or the picture disappears
        localPictureDictionary = self.pictureFormatDictionary.copy()
        for key,value in dictionary.items():
            localPictureDictionary[key] = value
        item = Label(self.tableFrame, image=photoImage, **localPictureDictionary) 
        
    def setupPicture(self, tableEntry, entrysGroup, dataPoint ): 
            elementIsList = isinstance(tableEntry, list)
            if elementIsList and len(tableEntry) >= 2:
                picturePath = tableEntry[1]
            elif self.providedPicturePath is not None:
                picturePath = self.providedPicturePath
            else:
                picturePath = os.getcwd()

            fileName = entrysGroup[dataPoint] + ".gif"
            picture = os.path.join(picturePath, fileName )

            (row,column) = self.currentCoordinates()
            localPictureDictionary = {"coord":(row,column)}
            return (picture, localPictureDictionary)
        
    def makeAnyHeader(self,  data ): 
            headerList = []
            headers = data.get("Headers", None)
            if headers is not None:
                for headerColumn in range(len(headers)):
                    (row,column) = self.currentCoordinates()
                    formatting = dict(coord=(row,headerColumn) )
                    formatting.update(self.headerTitleFormat)
                    formatting["justify"] = tk.CENTER
                    formatting.update(self.tableFormatting)
                    text = data["Headers"][headerColumn]
                    useText = text if isinstance(text,str) else str(text)
                    item = Label(self.tableFrame, text=useText, **formatting)
                    headerList.append(item)
                row = self.nextRow()
            return headerList
    
    # These use the table row and column to determine where to place the next widget
    def currentCoordinates(self):
            return (self.tableRow, self.tableColumn)
    def resetRow(self, start=0):
            self.tableRow = start
            return self.tableRow
    def nextRow(self, increment=1):
            self.tableRow += increment
            return self.tableRow
    def resetColumn(self, start=0):
            self.tableColumn = start
            return self.tableColumn
    def checkForExceededColumn(self):
            exceeeded = self.tableColumn + 1 > self.maxColumn
            if exceeeded:
                self.resetColumn()
                self.nextRow()
            return exceeeded
    def nextColumn(self, increment=1):
            self.tableColumn += increment
            return self.tableColumn
    def nextPosition(self, vertical):
            if vertical:
                row = self.nextRow()
                column = self.tableColumn
            else:
                row = self.tableRow
                column = self.nextColumn()
                if self.checkForExceededColumn():
                    (row, column) = self.currentCoordinates()
            return (row, column)
    def nextDataPointPosition(self, vertical, continuous, entryDepth):
            if vertical:
                column = self.nextColumn() 
                if self.checkForExceededColumn():
                    (row, column) = self.currentCoordinates()
                elif continuous:
                    row = self.nextRow(-entryDepth)
                else:
                    row = self.tableRow
            else:
                if continuous:
                    row = self.tableRow
                    column = self.tableColumn
                else:
                    row = self.nextRow()
                    column = self.resetColumn()
            return (row, column)
    def collectGroups(self,  data ):
            """First count how many items in the table have columns in the Column data,
            insure criteria columns have missing criteria filled in with blanks,
            then place each column into its own row in the group list where it is accessed individually"""
            countOfGroups = 0
            table = data["Table"]
            tableLength = len(table)
            for index in range(tableLength):
                eachEntry = table[index]
                element = eachEntry[0] if isinstance(eachEntry, list) else eachEntry
                if element.lower() not in ["row","frame"]: # But keep criteria
                    countOfGroups += 1

            # Insure criteria columns have missing criteria filled in with blanks
            group = []
            minimumColumnLength = len(data['Columns'][0])
            for index in range(len(data['Columns'])):
                eachColumn = data['Columns'][index]
                length = len(eachColumn)
                while len(eachColumn) < minimumColumnLength:
                    eachColumn.append("")

            # Place each column into its own row in the group list where it is accessed individually
            for index in range(countOfGroups  ):
                # Transfer each column into its own row
                eachList = list(map(lambda x: x[index], data['Columns']))
                group.append(eachList)
            return group
            
    def gradeButtonSelectedTable(self, window, statusBar):
    #    """Called when grade button is clicked. Temporary replacement for the standard funtion (same name)"""
        self.questionArea.resetGradeButton()
        success = True # Always True, rights and wrongs are both scored (in that order)
        totalNumberOfWidgets = len(window.widgets)
        numberOfValidWidgets = 0
        numberOfInvalidWidgets = 0
        if totalNumberOfWidgets == 0:
            statusBar.set( f"There are no questions to answer")
        else:
            invalidValues = window.validateVisibleActivatedWidgets()
            numberOfInvalidWidgets = len(invalidValues)
            if numberOfInvalidWidgets == 0:
                statusBar.set( f"All popus were answered correctly!")
            else:
                numberOfValidWidgets = totalNumberOfWidgets - numberOfInvalidWidgets
                warning = "incorrect answer" if numberOfInvalidWidgets == 1 else "incorrect answers"
                useComma = False
                if isinstance(invalidValues, list):
                    for widget in invalidValues:
                        names = widget.getTitle()
                        if isinstance(names, str):
                            if useComma:
                                warning += f", {names}"
                            else:
                                warning = f"{names}"
                            useComma = True
                        else:
                            warning ="Unknown error:"
                elif isinstance(invalidValues, dict):
                    for key,widget in invalidValues.items():
                        if isinstance(key, str):
                            if useComma:
                                warning += f", {key}"
                            else:
                                warning = f"{key}"
                            useComma = True
                        else:
                            warning ="Unknown error:"

                missing = "part" if numberOfInvalidWidgets == 1 else "parts"
                statusBar.set( f" Missed {numberOfInvalidWidgets} {missing} of the {totalNumberOfWidgets} popups with {warning}")
        
        self.canvas.resetDimensions()        
        cleanup = True
        return success, numberOfValidWidgets, numberOfInvalidWidgets, cleanup
    def getDimensions(self):
        width = self.tableOriginalForm.widget.cget('width')
        height = self.tableOriginalForm.widget.cget('height')
        return width, height  

"""Provide review of Python coding.
    #On NEXT: Display the next problem in the selected category.
    #        a) Click selects the button for the next (in category) item.
    #        b) Control-Click to refresh current problem from its file.
    #        b) Shift-Control-Click to refresh current problem but keep the current edited code
    #On SUBMIT: Process the code in the edit box and provide feedback.
    #On QUIT: Exit the program.
    #Problems are stored in the Problems or Solutions folders as .txt files with JSON data at the top and code below.
    #Problems presented in alphabetical order or randomized within categories. Answered problems are
    #marked and not reused. Optional dictionary/Json keywords are provided defaults.
    #Code is in a safe state so the computer is not affected. Unsafe code is marked with a Yellow background,
    #but can be run without any checking. When unsafe code is run, stdout & stderr is sent to the response window.
    #Set the development variable to True to enable Control-Click and Shift-Control-Click features.
    #Set the randomIndexActivated variable to True to randomize problem selection within a category.
    #
    ## Question Format:
    #{
    #"Name": "Problem #1",
    #"File": "Problem_01.txt",
    #"Title": "What are the Possibilities?",
    #"Type": "CodeCheck",
    #"Language","Python",
    #"Category": "Math",
    #"Reward": "Gold",
    #"Penalty": "Gold",
    #"Imports": "math, random, datetime", # Can also be an array
    #"Required":["answer"],
    #"PostReGex":['.* answer .*=','.* return .*answer"],
    #"Exclude":[],
    #"Parameters":[5000,99],
    #"Dictionary":{}, # Not implementes at this time
    #"Variables":"answer",
    #"Return":15,
    #"UnsafeCode":false,
    #"Instructions": "Set the variable called ~answer~ equal to the provided sum function (near line 6) and return it."
    ## For instructions, quotes seem to get lost so use a tilde and it gets replace by a single quote.
    #}
    #def myFunction(a,b):
    #    z = math.sqrt(7000)
    #    z = int(3) + float(a + z) 
    #    x = max(7,min(2,9000 + b))
    #    y = ((b * x**3)/(x-b))/a
    #    a = sum([1,2,3,4,5])
    #    c = True
    #    c = "abcdefg"
    #    b = c[2:-1]
    #    return b
    """
class CodeEditorClass():
    """ Question based on entering code. Currently Python and SQL supported.
    The solution is stored in a .txt file with a combination of JSON and text features. A correct answer
    must exactly match the solution in the .txt file. Python code is checkd to protect the computer
    from malicious code. SQL code is not checked to protect the server.
    """
    
    CATEGORY=0;DICTIONARY=1;PROBLEM_CODE=2;USED=3 # Order of elements in a problem list
    """These are the indicies of a list for each question. They are the category of the code. This can be any string.
    Code can be access sequentially or by category. The dictionary is the JSON portion of the .txt files which
    defines the questioning or other features.  The problem's code to correct is next. USED is True/Falae on 
    the question being used and answered. The correct answer is found in the dictionary."""
    
    def __init__(self, questionArea, dataDictionary, frame, rows):
        self.questionArea = questionArea
        self.data = self.questionArea.data
        self.canvas = questionArea.canvas
        self.currentProblem = dataDictionary 
        self.frame = frame 
        
        self.safeNodeVisitor = None # Class to check Python code
        
        # Language specific values
        language = self.currentProblem.get("Language", "Python")
        self.language = language.lower().strip().replace(" ","")
        if self.language == "python":
            self.currentProblem["Required Imports"] = "math, random, datetime"
        else:
            self.currentProblem["Required Imports"] = ""
            
        # Various parts of the question
        instructions = self.currentProblem.get("Instructions", "")
        text = self.currentProblem.get("Text", "Edit the code:")
        name = self.currentProblem.get("Name", text)
        answer = self.currentProblem.get("Answer", "")
        standardFont = ("TKDefaultFont", 14)

        # Major variables
        # allProblemsList       List of all problems [category,dictionary,problem, Used]
        # comboSelectionList    Subset list of categories for the combo box extracted from the self.categoryList 
        # currentProblemsList   List of current problems based on the category selected (subset of allProblemsList)
        # currentIndex          Index integer into the self.currentProblems tuple list
        # currentProblem        The current problem from [category,dictionary,problem,used] currentProblemsList
        # currentDictionary     The current dictionary from the currentProblemsList
        
        # Program mode variables
        #self.development = True # Set to allow certain development options
        # Problem location
        # if (quiz := self.questionArea.data.getResource("quiz")):
        #     self.problemFolder = quiz.get("Problem Folder","Problems")
        # else:
        #     self.problemFolder = "Problems"
        # self.problemPath = pathlib.Path(os.path.join(os.getcwd(), self.problemFolder))
        self.randomIndexActivated = False # problems in name order or random selection
        self.databaseInfo = None # Used with SQL
        
        # Initialize major variables
        self.mainTitleText = "Code Review"
        self.runSafeCode = True # Tracks what kind of code to run - safe or unsafe
        self.currentProblemsList = []
        self.comboSelectionList = []
        self.currentCategory = "" 
        self.currentIndex = None 
        self.currentDictionary = {}

        # Coordinates for the main components of the GUI
        y = 126
        numberCoordinates = [y+50, 26, 27]
        instructionCoordinates = [540, y, 890, y+430]
        responseCoordinates = [10, y+440, 890, y+570]
        editBoxCoordiantes = [30, y, 530, y+430]

        # Line numbers on the left side 
        start = numberCoordinates[0]
        number = 1
        importing = self.currentDictionary.get("Imports", None) # Imports are not shown but affect line numbers
        if isinstance(importing, str) and len(importing) > 0:
            number = 2
        elif isinstance(importing, list):
            number += len(importing)

        # Draw the line numbers
        for i in range(number,number + 15):
            simpleObject = Text(self.canvas, numberCoordinates[2], start, text=str(i), anchor="e", color="Black", font=standardFont)
            self.questionArea.addEditingElement(simpleObject)
            start += numberCoordinates[1]
        
        self.instructions = CanvasTextBox(self.canvas, *instructionCoordinates, text=instructions, label="Instructions")
        self.questionArea.addEditingElement( self.instructions)
        
        self.response = PrettyTextBox(self.canvas, *responseCoordinates, 
                                      label="Result of Editing (press Answer Button)", text="", font=("Consolas", 12))
        self.questionArea.addEditingElement( self.response)
        
        self.editBox = CanvasTextBox(self.canvas, *editBoxCoordiantes, readonly=False, text="",
                                     label="Edit Code in this Box", font=standardFont, scrolling=False)
        self.questionArea.addEditingElement( self.editBox)
        
        # Replace with our Submit code 
        self.displayCurrentProblem()
        self.questionArea.replaceSubmitProcessingFunction(self.gradeButtonSelectedCodeEditor)
    
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
            self.data.logError(f"Error: Unable to access {path} data which contains the JSON and code!")
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
                element = line.split(":")
                if len(element) == 2 and len(element[0]) > 0 and len(element[1]) > 0:
                    key = element[0].strip().replace('"','').replace("'","")
                    value = element[1].strip()
                    if value[-1] == ",": value = value[:-1]
                    firstLetter = value[0]
                    if firstLetter in ['[','{','(']:
                        if firstLetter == "[":
                            collection = []
                        elif firstLetter == "(":
                            collection = ()
                        else:
                            collection = {}
                        if len(value) > 2:
                            listing = value[1:-1].split(",")
                            for item in listing:
                                eachItem = self.convertFromString(item)
                                if firstLetter == "[":
                                    collection.append(eachItem)
                                elif firstLetter == "(":
                                    collection.append(eachItem)
                                else:
                                    dictionaryList = eachItem.split(":")
                                    if len(dictionaryList) == 2:
                                        collection[dictionaryList[0]] = dictionaryList[1]
                        dictionary[key] = collection        
                    else:
                        value = element[1].strip().replace('"','').replace("'",'')
                        if value[-1] == ",": value = value[:-1]
                        dictionary[key] = self.convertFromString(value)
                        
            # Get the name and filename and set them
            parts = file.split(".")
            namePart = parts[0]
            parts = namePart.split("_")
            number = parts[1]
            if number[0] == '0': number = number[1:]
            finalName = parts[0] + " #" + number
            dictionary.setdefault("Name", finalName)
            dictionary.setdefault("File", file)
            
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

    def convertFromSqlString(self, value):
        """Convert a SQL string so it can be checked against the expected return value. 
        This is similar to convertFromString but with some differences for SQL strings."""

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
            
            # Still unchanged, must be a real string, check to replace unneeded slashes, spaces, and tabs
            else:
                """ Replace any double slash \\ with / for comparisons, remove any \n ending"""
                length = len(string) - 1
                previousSpace = False
                returnValue = ""
                for count,letter in enumerate(string):
                    if letter == "\\":
                        returnValue += "/"
                        previousSpace = False
                    elif letter == '\n':
                        if count < length: returnValue += "/n"
                        previousSpace = False
                    elif letter == "\t":
                        if count < length: 
                            if previousSpace:
                                returnValue = returnValue[:-1]
                            returnValue += ","
                        previousSpace = False
                    elif letter == " ":
                        if not previousSpace:
                            returnValue += " "
                            previousSpace = True
                    else:
                        returnValue += letter
                        previousSpace = False

        return returnValue

    def removeTrailingZeroes(self, value):
        """Remove trailing zeroes if found in the string"""
        if not type(value) == str: return value
        returnValue = ""
        decimalInProgress = False
        savedText = ""
        for count,letter in enumerate(value):
            if letter == ".":
                decimalInProgress = True
                savedText += letter
            elif decimalInProgress:
                if letter == "0":
                    savedText += letter
                elif letter.isnumeric():
                    decimalInProgress = False
                    returnValue += savedText + letter
                    savedText = ""
                else:
                    decimalInProgress = False
                    returnValue += letter
                    savedText = ""
            else:
                decimalInProgress = False
                returnValue += letter
        
        return returnValue

    def checkForUnsafeCode(self, forceSafe=None):
        """Check for new/old unsafe code or returning to safe code"""
        if forceSafe is None:
            newUnsafeCode = self.currentDictionary.get("UnsafeCode", False)
        else:
            newUnsafeCode = not not forceSafe
        if newUnsafeCode:
            if self.runSafeCode:
                self.runSafeCode = False
                backgroundColor = "DarkGreen" if self.runSafeCode else "Yellow"
                textColor = "White" if self.runSafeCode else "Black"
                self.canvas.setBackground(backgroundColor)
                self.mainTitle.color = textColor
                self.mainTitle.text = self.mainTitleText + " - UNSAFE CODE"
                self.title.color = textColor
                self.canvas.update()
        elif not self.runSafeCode:
                self.runSafeCode = True
                backgroundColor = "DarkGreen" if self.runSafeCode else "Yellow"
                textColor = "White" if self.runSafeCode else "Black"
                self.canvas.setBackground(backgroundColor)
                self.mainTitle.color = textColor
                self.mainTitle.text = self.mainTitleText
                self.title.color = textColor
                self.canvas.update()

    def displayCurrentProblem(self):
        if self.currentProblem is None:
            self.editBox.set("No more problems available in this category. Please select a different category or exit.")
            self.response.clear()
            self.setInstructions("No instructions available.")
        else:
            currentcodecheck = self.currentProblem.get("Code", "")
            self.editBox.set(currentcodecheck)   
            self.response.clear()  
            extraText = self.currentProblem.get("Title", None)
            if extraText is not None:
                self.questionArea.titleLabel.text = self.mainTitleText + " - " + extraText
            extraText = self.currentProblem.get("Instructions", "Correct any errors")
            self.setInstructions(extraText, language=self.language)
            
            # Any preprocessing
            language = self.currentProblem.get("Language", "python").lower().strip().replace(" ","")
            match language:
                case "python": 
                    self.checkForUnsafeCode()
                case _: pass
        self.canvas.update()

    def preCheckPython(self, dictionary, codeLines):
        """ Check for required and forbidden keywords in the code."""
        succeed = True
        allLines = codeLines.splitlines()

        # Check for missing keywords that are required
        requiredKeywords = dictionary.get("Required", [])
        for keyword in requiredKeywords:
            found = False
            for line in allLines:
                findInWord = line.find(keyword)
                if findInWord >= 0: 
                    found = True
                    break
            succeed = succeed and found
            if not succeed:
                self.response.add(f"Required keyword not used: {keyword}.\n")
                break
        
        # When "os" is required, there are more forbidden words even if required (to use those, use unsafe code)
        if succeed and "os" in requiredKeywords:
            forbidden_keywords = ['popen', 'ftruncate', 'mkdir', 'makedirs', 'remove', 'removedirs',
                                  'rmdir', 'chdir', 'truncate', 'system']
            for keyword in forbidden_keywords:
                for line in allLines:
                    finding = line.find(keyword)
                    if finding >= 0:
                        self.response.add(f"Forbidden os keyword used with os import: {keyword}.\n")
                        succeed = False  
                        break
                
        # When "sys" is required, there are more forbidden words even if required (to use those, use unsafe code)
        if succeed and "sys" in requiredKeywords:
            forbidden_keywords = ['system', 'exit', 'deactivate_stack_trampoline', 'executable' ]
            for keyword in forbidden_keywords:
                for line in allLines:
                    finding = line.find(keyword)
                    if finding >= 0:
                        self.response.add(f"Forbidden sys keyword used with os import: {keyword}.\n")
                        succeed = False  
                        break


        # Check for standard forbidden keywords even if required (to use those, use unsafe code)
        if succeed:
            forbidden_keywords = ['import', 'exec', 'eval', 'from', 'exit', ';', "#"]
            for keyword in forbidden_keywords:
                for line in allLines:
                    finding = line.find(keyword)
                    if finding >= 0:
                        self.response.add(f"Forbidden keyword used: {keyword}.\n")
                        succeed = False  
                        break  
        # Check for excluded keywords that are not specifically required
        if succeed:
            excludedKeywords = dictionary.get("Exclude", [])
            for keyword in excludedKeywords:
                for line in allLines:
                    finding = line.find(keyword)
                    if finding >= 0:
                        if keyword not in requiredKeywords:
                            self.response.add(f"Excluded keyword used: {keyword}.\n")
                            succeed = False  
                        break                      
        return succeed

    def preCheckPythonTheUnsafe(self, dictionary, codeLines):
        """ Check for required and forbidden keywords in the code."""
        succeed = True
        allLines = codeLines.splitlines()

        # Check for missing keywords that are required
        requiredKeywords = dictionary.get("Required", [])
        for keyword in requiredKeywords:
            found = False
            for line in allLines:
                findInWord = line.find(keyword)
                if findInWord >= 0: 
                    found = True
                    break
            succeed = succeed and found
            if not succeed:
                self.response.add(f"Required keyword not used: {keyword}.\n")
                break
            
        # When "os" is required, there are more forbidden words, but as it is unsafe, allow if required
        if succeed and "os" in requiredKeywords:
            forbidden_keywords = ['popen', 'ftruncate', 'mkdir', 'makedirs', 'remove', 'removedirs',
                                  'rmdir', 'chdir', 'truncate', 'system']
            for keyword in forbidden_keywords:
                for line in allLines:
                    finding = line.find(keyword)
                    if finding >= 0:
                        if keyword not in requiredKeywords:
                            self.response.add(f"Forbidden os keyword used with os import: {keyword}.\n")
                            succeed = False  
                            break
                        
        # When "sys" is required, there are more forbidden words, but as it is unsafe, allow if required
        if succeed and "sys" in requiredKeywords:
            forbidden_keywords = ['system', 'exit', 'deactivate_stack_trampoline', 'executable' ]
            for keyword in forbidden_keywords:
                for line in allLines:
                    finding = line.find(keyword)
                    if finding >= 0:
                        if keyword not in requiredKeywords:
                            self.response.add(f"Forbidden sys keyword used with os import: {keyword}.\n")
                            succeed = False  
                            break


        # Check for standard forbidden keywords, but as it is unsafe, allow if required
        if succeed:
            forbidden_keywords = ['import', 'exec', 'eval', 'from', 'exit', ';', "#"]
            for keyword in forbidden_keywords:
                for line in allLines:
                    finding = line.find(keyword)
                    if finding >= 0:
                        if keyword not in requiredKeywords:
                            self.response.add(f"Forbidden keyword used: {keyword}.\n")
                            succeed = False  
                            break  

        # Check for excluded keywords that are not specifically required
        if succeed:
            excludedKeywords = dictionary.get("Exclude", [])
            for keyword in excludedKeywords:
                for line in allLines:
                    finding = line.find(keyword)
                    if finding >= 0:
                        if keyword not in requiredKeywords:
                            self.response.add(f"Excluded keyword used: {keyword}.\n")
                            succeed = False  
                        break                      
        return succeed

    def checkTheAnswer(self, answer, correctAnswer):
        """Check if the answer is correct. Answers can be many different types"""
        response = True
        if type(correctAnswer) == list:
            if type(answer) != list or len(answer) != len(correctAnswer):
                response = False
            else:
                for i in range(len(correctAnswer)):
                    checkAnswer = self.convertFromString(answer[i])
                    unchangedAnswer = answer[i]
                    checkCorrectAnswer = correctAnswer[i]
                    if checkAnswer != checkCorrectAnswer and unchangedAnswer != unchangedAnswer:
                        response = False
                        break
        elif type(correctAnswer) == dict:
            if type(answer) != dict or len(answer) != len(correctAnswer):
                response = False
            else:
                for key,value in answer.items():
                    checkAnswer = self.convertFromString(value)
                    unchangedAnswer = value
                    checkCorrectAnswer = correctAnswer.get(key,None)
                    if checkAnswer != checkCorrectAnswer and unchangedAnswer != unchangedAnswer:
                        response = False
                        break
        elif type(correctAnswer) == tuple:
            if type(answer) != tuple or len(answer) != len(correctAnswer):
                response = False
            else:
                for i in range(len(correctAnswer)):
                    checkAnswer = self.convertFromString(answer[i])
                    unchangedAnswer = answer[i]
                    checkCorrectAnswer = correctAnswer[i]
                    if checkAnswer != checkCorrectAnswer and unchangedAnswer != unchangedAnswer:
                        response = False
                        break
        else:
            checkAnswer = self.convertFromSqlString(answer)
            correctedAnswer = self.convertFromSqlString(correctAnswer)
            response = (checkAnswer == correctedAnswer) 
            if not response:
                checkAnswer = self.removeTrailingZeroes(checkAnswer)
                response = (checkAnswer == correctedAnswer) 
        return response

    def followedInstructionsCheck(self, code):
        """ Check for any ReGex patterns that must be matched in the code based on on instructions."""
        response = True
        # Use any ReGex provided if we are still good with an answer
        postReGexList = self.currentDictionary.get("PostReGex", [])
        for pattern in postReGexList:
            try:
                result = re.match(pattern, code, re.DOTALL)
            except:
                self.data.error.add(f"Error in ReGex pattern for instructions: {pattern}.\n")
                result = None

            if result is None: 
                response = False
                break
        return response

    def getSelectionsFromFolder(self, folderPath):
        """Bring in all problems from the folder and extract unique categories and all problems."""
        allSelectionList = []
        categorySet = set()
        number = 0
        used = False
        for file in os.listdir(folderPath):
            if file.endswith(".txt"):
                dictionary, code = self.extractProblem(folderPath, file)
                dictionary["Number"] = number
                category = dictionary.get("Category", "Math")
                allSelectionList.append( [category, dictionary, code, used] )
                categorySet.add(category)
                number += 1
        categoryList = list(categorySet)
        categoryList.sort()
        categoryList.insert(0,"Everything")
        return categoryList, allSelectionList
    
    def setInstructions(self, instruction, language=None):
        tryLanguage = None if language is None else language.lower()
        if tryLanguage == "python":
            standardInstructions = "Correct any errors in the code box and press Answer to see if you are correct. You can use variables: a,b,c,x,y,z, and answer. Imports from math, pathlib, and random are setup for you. You may not import any other libraries or use keywords that could harm your computer. Scroll down to see the results and press the Clear Response button to continue.\n\n"
        elif tryLanguage == "sql":
            standardInstructions = "Edit the provided code then select the Answer button to have it checked. Scroll down to see the results and press the Clear Response button to continue.\n\n"
        else:
            standardInstructions = ""
        self.instructions.set(standardInstructions)
        self.instructions.add(self.currentProblem["Name"]+"\n")
        quotedsAdded =instruction.replace("~","'")
        self.instructions.add(quotedsAdded)
            
    def processingSafePython(self, dictionary, blockOfCode):
        """ Process the code in the text box - process it safely"""
        # Pre-check - manual check for forbidden & required keywords
        codeResponse = ""
        correctAnswer = dictionary['Return']
        succeed = len(dictionary) > 0 and len(blockOfCode) > 0
        if succeed:
            succeed =  self.preCheckPython(dictionary, blockOfCode)
            if not succeed: 
                self.response.add("The pre-check failed, some of those keywords are not used.\n")
        else:
            self.response.add("No code or dictionary to process!\n")
            
        # Make the code to be run safely
        if succeed:  
            try:
                # Get any problem imports
                importingSet = set()
                listOfImports = dictionary.get("Imports", None)
                if listOfImports is not None:
                    if type(listOfImports) == str:
                        listOfImports = listOfImports.split(",")
                    for item in listOfImports:
                        importItem = item.strip()
                        if len(importItem) == 0 or importItem.lower == "import": continue
                        importingSet.add(importItem)
                    
                # Add any any required imports
                requiredImportsList = self.currentProblem.get("Required Imports","")
                if len(requiredImportsList) > 0:
                    if type(requiredImportsList) == str:
                        requiredImportsList = requiredImportsList.split(",")
                    for item in requiredImportsList:
                        importItem = item.strip()
                        if len(importItem) == 0 or importItem.lower == "import": continue
                        importingSet.add(importItem)
                    
                # Get remaining lists
                importingList = list(importingSet)
                requiredList = dictionary.get("Required",[] )
                variableList = dictionary.get("Variables",[] )

                # Make a fresh safe node object so past restrictions are not included
                self.safeNodeVisitor = PythonSafeNodeVisitorClass.NodeVisitorClass()
                code = self.safeNodeVisitor.safe_exec(blockOfCode, importingList, requiredList, variableList )
            except Exception as e:
                self.response.add(f"An error occurred during compiling: {e}.\n")
                ##succeed = False

        # Execute the code safely, if successful the myFunction() is available to be called
        if succeed:
            try:
                exec(code, globals()) #, locals()  places myFunction here
            except Exception as e:
                self.response.add(f"An error occurred during exec: {e}.\n")
                succeed = False

        # Call myFunction with parameters if exec() worked
        if succeed:
            parameters = dictionary.get("Parameters", []) # No kwargs at this time
            try:
                codeResponse = myFunction(*parameters) # If exec() worked without an error, myFunction() now exists
            
            except Exception as e:
                self.response.add(f"An error occurred in the function: {e}.\n")
                succeed = False

        # Post-checks - were the instructions followed rgardless of a correct answer
        if succeed:
            succeed = self.followedInstructionsCheck(blockOfCode)
            if not succeed:
                self.response.add(f"Some of the instructions were not followed. For reference, the answer was {codeResponse}.\n")

        # Final answer check for correctness
        if succeed:
            if correctAnswer is None:
                self.response.add("No correct answer was provided to check against, so you are good.\n")
            else:
                succeed = self.checkTheAnswer(codeResponse, correctAnswer)
        return succeed, codeResponse, correctAnswer

    def unsafePythonProcessing(self, dictionary, blockOfCode):
        """ Process the code in the text box without safety"""

        # Pre-check - manual check for forbidden & required keywords
        codeResponse = ""
        correctAnswer = dictionary['Return']
        succeed = len(dictionary) > 0 and len(blockOfCode) > 0
        if succeed:
            succeed =  self.preCheckPythonTheUnsafe(dictionary, blockOfCode)
            if not succeed: 
                self.response.add("The unsafe pre-check failed, missing or included forbidden words.\n")
        else:
            self.response.add("No code or dictionary to process!\n")

        # Clear the response text box to receive stdout & stderr. Reset the standard out and error streams to self.response
        if succeed:
            self.response.clear()
            self.canvas.update()
            sys.stdout = self.response.textBoxArea.redirectStandard( sys.stdout )
            sys.stderr = self.response.textBoxArea.redirectStandard( sys.stderr )

            # Try to exec the code unsafely
            stored_messages = "\n"
            try:
                exec(blockOfCode, globals(), locals() ) # runs code and places myFunction here
                stored_messages += f"Unsafe code ran without and error.\n"
            except Exception as e:
                stored_messages = f"An error occurred during unsafe exec: {e}.\n"
                succeed = False

            # Put standard output back, get any input and ignore any final <cr>
            codeResponse = self.response.get().strip()
            sys.stdout = sys.stdout.reset()
            sys.stderr = sys.stderr.reset()
            self.canvas.update()

            # Show your messages from the unsafe exec after any text
            self.response.add(stored_messages)

            # Final answer check for correctness
            correctAnswer = str(dictionary['Return']) # stdout only uses strings
            if correctAnswer is None:
                succeed = True
                self.response.add("No correct answer was provided to check against, so you are good.\n")
            else:
                succeed = self.checkTheAnswer(codeResponse.answer, correctAnswer)
        return succeed, codeResponse, correctAnswer
    
    def returnColumnWidths(self, codeResponse, padding=3):
        numberOfColumns = len(codeResponse.header)
        columnWidths = [ 0 for x in range(numberOfColumns) ]
        
        # Find the lengths of each header and save
        for count,header in enumerate(codeResponse.header):
            length = len(header)
            if length > columnWidths[count]: columnWidths[count] = length
            
        # Find the lengths of each data point and save if longer
        for line in codeResponse.lines:
            for count,dataPoint in enumerate(line):
                length = len(dataPoint)
                if length > columnWidths[count]: columnWidths[count] = length
                
        # Add padding
        if padding > 0:
            for i in range(numberOfColumns):
                columnWidths[i] += padding
            
        return columnWidths
        
    def SQLProcessing(self, dictionary, blockOfCode):
        """ Process the code in the text box for SQL (no safety)"""

        # Clear the response text box to receive the response
        self.response.clear()
        self.canvas.update()

        """Try to execute the code. Code response contains:
        # data = Copy of the provided data
        # answer = A single JSON-like string for checking as an answer
        # error = Boolean of an error occured
        # message = Any provided message
        # lines = Data divided into a list of lists
        # header = The headers with extra spacing removed
        """
        sqlProcessing = SqlDatabaseProcessing()
        
        # The user nickname can be the server name
        if len(self.data.nickname) > 0:
            if sqlProcessing.useServer is not None and len(sqlProcessing.useServer) == 0:
                sqlProcessing.useServer = self.data.nickname
            
        codeResponse = sqlProcessing.queryDatabase(blockOfCode)
        
        # Process the result, no data received and an error could have occured
        if len(codeResponse.data) == 0:
            message = codeResponse.message
            if codeResponse.error:
                if len(message) == 0:
                    message = "An error occured, no details"
                message = "<Red>"+message+">"
            if len(message) > 0:
                self.response.add(message)
                
        # Process data received
        else:
            columnWidth = self.returnColumnWidths(codeResponse)
            wholeLine = ""
            wholeWidth = 0
            
            # Display the headers with a separating line __________
            for count,header in enumerate( codeResponse.header ):
                width = columnWidth[count]
                eachLine = header.ljust(width)
                wholeLine += eachLine
                wholeWidth += width
            wholeLine += "\n"
            self.response.add(wholeLine)
            wholeLine = wholeWidth*"_"+"\n"
            self.response.add(wholeLine)

            # Display the table of data
            for line in codeResponse.lines:
                wholeLine = ""
                for count,dataPoint in enumerate( line ):
                    width = columnWidth[count]

                    # Check if this is a number, and if so remove any unnecessary trailing zeroes
                    if type(dataPoint) == str:
                        try:
                            if dataPoint.find(".") >= 0:
                                floatValue = float(dataPoint)
                                intValue = int(floatValue)
                                if floatValue == intValue:
                                    dataPoint = str(intValue)
                        except:
                            pass
                    eachLine = dataPoint.ljust(width)
                    wholeLine += eachLine
                wholeLine += "\n"
                self.response.add(wholeLine)
                
            # Display any message
            if len(codeResponse.message) > 0:
                wholeLine = "\n" + codeResponse.message + "\n"
                self.response.add(wholeLine)
                
        # Final answer check for correctness
        success = False
        correctAnswer = str(dictionary['Return']) # stdout only uses strings
        if correctAnswer is None:
            success = True
            self.response.add("No correct return answer was provided to check against, so you are good.\n")
        elif codeResponse is None or codeResponse.error:
            pass
        else: 
            success = self.checkTheAnswer(codeResponse.answer, correctAnswer)
        self.canvas.update()
        return success

    def gradeButtonSelectedCodeEditor(self, window, statusBar):
        """Called when grade button is clicked. Temporary replacement for the standard funtion (same name)"""
        self.questionArea.resetGradeButton()
        success = False
                
        # Get and process the block of code based on its language
        # Wait here, check self.editbox
        response = None
        correctAnswer = None
        blockOfCode = self.editBox.get()
        if self.language.lower() == "sql":
            success = self.SQLProcessing(self.currentProblem, blockOfCode)
            
        # Defaults to Python (safe or unsafe)
        elif self.runSafeCode:
            success, response, correctAnswer = self.processingSafePython(self.currentProblem, blockOfCode)
        else:
            success, response, correctAnswer = self.unsafePythonProcessing(self.currentProblem, blockOfCode)
           
        # Final response to user
        if success:
            self.response.add(f"That is the correct answer ({response}), well done!\n")
        elif correctAnswer is not None:
            response = "" if response is None else response
            self.response.add(f"That is not the correct answer ({response} instead of {correctAnswer}).\n")    
        
        # Add a button to wait and clear the response only after the user sees the response
        self.clearResponseButton = Button( self.questionArea.buttonFrame, self.questionArea.buttonFormat, 
                                          background="Red", foreground="Black", borderwidth=4,
                                   text='Clear Response', coord=(0,self.questionArea.clearSlot), sticky=tk.LEFT, action=self.on_clear)
        self.questionArea.addEditingElement( self.clearResponseButton)
        self.questionArea.hideButtons()
        self.questionActive = False
        right = 1 if success else 0
        wrong = 1 if right == 0 else 0
        cleanup = False
        return success, right, wrong, cleanup # This question does its own cleanup so clean = False
    
    def on_clear(self, *args):
        self.questionArea.clearAfterQuestion()