__version__ = "8.0"
from CoffeeCanvas import *
from CoffeeBean import *
from MapClass import *
from QuestionAreaClass import *
from QuizClass import *
from DataClass import *
from SoundMixerClass import *
from CoffeeColors import *
from CoffeeCanvas import Text 

class DebuggingClass():
    """ Display debuggin info and controls under any question in the QuestionAreaClass canvas
    PARAMETERS:
         canvas:     where to draw graphics
         data:       all game data
         dictionary:'shortCut' allow short-cut character to move player in the scenario map to just below the 
                    target circle. Is independent from other debugging.
                    'debuggingOn' Debugging is active, including short-cut character
                    
    Various controls are provided. Selecting  the number in the circle rotates it through possible values. Choosing
    coins or torches will reset their number to that new amount. Flying should not be attempted until scrolling is 
    activated or scrolling is not accurate. Invisible objects can be colored to be seen. Select objects by their
    name and change their color see their location. Useful for darkness when pieces are lost.
    """
    def __init__(self, canvas, data, **kwargs):
        self.mainCanvas = canvas
        self.data = data.setResource('debugging', self)
        self.movement = 1
        self.currentObject = None
        self.currentlyBlack = True
        self.objectAreInvisible = True
        self.graphicsElements = []
        
        # Debugging features to move player to starting circle
        self.movePlayerLetter = 'z'  # This is the shortcut key to move directly to the dungeon
        self.active = kwargs.get("debuggingOn",False) 
        self.shortCut = kwargs.get("shortCut",False) 
        if not self.shortCut: self.shortCut = self.active # The shortcut can be active by itself
        
        # The shortcut can happen even if debugging are not active
        if self.shortCut or data.debugging:
            self.mainCanvas.forEventAddFunction(self.movePlayerLetter, self.dungeonShortcut)

    def dungeonShortcut(self, *args):
        """ Shortcut to get to the dungeon"""
        if (target:= self.data.quiz.get("Target Location", False)):
            if (map:= self.data.getResource("scenarioMap")) is not None:
                x = target[0]
                y = target[1]+map.circleSize+2 # Just outside the circle
                map.map.moveCenterObjectToPosition(x,y)

    def stop(self):
        """Remove debugging graphics which were saved into a list"""
        if self.active:
            self.mainCanvas.root.unbind(self.movePlayerLetter)
            for item in self.graphicsElements:
                item.undraw()
            
    
    def setDebuggingGraphics(self, canvasForGraphics):
        """Setup to display all the graphics. Not called when class is instantiated but when itis needed"""
        self.canvas = canvasForGraphics
        if ( size := self.data.getResource('size')):
            (x, y, width, height ) = self.mainCanvas.getFourDimensions( size['debugging'] )
            self.x = x
            self.y = y
            self.width = width
            self.height = height
        else:
            return
        
        # This is the positioning widget on badges, which is used to show the player position on the map.
        self.map = self.data.getResource("map")
        badges = self.data.getResource("badges")
        self.badgePositioningObject = badges.addIcon("Positioning", PlayerClass.TYPE_POSITIONING) # Position of player on map, generally used for map construction
        self.map.positioning = badges.updatePositioning
        
        # Notice: Dragging is incompatible with Debugging Class, dragging needs to be prevented!
        self.draggingSpecificallyAllowed = False
        self.startControls()

    # Initialize the control area on the canvas    
    def startControls(self):
        """Display all the graphics and store objects into a list for later removal"""
        if not self.active: return

        # Continue if controls are active
        badges = self.data.getResource("badges")
        badges.positioningAvailable = True
        badges.updatePositioning()
        self.mainCanvas.update()
        self.mainCanvas.forEventAddFunction(self.movePlayerLetter, self.dungeonShortcut)
        
        base = Rectangle( self.canvas, self.x, self.y, self.x+self.width, self.y+self.height, fill="Yellow", width=3)
        side = 30
        halfsies = side/2
        gap = 10
        x_1 = self.x + 10
        x_2 = x_1 + side + gap
        x_3 = x_2 + side + gap
        x_4 = x_3 + side + gap
        x_5 = x_4 + side + gap
        x_6 = x_5 + side + gap
        x_7 = x_6 + side + gap
        x_8 = x_7 + side + gap
        x_9 = x_8 + side + gap
        x_10 = x_9 + side + gap
        x_11 = x_10 + side + gap
        x_12 = x_11 + side + gap
        x_13 = x_12 + side + gap
        x_14 = x_13 + side + gap
        y_1 = self.y + 10
        y_2 = y_1 + side + gap
        y_3 = y_2 + side + gap
        y_4 = y_3 + side + gap
        y_5 = y_4 + side + gap
        y_6 = y_5 + side + gap
        y_7 = y_6 + side + gap
        y_8 = y_7 + side + gap
        y_9 = y_8 + side + gap
        y_10 = y_9 + side + gap
        y_11 = y_10 + side + gap
        y_12 = y_11 + side + gap
        y_13 = y_12 + side + gap
        y_14 = y_13 + side + gap

        # Add any additional initialization code here called by various buttons and controls 
        def moveObjectUp(*args):
            if self.currentObject is not None: 
                self.currentObject.move(0, -self.movement)
                center = self.currentObject.getCenter()
                actualCenter = self.map.convertMapCoordinatesToStandard(center)
                self.objectLocation.text = f"{int(actualCenter[0])}, {int(actualCenter[1])}"
                self.canvas.update()
        def moveObjectDown(*args):
            if self.currentObject is not None: 
                self.currentObject.move(0, self.movement)
                center = self.currentObject.getCenter()
                actualCenter = self.map.convertMapCoordinatesToStandard(center)
                self.objectLocation.text = f"{int(actualCenter[0])}, {int(actualCenter[1])}"
                self.canvas.update()
        def moveObjectLeft(*args):
            if self.currentObject is not None:
                self.currentObject.move(-self.movement, 0)
                center = self.currentObject.getCenter()
                actualCenter = self.map.convertMapCoordinatesToStandard(center)
                self.objectLocation.text = f"{int(actualCenter[0])}, {int(actualCenter[1])}"
                self.canvas.update()
        def moveObjectRight(*args):
            if self.currentObject is not None:
                self.currentObject.move(self.movement, 0)
                center = self.currentObject.getCenter()
                actualCenter = self.map.convertMapCoordinatesToStandard(center)
                self.objectLocation.text = f"{int(actualCenter[0])}, {int(actualCenter[1])}"
                self.canvas.update()

        def clearCurrentObject(*args):
            # Clear the current object from the map
            if not self.currentlyBlack: makeImagesRed()
            self.currentObject = None
            self.entry.setText("Press 'z' for dungeon")
            self.objectLabel.text = "No object selected"
            self.objectLocation.text="        "
            self.redButton.turnButtonOff()  # Deselect the red button if it was selected

        def loadObjectFromEntry(*args):
            if self.currentObject is not None: self.clearCurrentObject()
            objectName = self.entry.getText()
            if objectName is not None and len(objectName) > 0:
                # Search for the object in the data objects
                for obj in self.data.objects:
                    if obj["Name"].lower() == objectName.lower():
                        # Load the object at the current player location
                        map = self.data.getResource("playersMap")
                        if map is not None:
                            objectMap = map.map
                            self.currentObject = objectMap.canvas.findItemByNameInList(objectName)
                            if self.currentObject is not None:
                                center = self.currentObject.getCenter()
                                actualCenter = objectMap.convertMapCoordinatesToStandard(center)
                                self.objectLocation.text = f"{int(actualCenter.x)}, {int(actualCenter.y)}"
                                self.currentObjectDictionary = obj
                                self.objectLabel.text = f"Loaded: {self.currentObjectDictionary['File']}"
                        break
            if self.currentObject is None: self.objectLabel.text="Object not found"

        def makeImagesRed(*args):
            if self.currentObject is not None:
                if self.currentlyBlack:
                    self.currentlyBlack = False
                    if not hasattr(self.currentObject, "PILimage"):
                        self.currentObject.color = "Red"
                        self.currentObject.outlineColor = "Black"
                        self.currentObject.outlineWidth = 1
                        self.canvas.update()

                    else:
                        image = self.currentObject.PILimage
                        if image is not None:
                                # Change the color of all images to red
                                self.blackImage = self.currentObject.image
                                r, g, b, a = image.split()
                                r = r.point(lambda i: 255)  # Make everything red but keep the alpha channel
                                g = g.point(lambda i: 0)    # Remove green
                                redImage = PILImage.merge("RGBA", (r, g, g, a))
                                newImage = ImageTk.PhotoImage(redImage)
                                self.currentObject.updateImage(newImage)
                else:
                     # Change the color of all images back to original
                    self.currentlyBlack = True
                    if not hasattr(self.currentObject, "PILimage"):
                        if self.objectAreInvisible:
                            self.currentObject.color = ""
                            self.currentObject.outlineColor = ""
                            self.currentObject.outlineWidth = 0
                            self.canvas.update()
                        else:
                            self.currentObject.color = "Yellow"
                            self.currentObject.outlineColor = "Black"
                            self.currentObject.outlineWidth = 1
                            self.canvas.update()
                    else:
                        newImage = self.blackImage
                        self.currentObject.updateImage(newImage)
                        newImage = None

        def controlFlying(*args):
            # Toggle flying mode for the player
            self.map.setFlying(self.flyingButton.selected)

        def changeMovement(*args):
            if self.movement == 1:
                self.movement = 10
            elif self.movement == 10:
                self.movement = 50
            elif self.movement == 50:
                self.movement = 0
            else:
                self.movement = 1   
            self.movementText._setText(f"{self.movement}")

        def controlVisible(*args):
            # Toggle visibility of invisible objects, these are all COFFEECANVAS objects
            self.objectAreInvisible = not self.objectAreInvisible
            for objectDictionary in self.data.objects:
                purpose = objectDictionary.get("Purpose", None)
                if purpose is not None:
                    if purpose.lower() == "invisible":
                        mapObject = objectDictionary["MapObject"]
                        if self.objectAreInvisible:
                            mapObject.color = ""
                            mapObject.outlineColor = ""
                            mapObject.outlineWidth = 0
                        else:
                            mapObject.color = "Yellow"
                            mapObject.outlineColor = "Black"
                            mapObject.outlineWidth = 1
                        self.canvas.update()
            

        def loadEpilogIntoInstructions(*args):
            instructions = self.data.getResource("instructions")
            if instructions is not None:
                text = self.data.makeTheEpilogue("\nTesting the Epilogue\n"+30*"-"+"\n")
                instructions.set(text)
                
        def changeWeapon(*args):
            player = self.data.getResource("player")
            weapon = player.nameOfWeapon()
            if weapon is None:
                self.data.pickupAxe()
            elif weapon == "Axe":
                player.removeItem("Axe")
                player.addItem("Sword", PlayerClass.TYPE_SWORD)
            else:
                player.weaponIsDamaged()

        def changeTorches(*args):
            self.data.torchChange(self.movement)
            rewardBox = self.data.getResource("rewardBox")
            rewardBox.checkForGameOver()
            
        def changeGold(*args):
            rewardBox = self.data.getResource("rewardBox")
            rewardBox.changeReward("Gold", self.movement)
            rewardBox.checkForGameOver()
        def changeSilver(*args):
            rewardBox = self.data.getResource("rewardBox")
            rewardBox.changeReward("Silver", self.movement)
            rewardBox.checkForGameOver()
        def changeCopper(*args):
            rewardBox = self.data.getResource("rewardBox")
            rewardBox.changeReward("Copper", self.movement)
            rewardBox.checkForGameOver()

        # 4 triangles for moving the object
        triangleLeft = SmartPolygon(self.canvas, (x_1, y_2+halfsies), (x_1+side, y_2), (x_1+side, y_2+side), fill="LightGreen", width=2, action=moveObjectLeft, dragging=self.draggingSpecificallyAllowed)
        triangleUp = SmartPolygon(self.canvas, (x_2+halfsies, y_1), (x_2, y_1+side ), (x_2 + side, y_1+side), fill="Green", width=2, action=moveObjectUp, dragging=self.draggingSpecificallyAllowed)
        triangleDown  = SmartPolygon(self.canvas, (x_2, y_3), (x_2+halfsies, y_3+side), (x_2+side, y_3), fill="Blue", width=2, action=moveObjectDown, dragging=self.draggingSpecificallyAllowed)
        triangleRight = SmartPolygon(self.canvas, (x_3, y_2), (x_3, y_2+side), (x_3+side, y_2+halfsies), fill="LightBlue", width=2, action=moveObjectRight, dragging=self.draggingSpecificallyAllowed)
        movementButton = SmartCircle(self.canvas, (x_2+halfsies), y_2+halfsies, halfsies, fill="LightRed", action=changeMovement, dragging=self.draggingSpecificallyAllowed)
        self.movementText = SmartText(self.canvas, (x_2+halfsies), y_2+halfsies, text="1", action=changeMovement, 
                            font=("TKDefaultFont", 12), dragging=self.draggingSpecificallyAllowed)
        
        # Entry to name the object
        self.entry = CanvasEntry(self.canvas, x_8, y_2-halfsies, text="", editCharacterWidth=33, dragging=self.draggingSpecificallyAllowed )
        # Text to show file selected
        self.objectLabel = Text(self.canvas, x_9, y_3-halfsies, text="Object file name goes here", width=330, 
                            background="LightBx_n",font=("TKDefaultFont", 16))
        # OK button to take entry and open the object in its starting location (based on searching All_Objects.json, questions and places)
        self.loadButton = CanvasButton(self.canvas, Point(x_10, y_4 ), Point(x_13, y_5) , "Load", action=loadObjectFromEntry, 
                            font=("TKDefaultFont", 16), squaricle=True, dragging=self.draggingSpecificallyAllowed)
        # Text to show object center location
        backgroundBox = Rectangle(self.canvas, x_1, y_4, x_8, y_6, fill="White", width=1)
        centerText = Text(self.canvas, x_2, y_5, text="Center:", font=("TKDefaultFont", 16))
        self.objectLocation = Text(self.canvas, x_4, y_5, text="", font=("TKDefaultFont", 16))
        # Clear button to clear the control area
        self.clearButton = CanvasButton(self.canvas, Point(x_10, y_5), Point(x_13, y_6 ), "Clear", action=clearCurrentObject, 
                            font=("TKDefaultFont", 16), squaricle=True, dragging=self.draggingSpecificallyAllowed)
        # Button to make images red
        self.redButton = CanvasButton(self.canvas, Point(x_10, y_6 ), Point(x_13, y_7 ), "Red Image", action=makeImagesRed, 
                            font=("TKDefaultFont", 16), squaricle=True, toggle=("Red"), dragging=self.draggingSpecificallyAllowed)
        # Toggle Button to make flying possible
        self.flyingButton = CanvasButton(self.canvas, Point(x_10, y_8), Point(x_13, y_9 ), "Flying", action=controlFlying, 
                            font=("TKDefaultFont", 16), squaricle=True, toggle=("Red"), dragging=self.draggingSpecificallyAllowed)
        # Toggle Button to make invisible objects visible (go throu list to change color and border)
        self.visibleButton = CanvasButton(self.canvas, Point(x_10, y_9 ), Point(x_13, y_10 ), "Visible", action=controlVisible, 
                            font=("TKDefaultFont", 16), squaricle=True, toggle=("Red"), dragging=self.draggingSpecificallyAllowed)
        
        # OK button to take entry and open the object in its starting location (based on searching All_Objects.json, questions and places)
        self.epilogButton = CanvasButton(self.canvas, Point(x_10, y_10 ), Point(x_13, y_11) , "Epilogue", action=loadEpilogIntoInstructions, 
                            font=("TKDefaultFont", 16), squaricle=True, dragging=self.draggingSpecificallyAllowed)
        ### Second Group
        # Damage your sword
        self.damageButton = CanvasButton(self.canvas, Point(x_6, y_8 ), Point(x_9+10, y_9) , "New Weapon", action=changeWeapon, 
                            font=("TKDefaultFont", 16), squaricle=True, dragging=self.draggingSpecificallyAllowed)
        
        self.torchButton = CanvasButton(self.canvas, Point(x_6, y_9 ), Point(x_9+10, y_10) , "Torches", action=changeTorches, 
                            font=("TKDefaultFont", 16), squaricle=True, fill="LightGreen", dragging=self.draggingSpecificallyAllowed)
        
        self.goldButton = CanvasButton(self.canvas, Point(x_4, y_10 ), Point(x_6, y_11) , "Gold", action=changeGold, 
                            font=("TKDefaultFont", 16), squaricle=True, fill="LightGreen", dragging=self.draggingSpecificallyAllowed)        
        self.silverButton = CanvasButton(self.canvas, Point(x_6, y_10 ), Point(x_8, y_11) , "Silver", action=changeSilver, 
                            font=("TKDefaultFont", 16), squaricle=True, fill="LightGreen", dragging=self.draggingSpecificallyAllowed)
        self.copperButton = CanvasButton(self.canvas, Point(x_8, y_10 ), Point(x_10, y_11) , "Copper", action=changeCopper, 
                            font=("TKDefaultFont", 16), squaricle=True, fill="LightGreen", dragging=self.draggingSpecificallyAllowed)
        circleNumberText = Text(self.canvas, x_7, y_11+10, text="Change using the circle number", font=("TKDefaultFont", 10))
        
        # Used to remove htem
        self.graphicsElements = [base, triangleLeft, triangleUp, triangleDown, triangleRight, movementButton,
                                 self.movementText, self.entry, self.objectLabel, self.loadButton, backgroundBox,
                                 centerText, self.objectLocation, self.clearButton, self.redButton, self.flyingButton,
                                 self.visibleButton, self.epilogButton, self.damageButton, self.torchButton,
                                 self.goldButton, self.silverButton, self.copperButton, circleNumberText]
        