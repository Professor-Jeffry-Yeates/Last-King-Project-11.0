# CoffeeBean
__version__ = "8.0"
""" Access to most Tkinter widgets """

import tkinter as tk
from tkinter import ttk
from tkinter.font import Font
import random, datetime, math, re, os
from CoffeeColors import *
import sys
class BasicWidget():
    def __init__(self, parent, *dictionaries, **dictionary):
        self.parent = parent
        self.window = parent
        while not isinstance(self.window.widget, tk.Tk):
            self.window = self.window.parent
        self.colors = self.window.colors
        self.widget = None # Main ttk Widget used
        self.label = None # Label Widget used with some Widgets
        self.variable = tk.StringVar(value='') # tk.StringVar used with most Widgets
        self.formatting = None # "{}" Expected auto-formatting of printed value
        self.formatType = "" # Variable type returned with value in Widget
        self.correctAnswer = None # Stores the correct answer, if applicable
        self.enabled = True # Keep track here as this state cannot be retrieved.  Note Text fields use this seperately for readonly status.
        self.visible = True # Keep track of visibility and keep grid-state so it can be retrieved.
        self.activated = True # Keep track of activation status, no specific definition or value, use as needed for your specific purposes
        self.name = "" # Name of Widget used when sending the current value
        self.title = "" # Title of Widget used when sending the current value
        self.attribute, self.placement = {}, {} # Temporary holding of widget attributes
        self.place, self.pack, self.grid = False, False, True # Which form of placement is used
        self.x = None # Used for Canvas widgets (x,y) position and size (w,h) in a canvas
        self.y = None # Keep the None values if not placed into a Canvas widget
        self.width = 0
        self.height = 0
        self.command = None
        self.actions = []
        self.dictionary = self.combineDictionaries( dictionaries, dictionary)
        self.setAttributes()

    # Static and Class Methods
    def defineSticky(self, value):
        if self.pack:
            return self.defineSidePlacement(value)
        else:
            match value.lower():
                case 'fullwidth': myPlacement = (tk.W + tk.E)
                case 'full': myPlacement = (tk.NSEW)
                case 'west': myPlacement = tk.W
                case 'east': myPlacement = tk.E
                case 'north': myPlacement =  tk.N
                case 'south': myPlacement = tk.S
                case 'upperleft' | 'northwest': myPlacement = tk.NW
                case 'upperright' | 'northeast': myPlacement = tk.NE
                case 'lowerleft' | 'southwest': myPlacement = tk.SW
                case 'lowerright' | 'southeast': myPlacement = tk.SE
                case 'left' : myPlacement = tk.W
                case 'right' : myPlacement = tk.E
                case 'top' : myPlacement =  tk.N
                case 'bottom' : myPlacement = tk.S
                case 'center': myPlacement =  tk.CENTER
                case 'side': myPlacement = tk.LEFT
                case _: myPlacement = value
            return myPlacement

    def defineSidePlacement(value):
        match value.lower():
            case 'left' | 'west': myPlacement = tk.LEFT
            case 'right' | 'east': myPlacement = tk.RIGHT
            case 'top' | 'north': myPlacement =  tk.TOP
            case 'bottom' | 'south': myPlacement = tk.BOTTOM
            case 'center': myPlacement =  tk.CENTER
            case 'side': myPlacement = tk.LEFT
            case _: myPlacement = value
        return myPlacement
    defineSidePlacement = staticmethod(defineSidePlacement)

    # General methods (overload for specific needs)
    def getWindow(self):
        return self.window
    def getName(self):
        if len(self.name) == 0:
            self.name = self.label.name
            if len(self.label.name) == 0:
                number = random.randint(1,99999)
                self.name = f"Unknown Widget #{number}"
        return self.name
    def getTitle(self):
        if len(self.title) == 0:
            return self.getName()
        return self.title
    def getCanvas(self):
        return self.window.canvas
    def addWidgetToWindow(self):
        self.window.addWidget(self)
    def clear(self):
        if self.variable is not None:
            self.variable.set(value='')
    def changeState(self, state):
        self.enabled = state
        self.widget.configure(state=state)
    def returnVariableValueBasedOnType(self, text=None):
        if text is None:
            if self.variable is None: return None
            if self.enabled == tk.DISABLED: return None
            value = self.variable.get()
        else:
            value = text
        if value != '':
            match self.formatType:
                case tk.IntVar:
                    try:
                        value = int(value)
                    except:
                        value = ''
                case tk.DoubleVar:
                    try:
                        value = float(value)
                    except:
                        value = ''
                case tk.BooleanVar:
                    try:
                        if value.lower() == 'true':
                            value = True
                        elif value.lower == 'false':
                            value = False
                        else:
                            value = bool(value)
                    except:
                        value = bool(value)
        return value
    def resetDictionaries(self, keepDictionary=False):
        self.attribute, self.placement = {}, {}
        if not keepDictionary: self.dictionary ={}
    def errorCheck(self): return # Override with validity check

    # Tkinter attributes neededing further processing
    def setColumnWeights(self, weights):
        if isinstance( weights, int):
            for column in range(weights):
                self.widget.columnconfigure( column, weight=1)
        else:
            column = 0
            for weight in weights:
                self.widget.columnconfigure( column, weight=weight )
                column += 1
    def setRowWeights(self, weights):
        if isinstance( weights, int):
            for row in range(weights):
                self.widget.rowconfigure( row, weight=1)
        else:
            row = 0
            for weight in weights:
                self.widget.rowconfigure( row, weight=weight )
                row += 1
    def setInitialText( self, value ):
        self.widget.insert('1.0', value)
    def setText( self, value ):
        text = value
        if self.formatting is not None: text = self.formatting(text)
        self.attribute['text']=text
        if self.name is None:
            self.name = text
        elif len(self.name) == 0:
            self.name = text

    def setTextFont( self, value):
        self.attribute['font']=value
    def setForeground( self, value ):
        self.attribute['foreground']=self.colors.get(value, value)
    def setFg( self, value ):
        self.attribute['fg']=self.colors.get(value, value)
    def setBg( self, value ):
        self.attribute['bg']=self.colors.get(value, value)
    def setBackground( self, value ):
        self.attribute['background']=self.colors.get(value, value)
    def setJustify( self, value ):
        self.attribute['justify']=value
    def setDisableByList(self, list):
        for widget in list:
            widget.changeState(tk.DISABLED)
    def setEnableByList(self, list):
        for widget in list:
            widget.changeState(tk.NORMAL)
    def undraw(self):
        self.widget.destroy()
    def delete(self):
        self.widget.destroy()
    def setActivated(self, value):
        self.activated = value # Can be any value you want
    def setDisable(self):
        self.changeState(tk.DISABLED)
    def setEnable(self):
        self.changeState(tk.NORMAL)
    def setVisibleByList(self, list):
        for widget in list:
            widget.setVisible()
    def setInvisibleByList(self, list):
        for widget in list:
            widget.setInvisible()
    def setVisible(self):
        if not self.visible:
            self.visible = True
            if self.pack:
                self.widget.pack()
            elif self.place:
                self.widget.place()
            else:
                self.widget.grid()
    def setInvisible(self):
        if self.visible:
            self.visible = False
            if self.pack:
                self.widget.pack_forget() # or _remove???
            elif self.place:
                self.widget.place_forget()
            else:
                self.widget.grid_forget()
    def checkVisibilityStatus(self): # Boolean of visibility, retrieved back two generations
        visibilityStatus = True
        if not self.visible:
            visibilityStatus = False
        elif self.parent is not None:
            parentWidget = self.parent
            if hasattr(parentWidget,'visible'): # If parent is a window or frame (or others), it has no visibility status
                try:
                    visibilityStatus = parentWidget.visible
                    if visibilityStatus:
                        if parentWidget.parent is not None:
                            parentWidget = parentWidget.parent
                            if hasattr(parentWidget,'visible'):
                                visibilityStatus = parentWidget.visible
                except:
                    pass
        return visibilityStatus
    # Non-Tkinter widget attributes
    def setName( self, value):
        self.name = value
    def setTitle( self, value):
        self.title = value
    def setVerticalAlignment( self, value ):
        if hasattr(self, 'vertical'):
            self.vertical = (value == True)
    def setFormatting( self, value ):
        self.widget.formatting=value
    def setFormatType( self, value):
        if isinstance(value, tk.StringVar) or isinstance(value, str):
            self.formatType=tk.StringVar()
        elif isinstance(value, tk.IntVar) or isinstance(value, int):
             if not isinstance(self.formatType,tk.DoubleVar): self.formatType=tk.IntVar() # Once a double, always a double
        elif isinstance(value, tk.DoubleVar) or isinstance(value, float):
            self.formatType=tk.DoubleVar()
        elif isinstance(value, tk.BooleanVar) or value == bool(value):
            self.formatType=tk.BooleanVar()
        elif value in (True,False,'True','False','true','false','TRUE','FALSE'):
            self.formatType=tk.BooleanVar()
        else:
            try:
                number = float(value)
                if number.isclose(int(number)):
                    if not isinstance(self.formatType,tk.DoubleVar): self.formatType=tk.IntVar() # Once a double, always a double
                else:
                    self.formatType=tk.DoubleVar()
            except:
                self.formatType=tk.StringVar()

    # Placement widget attributes
    def setSide( self, value ):
        sticky = self.defineSticky(value)
        self.placement['side']=sticky
    def setExpand( self, value ):
        self.placement['expand']=value
    def setStickyPlacement( self, value ):
        sticky = self.defineSticky(value)
        self.placement['sticky']=sticky
    def setPadX( self, value):
        self.placement['padx']=value
    def setPadY( self, value):
        self.placement['pady']=value
    def setInteriorPadX( self, value):
        self.placement['ipadx']=value
    def setInteriorPadY( self, value):
        self.placement['ipady']=value
    def setRow( self, value):
        self.placement['row']=value
    def setColumn( self, value):
        self.placement['column']=value
    def setRowspan( self, value):
        self.placement['rowspan']=value
    def setColumnspan( self, value):
        self.placement['columnspan']=value
    def setCoord( self, value):
        self.setRow( value[0])
        self.setColumn( value[1])
        if len(value) > 2:
            self.setRowspan( value[2])
            if len(value) > 3:
                self.setColumnspan( value[3])
    def canvasSet_x( self, value):
        self.x = value
        self.setStickyPlacement( "nw" )
    def canvasSet_y( self, value):
        self.y = value
    def canvasSetWidth( self, value):
        self.width = value
    def canvasSetHeight( self, value):
        self.height = value
    def canvasSize( self, value):
        self.canvasSize = value
        self.placement['side'] = tk.NW
    def setPlace( self, value):
            self.place, self.pack, self.grid = (value==True), False, False
    def setPack( self, value):
            self.place, self.pack, self.grid = False, (value==True), False
    def setGrid(self, value ):
        self.place, self.pack, self.grid = False, False, (value==True)
    def settingPlacement(self):
        placeInCanvas = self.x is not None and self.y is not None
        if placeInCanvas:
            self.parent.widget.create_window(self.x, self.y, width=self.width, height=self.height, anchor=self.placement['sticky'], window=self.widget)
            self.parent.widget.configure(scrollregion=self.parent.widget.bbox("all"))
        elif self.pack:
            self.widget.pack(**self.placement)
        elif self.place:
            self.widget.place(**self.placement)
        elif self.grid:
            self.widget.grid(**self.placement)
        else:
            self.widget.pack(fill="both", expand=True)

        self.resetDictionaries()
    def setCommand(self, value):
        if self.widget is not None:
            self.widget.configure(command=value)
        else:
            self.command = value # Hold it until the Button is created

    def callActions(self, *args):
        """Call all functions in the self.actions[] list in order"""
        if len(self.actions) > 0:
            useActions = self.actions.copy() # make a copy so original list can be modified by actions
            for function in useActions:
                if isinstance(function, list) or isinstance(function, tuple):
                    for nestedFunction in function:
                        if nestedFunction is not None:
                            nestedFunction(self, *args)
                elif function is not None:
                    function(self, *args)

    def saveObjectActions(self, function, makeFirst=False):
        """Set the function to be called when the object is selected.  There can
        be multiple functions called in the order they were added"""
        if function is None: return # No function to save
        if isinstance(function, list) or isinstance(function, tuple):
            if len(function) > 0:
                if makeFirst:
                    newList = function.reverse()
                    for eachFunction in newList:
                        if eachFunction is not None:
                            self.actions.insert(0,eachFunction)
                else:
                    for eachFunction in function:
                        if eachFunction is not None:
                            self.actions.append(eachFunction)
        else:
            self.actions.append(function)
        self.setCommand(self.callActions)

    def replaceActions( self, *args ):
        actionCopy = self.actions.copy()
        self.actions.clear()
        self.saveObjectActions(args)
        return actionCopy

    def setCorrectAnswer( self, value):
        self.correctAnswer = value

    # Attributes placed into attribute and placement dictionaries
    def combineDictionaries( self, dictionaries, dictionary ):
        returnDictionary = {}
        if dictionaries is not None and len(dictionaries) > 0:
            for eachDictionary in dictionaries:
                if eachDictionary is not None and len(eachDictionary) > 0:
                    if isinstance(eachDictionary, tuple):
                        for aDictionary in eachDictionary:
                            if aDictionary is not None and len(aDictionary) > 0:
                                returnDictionary.update(aDictionary)
                    else:
                        if len(eachDictionary) > 0:
                            returnDictionary.update(eachDictionary)

        if dictionary is not None and len(dictionary) > 0:
            returnDictionary.update(dictionary)
        return returnDictionary
    def setAttribute( self, key, value ):
        match key:
            case 'sticky': self.setStickyPlacement( value)
            case 'text': self.setText( value)
            case 'textfont': self.setTextFont( value)
            case 'foreground': self.setForeground( value)
            case 'background': self.setBackground( value)
            case 'justify': self.setJustify( value)
            case 'padx': self.setPadX( value)
            case 'pady': self.setPadY( value)
            case 'coord': self.setCoord( value)
            case 'row': self.setRow( value)
            case 'column': self.setColumn( value)
            case 'place': self.setPlace( value )
            case 'pack': self.setPack(value)
            case 'side': self.setSide(value)
            case 'expand': self.setExpand(value)
            case 'grid': self.setGrid(value)
            case 'rowweights': self.setRowWeights(value)
            case 'columnweights': self.setColumnWeights(value)
            case 'name': self.setName(value)
            case 'title': self.setTitle(value)
            case 'command': self.setCommand(value)
            case 'action': self.saveObjectActions(value)
            case 'correct': self.setCorrectAnswer(value)
            case 'validate': pass # handled by separate code
            case 'x': self.canvasSet_x( value)
            case 'y': self.canvasSet_y( value)
            case 'width': self.canvasSetWidth( value)
            case 'height': self.canvasSetHeight( value)
            case _:
                self.attribute[key]=value # All other attributes directly stored

    def setAttributes( self, limitTo=None, exclude=None ):
        if len(self.dictionary) > 0:
            for keyValue, value in self.dictionary.items():
                key = keyValue.lower()
                if exclude is not None and key in exclude: continue
                if limitTo is not None and keyValue not in limitTo: continue
                self.setAttribute( key, value)
    def setSpecificAttributes( self, **dictionary):
        if len(dictionary) > 0:
            for keyValue, value in dictionary.items():
                key = keyValue.lower()
                self.setAttribute( key, value)
    def copyAllowedAttributes( self, allowedKeyList ):
        returnDictionary = {}
        for key, value in self.attribute.items():
            if key in allowedKeyList:
                returnDictionary[key] = value
        return returnDictionary
    # Set variables or attributes after widget is created
    def setVariable( self, keyValue, value ):
        key = keyValue.lower()
        match key:
            case 'weights': self.setColumnWeights( value )
            case 'columnweights': self.setColumnWeights( value )
            case 'rowweights': self.setRowWeights( value )
            case 'vertical': self.setVerticalAlignment( value)
            case 'formatting': self.setFormatting( value)
            case 'formattype': self.setFormatType( value)
            case 'command': self.setCommand( value)
            case 'initialtext': self.setInitialText( value)
    def setVariables( self, limitTo=None, exclude=None ):
        if len(self.dictionary) > 0:
            for keyValue, value in self.dictionary.items():
                key = keyValue.lower()
                if exclude is not None and key in exclude: continue
                if limitTo is not None and keyValue not in limitTo: continue
                self.setVariable( keyValue, value )
    def answerIsCorrect(self):
        response = False
        userResponse = self.get()
        if isinstance(userResponse, dict):
            if isinstance(self.correctAnswer, list):
                response = True
                for key, value in userResponse.items():
                    if key in self.correctAnswer:
                        if not value: response = False
                    elif value: response = False
            else:
                response = self.userResponse.get(self.correctAnswer,False)
        elif isinstance(self.correctAnswer, list):
            if userResponse in self.correctAnswer:
                response = True
        elif userResponse == self.correctAnswer:
            response = True
        return response

class ScrollingWidget(BasicWidget):
    def __init__(self, parent, *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)
        self.scrolling = self.dictionary.get('scrolling',False)

    # TODO: Implement scrolling perhaps with something in draw (predraw, normal draw, post draw)
    def setScrollingFrame(self, kind="both", frameWidget=None):
        """ Set up the scrolling frame for the widget.  This is used for all widgets.
        """
        if self.scrolling:
            if frameWidget is None:
                self.parent.widget = ttk.Frame(self.parent.widget)
                self.parent.widget.pack(fill="both", expand=True)
            else:
                self.parent.widget = frameWidget
            self.kind = kind

    def setScrollingAfterFrame(self):
        if self.scrolling:
            self.setPack(True)
            self.placement = dict(fill="both", expand=True)

            if self.kind == "both" or self.kind == "horizontal":
                self.xscrollWidget = ttk.Scrollbar(self.widget, command=self.widget.xview, orient=tk.HORIZONTAL)
                self.xscrollWidget.pack(side=tk.BOTTOM, fill=tk.X)

            if self.kind == "both" or self.kind == "vertical":
                self.yscrollWidget = ttk.Scrollbar(self.widget, command=self.widget.yview, orient=tk.VERTICAL)
                self.yscrollWidget.pack(side=tk.RIGHT, fill=tk.Y)

            if self.kind == "both" or self.kind == "horizontal":
                self.widget.configure(xscrollcommand=self.xscrollWidget.set)

            if self.kind == "both" or self.kind == "vertical":
                self.widget.configure(yscrollcommand=self.yscrollWidget.set)

            # Bind configuration events to the canvas' scroll bars within the scroll region provided
            self.widget.bind('<Configure>', lambda e: self.frameParent.configure(scrollregion=self.frameWidget.bbox("all")))

class Label(BasicWidget):
    def __init__(self, parent, *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)
        self.setAttributes()
        
        # Any image on the label can be the full directory to a file or an actual image
        if ( image := self.attribute.pop('image',None)):
            if type(image) == str:
                if os.path.exists(image):
                    self.fullpath = image
                    self.image = tk.PhotoImage(file=image)
                    self.attribute['image'] = self.image
                else:
                    self.data.logError(f"Image not found in {image}")
            else:
                self.image = image
                self.attribute['image'] = image
            
        self.widget = tk.Label(parent.widget, **self.attribute)
        self.setVariables()
        self.settingPlacement()

    # Property
    def get(self):
        text = self.widget.cget("text")
        text = self.returnVariableValueBasedOnType(text=text)
        return text
    def set( self, text):
        if self.formatting is not None: text = self.formatting(text)
        self.widget.configure(text=text)
    value = property(get, set)

    # Individual elements set
    def setAnchor( self, value): self.attribute['anchor']=value
    def setWraplength( self, value): self.attribute['wraplength']=int(value)
    def setUnderline( self, value): self.attribute['underline']=int(value)
    def setAttributes( self, limitTo=None, exclude=None ):
        if len(self.dictionary) > 0:
            for keyValue, value in self.dictionary.items():
                key = keyValue.lower()
                if exclude is not None and key in exclude: continue
                if limitTo is not None and key not in limitTo: continue
                if key == 'anchor': self.setAnchor( value)
                elif key == 'wraplength':self.setWraplength( value)
                elif key == 'underline': self.setUnderline( value)
                else: super().setAttribute(key, value)

class FixedLabel(Label):
    def __init__( self, parent, coord, *dictionaries, **dictionary):
        super().__init__(parent, dictionaries, dictionary)
        self.setAttribute( "coord", coord) # This is a special attribute for FixedLabel
        self.widget = Label( parent, dictionary)

    # Property
    def get(self):
        text = self.widget.cget("label")
        text = self.returnVariableValueBasedOnType(text=text)
        return text
    def set( self, text):
        if self.formatting is not None: text = self.formatting(text)
        self.widget.configure(text=text)
    value = property(get, set)

class BasicFrame( BasicWidget ): # Not instantiated
    def __init__(self, parent, *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)
        self.scrolling = False

# Frame specific methods
    def destroy(self):
        self.widget.destroy()
    def setBorderWidth( self, value ):
        self.attribute['bd']=int(value)
    def setBackground( self, value ):
        self.attribute['background']=self.colors.get(value, value)
    def setRelief( self, value ):
        if isinstance( value, str):
            useValue = value
            checking = value.lower()
            match checking:
                case 'flat': useValue= tk.FLAT
                case 'groove': useValue= tk.GROOVE
                case 'raised': useValue= tk.RAISED
                case 'ridge': useValue= tk.RIDGE
                case 'solid': useValue= tk.SOLID
                case 'sunken': useValue= tk.SUNKEN
            self.attribute['relief']=useValue
    def setBorderWidth( self, value ):
        self.attribute['borderwidth']=int(value)
    def setWidth( self, value ):
        self.attribute['width']=int(value)
    def setHeight( self, value ):
        self.attribute['height']=int(value)
    def setHighlightbackground( self, value ):
        self.attribute['highlightbackground']=self.colors.get(value, value)
    def setHighlightColor( self, value ):
        self.attribute['highlightcolor']=self.colors.get(value, value)
    def setHighlighthightThickness( self, value ):
        self.attribute['highlightthickness']=int(value)
    def setCursor( self, value ): # There are 40 types at least
        self.attribute['cursor']=value
    def setAttribute( self, keyValue, value ):
        key = keyValue.lower()
        match key:
            case 'cursor': self.setCursor( value)
            case 'height': self.setHeight( value)
            case 'width': self.setWidth( value)
            case 'highlightbackground': self.setHighlightbackground( value)
            case 'highlightcolor': self.setHighlightColor( value)
            case 'highlightthickness': self.setHighlighthightThickness( value)
            case 'relief': self.setRelief(value)
            case 'borderwidth': self.setBorderWidth( value)
            case 'columnweights': pass # used by setVariable only
            case 'rowweights': pass
            case _: super().setAttribute( keyValue, value )

    def setVariables( self, limitTo=None, exclude=None ):
        if len(self.dictionary) > 0:
            for keyValue, value in self.dictionary.items():
                key = keyValue.lower()
                if exclude is not None and key in exclude: continue
                if limitTo is not None and keyValue not in limitTo: continue
                if key == 'height': self.widget.grid_propagate(0)
                elif key == 'width': self.widget.grid_propagate(0)
                else: super().setVariable( key, value)

class Frame( BasicFrame ):
    def __init__(  self, parent, *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)
        self.setAttributes(exclude=('font','textfont'))
        self.widget = tk.Frame(parent.widget, **self.attribute)
        self.setVariables()
        self.settingPlacement()

    # Property
    def get(self):
        return None
    def set(self, value):
        pass
    value = property(get, set)

class LabelFrame( BasicFrame ):
    def __init__( self, parent, *dictionaries, **dictionary):
        super().__init__(parent, dictionaries, dictionary)
        self.setAttributes()
        self.widget = tk.LabelFrame(parent.widget, **self.attribute)
        self.setVariables()
        self.settingPlacement()

    def get(self):
        return self.text
    def set( self, text):
        self.standardLabelSet(text)
    value = property(get, set)

    def setAttribute( self, keyValue, value ):
        key = keyValue.lower()
        match key:
            case 'text': self.setText( value)
            case _: super().setAttribute( keyValue, value )

class Entry( BasicWidget): # ScrollingWidget ):
    def __init__(self, parent, *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)
        self.hint  = "" # Stores any hint text
        self.showDot=None
        self.regexFormat = "" # Stores any Regex statements
        (row, column) = self.dictionary['coord']
        if 'text' in self.dictionary:
            self.setAttributes(limitTo=('font','fg','bg','coord','text'))
            self.setAttributes(limitTo=('textfont')) # Overrides any font in the above
            self.attribute.update(self.placement)
            self.label = Label(parent, **self.attribute) # Automatically placed within parent
            self.resetDictionaries(keepDictionary=True)
            row += 1

        # make a dictionary of self.attribute that is only for the entry with new coord
        self.setAttributes(exclude=('coord','row','column','text','textfont'))
        self.setAttribute('coord', (row,column))
        if self.showDot is not None: self.attribute["show"] = self.showDot
        self.widget = ttk.Entry( parent.widget, textvariable=self.variable, **self.attribute)
        self.setVariables()
        self.settingPlacement()
        self.addWidgetToWindow()

    #Propeties established
    def get(self):
        value = self.returnVariableValueBasedOnType()
        if len(self.hint) > 0:
            if value == self.hint: value = ''
        return value
    def set(self, value):
        self.variable.set(value)
    value = property(get, set)

    # Individual elements set
    def setShow( self, value):
        if isinstance(value, str):
            self.showDot=value
        else:
            self.showDot = '•'
    def setInitialText(self, value): self.variable.set(value)
    def setRegex(self, value):
        self.regexFormat = value
    def setHint( self, value):
        self.hint = value
    def setAttributes( self, limitTo=None, exclude=None ):
        if len(self.dictionary) > 0:
            for keyValue, value in self.dictionary.items():
                key = keyValue.lower()
                if exclude is not None and key in exclude: continue
                if limitTo is not None and key not in limitTo: continue
                if key == 'show': self.setShow( value)
                elif key == 'initialtext': self.setInitialText( value)
                elif key == 'regex': self.setRegex( value)
                elif key == 'hint': self.setHint(value)
                else: super().setAttribute( key, value)
# TODO Implement ListBox (ScrollingWidget):
class ComboBox( ScrollingWidget ):
    def __init__( self, parent, values, *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)
        self.correctAnswer = self.attribute.pop('answer',None)
        maxwidth = self.attribute.pop('maxwidth',200)
        newIndex = self.attribute.pop('newindex',None)
        readonly = self.attribute.pop('readonly',True)
        state = ["readonly"] if readonly else ["normal"]
        #text = self.attribute.pop('text', "Choose One")
        #title = self.attribute.pop('title', "Combo Box")
        self.setPack(True)

        if True: # 'text' in self.dictionary:
            self.setAttributes(limitTo=('font','fg','bg','coord','text'))
            self.setAttributes(limitTo=('textfont')) # Overrides any font in the above
            self.placement = {'pack':True, 'side': tk.TOP, 'expand':True, 'wraplength': maxwidth-15, 'width': maxwidth-5}
            self.attribute.update(self.placement)
            self.label = Label(parent, **self.attribute)

            self.attribute["text"] = " " # Needed to force combo down one line
            self.emptylabel = Label(parent, **self.attribute)
            self.resetDictionaries(keepDictionary=True)

        # make a dictionary of self.attribute that is only for the combo with new coord
        self.setAttributes(exclude=('coord','row','column','text','textfont','borderwidth','relief','answer','maxwidth','readonly','newindex'))
        if 'font' in self.dictionary:
            window = self.getWindow()
            window.saveCheckboxFont(self.dictionary['font'])
        if 'background' in self.dictionary:
            window = self.getWindow()
            color = self.dictionary['background']
            color = window.colors.get(color, color)
            window.saveCheckboxBackgroundColor(color)


        self.setScrollingFrame(parent.widget, frameWidget=parent.widget)
        # This option specifies the width of the entry area as a number of characters.
        # The actual width will be this number times the average width of a character in
        # the effective font.
        width = 0
        for item in values:
            length = len(item)
            if length > width: width = length
        self.attribute["width"] = width+2
        self.widget = ttk.Combobox( parent.widget,
                                   state=state,
                                   textvariable=self.variable,
                                   values=values,
                                   **self.attribute)
        self.setScrollingAfterFrame()

        if newIndex is not None: self.widget.current(newindex=newIndex)  # Default to "Everything"
        self.setVariables()
        self.setPack(True)
        self.placement = {'side': tk.TOP, 'expand':True}
        self.settingPlacement()
        self.addWidgetToWindow()

    #Propeties established
    def get(self):
        value = self.widget.get()
        if self.formatting is not None: value = self.formatting(value)
        return value
    def set(self, value):
        self.widget.set(value)
    value = property(get, set)

    #def clear(self): self.widget.set("")
    def setAttributes( self, limitTo=None, exclude=None ):
        if len(self.dictionary) > 0:
            for keyValue, value in self.dictionary.items():
                key = keyValue.lower()
                if exclude is not None and key in exclude: continue
                if limitTo is not None and key not in limitTo: continue
                match key:
                    case 'valuesonly': self.widget.state(['readonly'])
                    case 'disable': self.widget.state(['disable'])
                    case 'enable': self.widget.state(['!disable'])
                    case 'editingok': self.widget.state(['!readonly'])
                    case 'background': self.attribute[key]=value # Different for combo
                    case 'foreground': self.attribute[key]=value # Different for combo
                    case 'bg': self.attribute['background']=value # Different for combo
                    case 'fg': self.attribute['foreground']=value # Different for combo
                    case _: super().setAttribute( key, value)

class TableComboBox( BasicWidget ):
    def __init__( self, parent, values, *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)
        # make a dictionary of self.attribute that is only for the label in the combo
        width = self.attribute.pop("width", None)
        if width is None:
            width = 10
            for item in values:
                if isinstance(item,str):
                    length = len(item)
                    if length > width: width = length
            width += 2
        self.attribute["width"] = width
        coordinates = dictionary.get('coord',None)
        (row, column) = coordinates
        if 'text' in self.dictionary:
            self.setAttributes(limitTo=('font','fg','bg','coord','text'))
            self.setAttributes(limitTo=('textfont')) # Overrides any font in the above
            self.attribute.update(self.placement)
            self.label = Label(parent, **self.attribute) # Automatically placed within parent
            self.resetDictionaries(keepDictionary=True)
            row += 1

        # make a dictionary of self.attribute that is only for the combo with new coord
        self.setAttributes(exclude=('coord','row','column','text','textfont','borderwidth','relief'))
        if 'font' in self.dictionary:
            window = self.getWindow()
            window.saveCheckboxFont(self.dictionary['font'])
        if 'background' in self.dictionary:
            window = self.getWindow()
            color = self.dictionary['background']
            color = window.colors.get(color, color)
            window.saveCheckboxBackgroundColor(color)
        self.setSpecificAttributes(coord=(row,column))

        self.widget = ttk.Combobox( parent.widget,
                                   textvariable=self.variable,
                                   values=values,
                                   **self.attribute)


        self.setVariables()
        self.settingPlacement()
        self.addWidgetToWindow()

    #Propeties established
    def get(self):
        value = self.widget.get()
        if self.formatting != None: value = self.formatting(value)
        return value
    def set(self, value):
        self.widget.set(value)
    value = property(get, set)

    #def clear(self): self.widget.set("")
    def setAttributes( self, limitTo=None, exclude=None ):
        if len(self.dictionary) > 0:
            for keyValue, value in self.dictionary.items():
                key = keyValue.lower()
                if exclude != None and key in exclude: continue
                if limitTo != None and key not in limitTo: continue
                match key:
                    case 'valuesonly': self.widget.state(['readonly'])
                    case 'disable': self.widget.state(['disable'])
                    case 'enable': self.widget.state(['!disable'])
                    case 'editingok': self.widget.state(['!readonly'])
                    case 'background': self.attribute[key]=value # Different for combo
                    case 'foreground': self.attribute[key]=value # Different for combo
                    case 'bg': self.attribute['background']=value # Different for combo
                    case 'fg': self.attribute['foreground']=value # Different for combo
                    case _: super().setAttribute( key, value)

class RadioBox( BasicWidget ):
    """Display Radio Buttons with a label of text, values list of
    each radio button label (which is its value), and grid coordinates"""
    def __init__( self, parent, values,  *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)
        # make a dictionary of self.attribute that is only for the label in the Radio Box of radio buttons
        (row, column) = self.dictionary['coord']
        vertical = self.attribute.pop('vertical',False) # Default.  Needed for setting radio button groups' direction
        #vertical = self.dictionary.get('vertical',False) # Default.  Needed for setting radio button groups' direction
        side = tk.TOP if vertical else tk.LEFT
        self.correctAnswer = self.attribute.pop('answer',None)
        size = self.attribute.pop('maxwidth', 0)
        font = self.dictionary['font'] if 'font' in self.dictionary else ("TKDefaultFont", 10)
        buttonColor = self.attribute['bg'] if 'bg' in self.attribute else self.colors["Mist"]
        self.attribute['bg']=buttonColor
        textColor = self.attribute['fg'] if 'fg' in self.attribute else self.colors["Black"]

        if 'text' in self.dictionary:
            self.setAttributes(limitTo=('font','fg','bg','text'), exclude=('textfont'))
            self.placement = {'pack':True, 'side':tk.TOP, 'anchor':tk.NW, 'expand':True, 'wraplength': size-15, 'width': size-5}
            self.attribute.update(self.placement)
            self.label = Label(parent, **self.attribute) # Automatically placed within parent

            Label(parent, text=(size-15)*" ", pack=True, side=tk.TOP, expand=False, wraplength=size, width=size-15,
                        background=buttonColor) # Automatically add a space after the question
            self.resetDictionaries(keepDictionary=True)
            self.window.root.update_idletasks()

        self.setAttributes(exclude=('coord','row','column','text','font','textfont'))
        #self.setSpecificAttributes(coord=(row,column))
        #self.setPack(side=side, expand=True)
        self.widget = parent.widget # tk.Frame(parent.widget).pack(side=side, expand=True) # , **self.attribute
        #self.setVariables()
        # , 'justify':tk.LEFT, 'wraplength':self.width-10
        # Make each radio button directly within the frame
        # #  using the frame's string var which receives the text label of the button
        # If the frame is ValidRadioGroupLabelFrame, then radio information is needed from this widget
        for value in values:
            text = value
            if self.formatting is not None: text = self.formatting(text)
            button = tk.Radiobutton(
                        self.widget,
                        variable=self.variable,
                        text=text,
                        value=value,
                        background=buttonColor,
                        foreground=textColor,
                        font=font)
            if vertical:
                button.pack(anchor=tk.W)
            else:
                button.pack(side=tk.LEFT, expand=False, padx=10)
        self.variable.set(False) # Initially, all buttons off.  Setting it here works better than earlier.
        self.addWidgetToWindow()

    def get(self):
        value = self.returnVariableValueBasedOnType()
        if value == '0': value = None
        return value
    def set(self, value):
        return # No setting the radio button
    value = property(get, set)

    # Individual elements set
    def clear(self):
        self.variable.set(False)
    def underline( self, value): self.label.underline=value
    def setAttributes( self, limitTo=None, exclude=None ):
        if len(self.dictionary) > 0:
            for keyValue, value in self.dictionary.items():
                key = keyValue.lower()
                if exclude is not None and key in exclude: continue
                if limitTo is not None and key not in limitTo: continue
                if key == 'underline': self.underline( value)
                elif key == 'vertical': pass # Only used by setvariables()
                else: super().setAttribute(key, value)

class SpinBox( BasicWidget ):
    def __init__( self, parent,  *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)
        # make a dictionary of self.attribute that is only for the label in the SpinBox
        self.group = [] # Used to coordinate a series of spinboxes
        (row, column) = self.dictionary['coord']
        if 'text' in self.dictionary:
            self.setAttributes(limitTo=('font','fg','bg','coord','text'))
            self.setAttributes(limitTo=('textfont')) # Overrides any font in the above
            self.attribute.update(self.placement)
            self.label = Label(parent, **self.attribute) # Automatically placed within parent
            self.resetDictionaries(keepDictionary=True)
            row += 1

        # make a dictionary of self.attribute that is only for the Spin Box
        self.setSpecificAttributes(from_="-Infinity", to="Infinity", increment=1) # Default values
        self.setAttributes(exclude=('coord','text','textfont'))
        self.setSpecificAttributes(row=row, column=column, sticky='fullwidth')
        self.widget = tk.Spinbox( parent.widget, textvariable=self.variable, **self.attribute )
        self.variable.set(value='')
        self.setVariables()
        self.settingPlacement()
        self.addWidgetToWindow()

    #Propeties established
    def get(self):
        value = self.returnVariableValueBasedOnType()
        return value
    def set(self, value):
        self.variable.set(value)
    value = property(get, set)

    # Individual elements set
    def setFrom( self, value): self.attribute['from_']=value
    def setTo( self, value): self.attribute['to']=value
    def setIncrement( self, value): self.attribute['increment']=value
    def setAttributes( self, limitTo=None, exclude=None ):
        if len(self.dictionary) > 0:
            for keyValue, value in self.dictionary.items():
                key = keyValue.lower()
                if exclude is not None and key in exclude: continue
                if limitTo is not None and key not in limitTo: continue

                if key == 'from' or key == 'from_':
                    self.setFrom(value)
                    self.setFormatType(value)
                elif key == 'to':
                    self.setTo(value)
                    self.setFormatType(value)
                elif key == 'increment':
                    self.setIncrement(value)
                    self.setFormatType(value)
                elif key == 'debugging':
                    (theFrom, theTo, increment) = value
                    self.setFrom(theFrom)
                    self.setTo(theTo)
                    self.setIncrement(increment)
                else: super().setAttribute(key, value)

class BasicText( BasicWidget ): # Not instantiated
    allowedAttributes = ('bg','background','bd','cursor','exportselection','font','fg','foreground','height',
                        'highlightbackground','highlightcolor','highlightthickness',
                        'padx','pady','relief','spacing1','spacing2','spacing3',
                        'state','width','wrap')

    def __init__( self, parent, *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)
        self.setAttributes(limitTo=('x','y'))
        self.underline=0
        self.height=1
        self.width=60
        self.justify=False

    def clear(self):
            self.widget.delete('1.0', tk.END)
    def setUnderline( self, value):
        self.underline=int(value)
    def setWrap( self, value):
        checking = value.lower()
        if checking in ('none','char','word'):
            self.attribute['wrap']= (value == True)
    def setMaxUndo(self, value):
        if isinstance( value, int) and value >= 0:
            self.attribute['maxundo']=int(value)
    def setTextHeight(self, value):
        self.attribute['height']=int(value)
    def setTextWidth(self, value):
        self.attribute['width']=int(value)
    def setUndo( self, value):
        self.attribute['undo']= (value == True)
    def setSpacing1( self, value):
        if isinstance( value, int) and value >= 0:
            self.attribute['spacing1']=int(value)
    def setSpacing2( self, value):
        if isinstance( value, int) and value >= 0:
            self.attribute['spacing2']=int(value)
    def setSpacing3( self, value):
        if isinstance( value, int) and value >= 0:
            self.attribute['spacing3']=int(value)
    def setReadOnly(self, value):
        self.readonly=bool(value) # self.widget.config(state=tk.DISABLED)

    def setAttributes( self, limitTo=None, exclude=None ):
        if len(self.dictionary) > 0:
            for keyValue, value in self.dictionary.items():
                key = keyValue.lower()
                if exclude is not None and key in exclude: continue
                if limitTo is not None and key not in limitTo: continue
                match key:
                    case 'underline': self.setUnderline( value)
                    case 'undo': self.setUndo( value)
                    case 'maxundo': self.setMaxUndo( value)
                    case 'wrap': self.setWrap( value)
                    case 'height': self.setTextHeight( value)
                    case 'width': self.setTextWidth( value)
                    case 'spacing1': self.setSpacing1( value)
                    case 'spacing2': self.setSpacing2( value)
                    case 'spacing3': self.setSpacing3( value)
                    case _: super().setAttribute( key, value)

    def setVariables( self, limitTo=None, exclude=None ):
        if len(self.dictionary) > 0:
            for keyValue, value in self.dictionary.items():
                key = keyValue.lower()
                if exclude is not None and key in exclude: continue
                if limitTo is not None and key not in limitTo: continue
                match key:
                    case 'readonly':
                        readOnlyState = tk.NORMAL if value else tk.DISABLED
                        self.widget.config(state=readOnlyState)
                    case 'justify':
                        self.widget.tag_configure('justify', justify=value) # Make a tag named for the justification requested
                        self.justify = True # the tag will be used when the insert() method is called
                    case _: super().setVariable( key, value)

class SimpleText( BasicText ):
    def __init__( self, parent, *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)
        self.setSpecificAttributes(height=1)
        allowedAttributes = self.copyAllowedAttributes(BasicText.allowedAttributes)

        self.setScrollingFrame(parent.widget, kind="vertical")
        self.widget = tk.Text( parent.widget, **allowedAttributes)
        self.setScrollingFrameAfterFrame()

        text = "" if not 'text' in dictionary else dictionary['text']
        self.set(text)
        self.setVariables()
        self.settingPlacement()

    #Propeties established
    def get(self, position='1.0'):
        text = self.widget.get(position, 'end-1c')
        return( text[:-1])
    def set(self, value, position='1.0'):
        if self.readonly:
            self.widget.config(state=tk.NORMAL)
            self.widget.delete(position, tk.END)
            if self.justify:
                self.widget.insert(position, value, 'justify')
            else:
                self.widget.insert(position, value)
            self.widget.config(state=tk.DISABLED)
        else:
            self.widget.delete(position, tk.END)
            if self.justify:
                self.widget.insert(position, value, 'justify')
            else:
                self.widget.insert(position, value)
    value = property(get, set)

class TextRedirectorClass():
    """ Class to redirect stdout or stderr to a Tkinter Text widget.
    Could be wrapped into a SmartText object or GenericText object."""
    # ex: sys.stdout = TextRedirector(self, sys.stdout)
    # ex: sys.stderr.reset()
    # see: https://stackoverflow.com/questions/12351786/how-to-redirect-print-statements-to-tkinter-text-widget
    def __init__(self, textBox, standard):
        """ Initialize the redirector with the textbox.widget to write to, the standard stream, and a tag for text styling."""
        if standard is sys.stdout:
            self.tag = "stdout"
        elif standard is sys.stderr:
            self.tag = "stderr"
        elif standard is sys.stdin:
            self.tag = "stdin"
        else:
            self.tag = "other"
        self.widget = textBox.widget
        self.standard = standard # Save for a later reset()

    def write(self, string):
        """ Write the string to the widget with the specified tag. Note .config() changes state."""
        self.widget.configure(state="normal")
        self.widget.insert("end", string, (self.tag,))
        self.widget.configure(state="disabled")

    def reset(self): # ex: sys.stdout = stdout.reset()
        """ Reset to the standard stream and return it."""
        self.widget.configure(state="normal")
        return self.standard

class TextBox( BasicText ):
    def __init__( self, parent,  *dictionaries, **dictionary):
        self.frameWidget = None
        self.xscrollWidget = None
        self.yscrollWidget = None
        super().__init__(parent,  *dictionaries, **dictionary)
        centerText = self.dictionary.pop('centertext', False)
        self.hint  = self.dictionary.get('hint', "") # Stores any hint text
        self.scrolling = self.dictionary.get('scrolling',False)
        self.readOnly = self.dictionary.get('readonly',False)
        text = self.dictionary.get('text', "")
        kind = self.dictionary.get('kind', 'Both')
        packing = self.dictionary.get('pack', False)
        self.attribute = self.dictionary | {'undo':True,'maxundo':100,'wrap':False,
                              'wrap':'word','spacing1':2,'spacing2':2,'spacing3':2}
        self.setAttributes()
        allowedAttributes = self.copyAllowedAttributes( BasicText.allowedAttributes)
        if self.scrolling:
            self.setScrollingFrame(parent.widget, kind=kind)
            self.widget = tk.Text( self.frameWidget, **allowedAttributes)
            self.widget.pack()
            self.setScrollingAfterFrame()
        elif packing:
            self.grid = False
            self.pack = True
            self.widget = tk.Text( parent.widget, **allowedAttributes)
        else:
            self.widget = tk.Text( parent.widget, **allowedAttributes)
            coordinates = self.dictionary.get("grid",(0,0))
            self.setCoord(coordinates)
            self.widget.grid_columnconfigure(0, weight = 1)
            self.widget.grid_rowconfigure(0, weight = 1)
          
        if centerText:
            self.setCenter(text)
        else:
            self.set(text)
        self.setVariables()
        if not self.readOnly:
            self.widget.config(state=tk.NORMAL)
        self.settingPlacement()
            
    def redirectStandard(self, standard):
        """ Initialize the redirector class with the textbox widget to write to, the standard stream to send to the textBox, 
        and a tag for text styling. Yes, pass in self. This returns the instantiated class with specifics of the standard being redirected"""
        return TextRedirectorClass( self, standard)

    def setScrollingFrame(self, parentWidget, kind="both", frameWidget=None):
        """ Set up the scrolling frame for the widget.  This is used for all widgets.
        """
        if self.scrolling:
            self.kind = kind
            self.frameParent = parentWidget
            if frameWidget is None:
                self.frameWidget = ttk.Frame(parentWidget)
                #self.frameWidget.pack(expand = True, fill = tk.BOTH)
                self.frameWidget.grid() # grid_columnconfigure()
            else:
                self.frameParent = parentWidget

            if kind == "both" or kind == "horizontal":
                self.xscrollWidget = ttk.Scrollbar(self.frameWidget, orient = tk.HORIZONTAL)
                self.xscrollWidget.pack(side=tk.BOTTOM, fill=tk.X)
                self.attribute['xscrollcommand'] = self.xscrollWidget.set

            if kind == "both" or kind == "vertical":
                self.yscrollWidget = ttk.Scrollbar(self.frameWidget, orient=tk.VERTICAL)
                self.yscrollWidget.pack(side=tk.RIGHT, fill=tk.Y)
                self.attribute['yscrollcommand'] = self.yscrollWidget.set

    def setScrollingAfterFrame(self):
        if self.scrolling:

            self.setPack(True)
            self.placement = dict(fill=tk.BOTH, expand=True)

            if self.kind == "both" or self.kind == "horizontal":
                self.xscrollWidget.configure(command=self.widget.xview)

            if self.kind == "both" or self.kind == "vertical":
                self.yscrollWidget.configure(command=self.widget.yview)

    #Propeties established
    def get(self):
        text = self.widget.get('1.0', 'end-1c')
        if len(self.hint) > 0:
            if text == self.hint: text = ''
        return( text)
    def set(self, value):
        if self.readonly: self.widget.config(state=tk.NORMAL)
        self.widget.delete('1.0', tk.END)
        self.widget.insert('1.0',value)
        if self.readonly: self.widget.config(state=tk.DISABLED)
    def setCenter(self, value):
        if self.readonly: self.widget.config(state=tk.NORMAL)
        self.widget.tag_configure("center", justify="center")
        self.widget.delete('1.0', tk.END)
        self.widget.insert('1.0',value,'center')
        if self.readonly: self.widget.config(state=tk.DISABLED)
    def clear(self):
        if self.readonly: self.widget.config(state=tk.NORMAL)
        self.widget.delete('1.0', tk.END)
        if self.readonly: self.widget.config(state=tk.DISABLED)
    def add(self,value,moveToEnd = True):
        if self.readonly: self.widget.config(state=tk.NORMAL)
        self.widget.insert(tk.END, value)
        self.widget.location = tk.END # Set the cursor to the end of the text
        if moveToEnd: self.widget.see(tk.END) # Scroll to the end of the text
        if self.readonly: self.widget.config(state=tk.DISABLED)
    def addBold(self,value,moveToEnd = True):
        if self.readonly: self.widget.config(state=tk.NORMAL)
        self.widget.tag_configure('bold', font=('Calibri', 12, 'bold'))
        self.widget.insert(tk.END, value, 'bold')
        #self.widget.insert(tk.END, value)
        self.widget.location = tk.END # Set the cursor to the end of the text
        if moveToEnd: self.widget.see(tk.END) # Scroll to the end of the text
        if self.readonly: self.widget.config(state=tk.DISABLED)
    def beginning(self):
        self.widget.see('1.0') # Scroll to the beginning of the text
    def ending(self):
        self.widget.see( tk.END) # Scroll to the beginning of the text
    def setHint( self, value):
        self.hint = value
    def setReadOnly( self, value):
        self.readonly = bool(value)
    def setAttributes( self, limitTo=None, exclude=None ):
        if len(self.dictionary) > 0:
            for keyValue, value in self.dictionary.items():
                key = keyValue.lower()
                if exclude is not None and key in exclude: continue
                if limitTo is not None and key not in limitTo: continue
                if key == 'hint': self.setHint(value)
                elif key =='initialtext': pass # All these are needed but used by setVariables()
                elif key =='scrolling': pass
                elif key =='scrollvertical': pass
                elif key =='scrollhorizontal': pass
                elif key =='readonly': self.setReadOnly(value)
                elif key =='fg': self.setFg(self.colors.get(value,value))
                elif key =='foreground': self.setForeground(self.colors.get(value,value))
                elif key =='bg': self.setBg(self.colors.get(value,value))
                elif key =='background':self.setBackground(self.colors.get(value,value))
                else: super().setAttribute(key, value)

class CheckBoxes( BasicWidget):
    """Display chekboxes with a label of text, values dictionary of
    each checkbox labe and its initial Boolean value, and grid coordinates"""
    def __init__( self, parent, values,  *dictionaries, **dictionary):
        super().__init__(parent,  *dictionaries, **dictionary)
        
        (row, column) = self.dictionary['coord']
        vertical = self.attribute.pop('vertical',False) # Default.  Needed for setting radio button groups' direction
        side = tk.TOP if vertical else tk.LEFT
        self.correctAnswer = self.attribute.pop('answer',None)
        self.preset = [] # List of optional preset values
        self.allOffBox = None
        self.allOnBox = None
        self.elements = dict() # Required for controlling individual elements
        size = self.attribute.pop('maxwidth', 0)

        if 'text' in dictionary:
            self.setAttributes(limitTo=('font','fg','bg','coord','text'))
            self.setAttributes(limitTo=('textfont')) # Overrides any font in the above
            self.placement = {'pack':True, 'side':side, 'expand':True, 'wraplength': size-15, 'width': size-5, 'justify':tk.LEFT}
            self.attribute.update(self.placement)
            self.label = Label(parent, **self.attribute) # Automatically placed within parent
            self.resetDictionaries(keepDictionary=True)
            row += 1

        # make a dictionary of self.attribute that is only for the frame of the check boxes
        self.setAttributes(exclude=('coord','row','column','text','font','textfont'))
        self.widget = parent.widget # tk.Frame(parent.widget, **self.attribute)

        # Make each check box in the values list directly within the frame.  For a single checkbox,
        # place the name as the only string in a list.
        font = self.dictionary['font'] if 'font' in self.dictionary else ("TKDefaultFont", 10)
        count = 0
        for value in values:
            initialSetting = False
            if count < len(self.preset):
                initialSetting = (self.preset[count] == True)
                count += 1
            text = value
            if self.formatting is not None: text = self.formatting(text)
            checkboxVariable = tk.BooleanVar(value=initialSetting)
            labelVariable = tk.StringVar(value=text)
            self.elements[text] = checkboxVariable
            button = tk.Checkbutton(
                        self.widget,
                        variable=checkboxVariable,
                        textvariable=labelVariable,
                        font=font)
            if vertical:
                button.pack(anchor=tk.W) #side=tk.TOP, expand=True)
            else:
                button.pack(side='right', expand=True)
        self.setVariables()
        self.addWidgetToWindow()

    def get(self):
        data = dict()
        count = 0
        for key,variable in self.elements.items():
            try:
                value = bool(variable.get())
                name = key
            except:
                name = f"Missing_{count}"
                value = None
            data[name] = value
            count += 1
        return data
    def set(self, value):
        if isinstance(value, tuple):
            (name, value) = value
            for key,variable in self.elements.items():
                if key == name:
                    variable.set(value)
                    break
    value = property(get, set)

    # Individual elements set
    def clear(self):
        for checkbox in self.elements.values():
            checkbox.set(False)
    def setAllBoxes( self, value):
        if (value == True):
            if self.allOnBox is not None and self.allOnBox.get() == True:
                for checkbox in self.widget.children:
                    if self.allOffBox is checkbox:
                        checkbox.variable.set(False)
                        continue
                    checkbox.variable.set(True)
        elif self.allOffBox is not None and self.allOffBox.get() == True:
            for checkbox in self.widget.children:
                checkbox.variable.set(False)
    def setAllOnBox(self,  value):
        for checkbox in self.widget.children:
            if checkbox.textvariable.get() == value:
                self.allOnBox = checkbox
                checkbox.command = self.setAllBoxes(True)
                break
    def setAllOffBox(self,  value):
        for checkbox in self.widget.children:
            if checkbox.textvariable.get() == value:
                self.allOffBox = checkbox
                checkbox.command = self.setAllBoxes(False)
                break
    def onValue( self, value): self.widget.onvalue=value
    def offValue( self, value): self.widget.offvalue=value
    def setAttributes( self, limitTo=None, exclude=None ):
        if len(self.dictionary) > 0:
            for keyValue, value in self.dictionary.items():
                key = keyValue.lower()
                if exclude is not None and key in exclude: continue
                if limitTo is not None and keyValue not in limitTo: continue
                match key:
                    case 'onvalue': self.onValue( value)
                    case 'offvalue': self.offValue( value)
                    case 'allset': self.setAllOnBox(value)
                    case 'alloff': self.setAllOffBox(value)
                    case 'preset':
                        if isinstance( value, list): self.preset = value
                    case _: super().setAttribute( key, value)
    def setVariables( self, limitTo=None, exclude=None ):
        if len(self.dictionary) > 0:
            for keyValue, value in self.dictionary.items():
                key = keyValue.lower()
                if exclude is not None and key in exclude: continue
                if limitTo is not None and keyValue not in limitTo: continue
                if key == 'setallon': self.setAllOnBox( value)
                elif key == 'setalloff': self.setAllOffBox( value)

class Button( BasicWidget):
    """Display button with an optional label of text/graphics and grid coordinates"""
    def __init__( self, parent,  *dictionaries, **dictionary):
        super().__init__(parent,  *dictionaries, **dictionary)
        self.holdPush = False
        self.usingPicture = False # Non-False is the url of the picture
        self.holdColor = None
        self.holdFontColor = None
        self.originalColor = None
        self.originalFontColor = None
        self.default='active'
        #self.setAttributes(exclude=('sticky')) # Doubles actions, everythingelse was already set
        if 'image' in self.attribute:
            self.fullpath = self.attribute['image']
            self.image = tk.PhotoImage(file=self.fullpath)
            self.attribute['image'] = self.image
        self.widget = tk.Button(parent.widget, **self.attribute)
        if self.command is not None:
            self.setCommand(self.command) # Command can't be set until the widget already exists
        self.setVariables()
        self.settingPlacement()

    #Propeties established
    def get(self):
        value = self.widget.cget('text')
        return value
    def set(self, value):
        self.widget.config(text=value)
    value = property(get, set)

    def setVariable( self, key, value ):
        match key:
            case 'holdpush': self.holdPush =  value
            case 'usingpicture': self.usingPicture = value
            case 'holdcolor': self.holdColor = self.colors.get(value, value)
            case 'holdfontcolor': self.holdFontColor = self.colors.get(value, value)
            case 'originalcolor': self.originalColor = self.colors.get(value, value)
            case 'originalfontcolor': self.originalFontColor = self.colors.get(value, value)
            case 'default': self.default= value
            case _: super().setVariable( key, value)

    def setPackSides( self, value):
        side = self.defineSidePlacement(value)
        self.placement['side']=side

    # Individual elements set
    def setAttributes( self, limitTo=None, exclude=None ):
        if len(self.dictionary) > 0:
            for keyValue, value in self.dictionary.items():
                key = keyValue.lower()
                if exclude is not None and key in exclude: continue
                if limitTo is not None and keyValue not in limitTo: continue
                match key:
                    case 'side': self.setPackSides(value)
                    case _: super().setAttribute( key, value)

############################## Helper classes ##############################

# Provide a greyed-out suggestion of what to type.  Only available in the text box
#   because the entry widget does not support tags.  In progress ....
class SuggestTextBoxMixin():
    def __init__(self, parent, *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)

        self.suggestList = []
        self.lastUserEntered = ""
        self.lastSuggestion = ""
        self.widget.bind('<<Modified>>', self._on_modified)
        self.widget.tag_configure('suggest', foreground=self.colors["LightGray"])
        self.widget.tag_configure('entered', foreground=self.colors["Black"])

    def _on_modified(self):
        if self.edit_modified():
            content = self.get('1,0', 'end-1chars')
            contentLength = len(content)
            if contentLength == 0:
                self.variable.tag_delete('suggest', 'entered')

            elif len(self.suggestList) > 0:
                self.variable.tag_delete('suggest', 'entered')
                self.variable.delete(0, tk.END)

                matching = [ x for x in self.suggestList
                        if x.startswith(content) ]
                itemsMatched = len(matching)
                if itemsMatched == 0: # No match, keep all content as entered and no grey text
                    self.variable.insert('end', content, 'entered')
                    self.widget.icursor('end')
                elif itemsMatched == 1: # Single match, keep all content as entered and no grey text
                    self.variable.insert('end', matching[0], 'entered')
                    self.widget.icursor('end')
                else:
                    self.variable.insert('end', content, 'entered')
                    self.variable.insert('end', matching[0][9:], 'suggest')
                    self.widget.icursor('end')

            self.edit_modified(False)

class _controlClass(): # Used by ControlMixin
    def __init__(self, name, frameWidget, controlType, *widgets):
        self.name = name
        self.frameWidget = frameWidget
        self.currentStatus = False
        self.controlType = controlType
        self.controlList = widgets

class ControlMixin( BasicWidget ): # Only tested on checkboxes. May not work on other widgets (buttons, radioboxes).
    # Requires self.elements dictionary to hold widget names and tk. values (check boxes have this already)
    def __init__(self, parent, *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)
        self.controlDictionary = dict()

    def setWidgetControlList(self, controlType, *widgets):
        usedWidgets = []
        window = self.getWindow()
        allWidgets = window.getWidgetChildren()
        for eachWidget in widgets:
            if isinstance(eachWidget, Frame) or isinstance(eachWidget, LabelFrame):
                for possibleWidget in allWidgets: # Find all child widgets of the frame
                    if possibleWidget.parent.widget == eachWidget.widget:
                        usedWidgets.append(possibleWidget)
            else:
                usedWidgets.append(eachWidget)
        frameWidget = widgets[0]
        controlInfo = _controlClass(self.name, frameWidget, controlType.lower(), *usedWidgets)
        self.controlDictionary[self.name] = controlInfo
        frameTextVariable = self.elements[self.name]
        frameTextVariable.trace_add('write', self.toggleControledWidget)

    def manuallyToggleControledWidget(self):
        for widgetName, controledWidget in self.controlDictionary.items():
            if  widgetName == self.name:
                controledWidget.currentStatus = not controledWidget.currentStatus
                if controledWidget.controlType == 'enable':
                    if controledWidget.currentStatus:
                        self.setDisableByList(controledWidget.controlList)
                    else:
                        self.setEnableByList(controledWidget.controlList)
                elif controledWidget.controlType == 'visible':
                    if controledWidget.currentStatus:
                        controledWidget.frameWidget.setInvisible()
                    else:
                        controledWidget.frameWidget.setVisible()

    def toggleControledWidget(self, variable_name, *_):
        for widgetName, controledWidget in self.controlDictionary.items():
            eachWidget = self.elements[widgetName]
            widgetWindowName = eachWidget._name
            if  widgetWindowName == variable_name:
                controledWidget.currentStatus = not controledWidget.currentStatus
                if controledWidget.controlType == 'enable':
                    if controledWidget.currentStatus:
                        self.setDisableByList(controledWidget.controlList)
                    else:
                        self.setEnableByList(controledWidget.controlList)
                elif controledWidget.controlType == 'visible':
                    if controledWidget.currentStatus:
                        controledWidget.frameWidget.setInvisible()
                    else:
                        controledWidget.frameWidget.setVisible()
                canvas = self.getCanvas()
                if canvas is not None: canvas.updateScrollRegion()

    def setStatus(self, name, value=False):
        newValue = not bool(value) # Forces a change to the new value
        control = self.controlDictionary[name]
        control.currentStatus = newValue
        variable = self.elements[name]
        variable.set(value)

    def clear(self):
        for item in self.elements.values():
            for control in self.controlDictionary.values():
                control.currentStatus = True # Forces a change to False
            item.set(False)

############################## Validation classes ##############################
class FiveCharEntry(Entry):
    def __init__(self, parent, *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)
        self.error = tk.StringVar()
        self.widget.configure(
            validate='all',
            #validatecommand=(self.register(self.validate), '%P', '%s', '%S', '%V', '%i', '%d'),
            #invalidcommand=(self.register(self.invalid), '%P', '%s', '%S', '%V', '%i', '%d')
            validatecommand=(self.widget.register(self._on_validate), '%P'),
            invalidcommand=(self.widget.register(self._on_invalid), '%P')
        )

    def _on_validate(self, proposed):
        if len(proposed) <= 5:
            return True
        else:
            #self.error.set('Too many characters')
            return False

    def _on_invalid(self, proposed):
        self.error.set(f'{proposed} is too long, only 5 chars allowed')

class ValidityBasisMixin():
    def __init__(self, parent, *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)
        if self.label is None:
            self._originalLabelText = ""
        else:
            self._originalLabelText = self.label.get()
        self._errorState = False
        self.currentValue = None
        action, result, current, index, char, event = '%d','%P','%s','%i','%S','%V'
        self.widget.configure(
            validate='all', # after idle {%W config -validate %v}
            validatecommand=(self.widget.register(self._on_validate), action, result, current, index, char, event),
            invalidcommand=(self.widget.register(self._on_invalid), action, result, current, index, char, event)
        )

    def _turnOffErrorColors(self, color="Black"):
        #print(f"Error colors -off- with {color}")
        goodColor = self.colors.get(color, color)
        self.widget.config(foreground=goodColor)
        if self.label is not None and self.label.widget is not None:
            self.label.widget.config(foreground=color)

    def _turnOnErrorColors(self, color="Red"):
        #print(f"Error colors ON with {color}")
        goodColor = self.colors.get(color, color)
        self.widget.config(foreground=goodColor)
        if self.label is not None and self.label.widget is not None:
            self.label.widget.config(foreground=color)

    def _toggle_error( self, error=''):
        self.currentValue = self.get()

        errorMessageprovided = len(error) > 0 # Assume a new error state if there is an error message
        if errorMessageprovided:
            #print(f"{self.name}: value: {currentValue}, new error for new?={errorMessageprovided}, current?={self._errorState}, error message provided={error} to ValidityBasisMixin")
            if not self._errorState: self._turnOnErrorColors()
            self._errorState = True
            self.widget.icursor(tk.END)
            self.set('')
            self.set(self.currentValue)
            self.widget.icursor(tk.END)
            if self.label is not None and self.label.widget is not None:
                newLabelMessage = f"{error} {self._originalLabelText}"
                self.label.widget.config(text=newLabelMessage)

        elif self._errorState: # otherwise, if there was an error but not now
            #print(f"{self.name}: value: {currentValue}, error now over for new?={errorMessageprovided}, current?={self._errorState}, no message provided to ValidityBasisMixin")
            self._turnOffErrorColors(self.canvas.colors["Blue"])
            self._errorState = False
            self.set(self.currentValue)
            if self.label is not None and self.label.widget is not None:
                self.label.widget.config(text=self._originalLabelText)

        else: # No current error and no previous error
            #print(f"{self.name}: value: {currentValue}, never was an error for new?={errorMessageprovided}, current?={self._errorState}, no message provided to ValidityBasisMixin")
            self._turnOffErrorColors()
            self.set(self.currentValue)

    # Override with specific validity method
    def _on_validate(self, action, result, current, index, char, event):
        valid = True
        return valid

    # Override with specific error checking
    def errorCheck(self):
        pass

    # Override with specific invalidity method (this works for many methods)
    def _on_invalid(self, action, result, current, index, char, event):
        pass
    # if event != 'key':
    #         self._toggle_error('Invalid')

    # Override the clear method to additionally clear the error state
    def clear(self):
        self._turnOffErrorColors()
        super().clear()

class UsDateMixin(ValidityBasisMixin):
    def __init__(self, parent, *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)

    # Combine classes ValidityMixin and Entry (ValidityMixin acts like an Interface)
    #  ValidityMixin is a general purpose class that can be used for almost any validation
    #  The code below is specific to US dates on any input widget.
    #  Entry class is used here, but any input widget will work for a different specific class
    def _on_validate(self, action, result, current, index, char, event):

        # ISO dates only need digits and hyphens
        valid = True
        if event == 'key':
            self._toggle_error()
            if action == '0':
                valid = True
            elif index in ('0', '1', '3', '4', '6', '7', '8', '9'):
                valid = char.isdigit()
            elif index in ('2', '5'):
                valid = char in ('-', '/')
            elif index >= '10':  # Too long
                valid = False
        elif event == 'focusout':
            text = self.get()
            if len(text) == 0:
                self._toggle_error()
            else:
                try:
                    datetime.datetime.strptime(text, '%m-%d-%Y')
                except ValueError:
                    valid = False
                else:
                    valid = True
                    self._toggle_error()
        return valid

    def errorCheck(self):
        text = self.get()
        self._toggle_error()
        try:
            datetime.datetime.strptime(text, '%m-%d-%Y')
        except ValueError:
            self._toggle_error('Invalid')

class NonblankMixin(ValidityBasisMixin):
    def errorCheck(self):
        text = self.get()
        self._toggle_error()
        if len(text) == 0:
            self._toggle_error('Missing')

# Provide a hint in the entry or text box that disappears when the user starts typing
class HintMixin(ValidityBasisMixin):
    def __init__(self, parent, *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)
        self.widget.bind('<FocusIn>', self.remove_temp_hint)
        self.widget.bind('<FocusOut>', self.set_temp_hint)
        self.set_temp_hint()

    def remove_temp_hint(self, e=None):
        content = self.get() # If the current value is the hint, the value is ""
        if len(self.hint) > 0 and (content == self.hint or content == ''):
            self.widget.delete(0, tk.END)
            self.widget.configure(foreground="#000000") # Black
    def set_temp_hint(self, e=None):
        contents = self.get()
        if len(self.hint) > 0 and len(contents) == 0:
            color = self.widget.cget('background')
            if color == "#ffffff": # White
                self.widget.configure(foreground="#cdcdcd") # Grey
            else:
                self.widget.configure(foreground="#ffffff")  # White
            self.widget.delete(0, tk.END)
            self.variable.set(self.hint)
            self.widget.icursor(0)

    # Override the clear method to additionally set any temporary hint
    def clear(self):
        super().clear()
        self.set_temp_hint()

class IsoDateMixin(ValidityBasisMixin):
    def _on_validate(self, action, result, current, index, char, event):

        # ISO dates only need digits and hyphens
        valid = True
        if event == 'key':
            self._toggle_error()
            if action == '0':
                valid = True
            elif index in ('0', '1', '2', '3', '5', '6', '8', '9'):
                valid = char.isdigit()
            elif index in ('4', '7'):
                valid = char == '-'
        elif event == 'focusout':
            text = self.get()
            if len(text) == 0:
                self._toggle_error()
            else:
                try:
                    datetime.datetime.strptime(text, '%Y-%m-%d')
                except ValueError:
                    valid = False
                else:
                    valid = True
                    self._toggle_error()
        return valid

    def errorCheck(self):
        text = self.get()
        self._toggle_error()
        if len(text) == 0:
            self._toggle_error('Missing')
        else:
            try:
                datetime.datetime.strptime(text, '%Y-%m-%d')
            except ValueError:
                self._toggle_error('Invalid')

class NumberMixin(ValidityBasisMixin):
    def _focus_check(self, valueToCheck=None):
        valid = True
        if valueToCheck is None:
            textOrNumber = self.get()
        else:
            textOrNumber = valueToCheck
        if isinstance( textOrNumber, str):
            if len(textOrNumber) == 0:
                self._toggle_error()
                return valid
        amount = math.nan
        try:
            if isinstance(self.formatType, tk.DoubleVar):
                amount = float(textOrNumber)
            else:
                amount = int(textOrNumber)
        except ValueError:
            valid = False
        else:
            try:
                low = self.widget.cget('from')
                high = self.widget.cget('to')
                if amount < low or amount > high:
                    valid = False
                else:
                    valid = True
                    self._toggle_error()
            except:
                valid = True
                self._toggle_error()
        return valid

    def _on_validate(self, action, result, current, index, char, event):

        # ISO dates only need digits and hyphens
        valid = True
        if event == 'key':
            self._toggle_error()
            if action == '0': # Deletion
                valid = True
            elif char in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9'):
                valid = True
            elif char in ('.'):
                valid = isinstance(self.formatType, tk.DoubleVar)
            elif index in ('0'):
                valid = char == '-'
            else:
                valid = False
            if valid and self._errorState:
                _ = self._focus_check(result)
        elif event in ('focusout','focusin'):
            valid = self._focus_check()
        elif event == 'forced':
            _ = self._focus_check(result)
        return valid

    def errorCheck(self):
        textOrNumber = self.get()
        self._toggle_error()
        if textOrNumber is None:
            pass
        elif len(textOrNumber) == 0:
            self._toggle_error('Missing')
        else:
            valid = self._focus_check(textOrNumber)
            if not valid:
                self._toggle_error('Invalid')

class ComboBoxMixin(ValidityBasisMixin):
    def _on_validate(self, action, result, current, index, char, event):
        valid = True
        currentValue = self.get()

        if event == 'key':
            #print(f"Key event for {self.name}: value: {currentValue}")
            self._toggle_error()
            if action == '0':
                return True # Delete
            if len(result) == 0:
                return True

            # For a key event (not delete) and text exists, check for a beginning-match from available choices
            availableChoices = self.widget.cget('values')
            matchingList = [ x for x in availableChoices if x.lower().startswith(result.lower()) ]
            length = len(matchingList)
            if length == 0:
                valid = False
            elif length == 1: # Found a match, put the whole match into the editing area
                self.set(matchingList[0])
                self.widget.icursor(tk.END)

        elif event == 'focusin':
            #print(f"Focus in event for {self.name}: value: {currentValue}")
            self.errorCheck()

        elif event == 'focusout':
            #print(f"Focus out event for {self.name}: value: {currentValue}")
            self.errorCheck()

        return valid

    # Check if there is an input error ...
    def errorCheck(self):
        currentValue = self.get()

        # No result provided
        if len(currentValue) == 0:
            self._toggle_error('Missing')

        # Otherwise, something was provided
        else:
            currentChoices = self.widget.cget('values')
            matchingList = [ x for x in currentChoices if x.lower() == currentValue.lower() ]
            itemsMatchedInList = len(matchingList)

            # If the result was not a single pick from the list, it is invalid
            if itemsMatchedInList != 1:
                self._toggle_error('Invalid')

            # if a possibly correct answer was provided...
            elif self.correctAnswer is not None:
                if matchingList[0] == self.correctAnswer:
                    self._toggle_error()
                else:
                    self._toggle_error('Incorrect')

class PasswordMixin(ValidityBasisMixin):
    def __init__(self, parent, *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)
        self.widget.config(show='•') # Show an optional dot instead of the text
        self._password = ""
        self.variable.trace_add('write', self._on_edit)
        self.widget.bind('<FocusOut>', self._focus_out)

    def _on_validate(self, action, result, current, index, char, event):
        # Passwords have no immediate restrictions on characters inputted and they show the spot character
        valid = True
        if event == 'key':
            self._toggle_error()
            if action == '0': # Delete
                if len(self._password) > 1:
                    currentIndex = int(index)
                    self._password = self._password[:currentIndex] + self._password[currentIndex+1:]
                else:
                    self._password = ""
            else:
                currentIndex = int(index)
                if currentIndex < len(current):
                    self._password = self._password[:currentIndex] + char + self._password[currentIndex:]
                else:
                    self._password += char
        elif event == 'focusout':
            valid = True
            # Check against regex
            if len(self._password) > 0:
                # ERegex pattern is r"^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?!.*\s)(?=.*[-@#$%*]).{8,}$"
                if len(self.regexFormat) > 0:
                    match = re.match(self.regexFormat, self._password)
                    if not bool(match):
                        self._toggle_error('Invalid')
        return valid

    # Change past charaters to bullets, leaving just the last char visible
    def _on_edit(self, *_):
        visiblePassword = self.variable.get()
        length = len(visiblePassword)
        if length > 1:
            newPassword = '•'*(length-1) + visiblePassword[-1]
            self.variable.set(newPassword)

    # Change all charaters to bullets
    def _focus_out(self, *_):
        visiblePassword = self.variable.get()
        length = len(visiblePassword)
        if length > 0:
            newPassword = '•'*(length)
            self.variable.set(newPassword)

    def errorCheck(self):
        self._toggle_error()
        if len(self._password) == 0:
            self._toggle_error('Missing')
        else:
            match = re.match(self.regexFormat, self._password)
            if not bool(match):
                self._toggle_error('Invalid')

class ControlSpinBoxMixin(NumberMixin ):
    def __init__(self, parent, *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)

    def minimumChange(self, *_):
        self._toggle_error()
        amountText = self.get()
        low = self.group[0].get()
        if amountText is not None and len(amountText) > 0 and low is not None and len(low) > 0:
            self.widget.configure(from_=low)
            try:
                amount = float(amountText)
                low = float(self.widget.cget('from'))
                high = float(self.widget.cget('to'))
            except:
                pass
            else:
                if amount < low or amount > high:
                    self._toggle_error('Invalid')
                self.set(amountText)

    def maximumChange(self, *_):
        self._toggle_error()
        amountText = self.get()
        high = self.group[1].get()
        if amountText is not None and len(amountText) > 0 and high is not None and len(high) > 0:
            self.widget.configure(to=high)
            try:
                amount = float(amountText)
                low = float(self.widget.cget('from'))
                high = float(self.widget.cget('to'))
            except:
                pass
            else:
                if amount < low or amount > high:
                    self._toggle_error('Invalid')
                self.set(amountText)

    def coordinateMinMax( self, *spinBoxes):
        '''Coordinate a servies of SpinBoxes so that the maximum of one is the minimum of the next one.
        The widget making the call is the lowest in the series.  The second is the maximum.  All others
        must fall between the two.'''
        # Insure this can be done with a integer, float series of spinboxes
        if len(spinBoxes) == 0: return
        if self.formatType == "" or self.formatType == tk.StringVar: return
        self.group = [self, *spinBoxes]
        minimumBox = True
        maximumBox = True
        for spinbox in self.group:
            if minimumBox:
                minimumBox = False
                continue
            self.group[0].variable.trace_add('write', spinbox.minimumChange)
            spinbox.group = self.group # All widgets are the same group
            if maximumBox:
                maximumBox = False
                continue
            self.group[1].variable.trace_add('write', spinbox.maximumChange)

class ValidRadioBox(RadioBox):
    def __init__(self, parent, *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)
        self._errorState = False
        self.widget.config(takefocus=1)
        if self.label is None:
            self._originalLabelText = "Missing"
        else:
            self.label.widget.config(takefocus=1)
            self._originalLabelText = self.label.get()
        self.widget.bind('<Button>', self._trigger_focus_out_validation)
        self.variable.trace_add('write', self._trigger_focus_out_validation)

    def _toggle_error( self, error=''):
        newErrorState = len(error) > 0
        if newErrorState:
            text = f"{error} {self._originalLabelText}"
            self.label.widget.config(text=text,foreground=self.colors["Red"])
            self._errorState = True

        elif self._errorState:
            self.label.widget.config(text=self._originalLabelText,foreground=self.colors["Black"])
            self._errorState = False

    def _trigger_focus_out_validation(self,*_):
        currentValue = self.get()
        self._toggle_error()
        if currentValue == False or currentValue is None:
            self._toggle_error('Missing')

    # Clear method to additionally clear the error state (called by the radioBox)
    def clear(self):
        super().clear()
        self._toggle_error()

    def errorCheck(self):
        currentValue = self.get()
        self._toggle_error()
        if currentValue == False or currentValue is None:
            self._toggle_error('Missing')


######################### Mixin (Interface) Classes #################################
class ValidHintedEntryUsDate(UsDateMixin, HintMixin, Entry):
    def __init__(self, parent, *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)

class ValidEntryUsDate(UsDateMixin, Entry):
    def __init__(self, parent, *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)

class ValidEntry(NonblankMixin, Entry):
    def __init__(self, parent, *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)

class SuggestEntry(UsDateMixin, Entry):
    def __init__(self, parent, *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)

class ValidEntryIsoDate(IsoDateMixin, Entry):
    def __init__(self, parent, *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)

class ValidSpinBox(ControlSpinBoxMixin, SpinBox):
    def __init__(self, parent, *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)

class ValidEntryPassword(PasswordMixin, Entry):
    def __init__(self, parent, *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)

class ValidTableComboBox(ComboBoxMixin, ComboBox):
    def __init__(self, parent, *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)
        super().__init__(parent, *dictionaries, **dictionary)

class ControlCheckBoxes(ControlMixin, CheckBoxes):
    def __init__(self, parent, *dictionaries, **dictionary):
        super().__init__(parent, *dictionaries, **dictionary)
        super().__init__(parent, *dictionaries, **dictionary)

##############################################################################################################
### Message Boxes ###
''' These are a collection of message boxes.  They are not standard widgets, but they are
    useful for getting information from the user.  They are part of tkinter.
    Use them as a function call that (usually) returns True for OK and False for CANCEL.

The following are the message boxes available.  The first two are the most common:
import tkinter.messagebox as tkMessageBox
result = tkMessageBox.askokcancel(title, message)
result = tkMessageBox.askokcancel(title, message, okText='Okie Dokie', cancelText='Not Now')
result = tkMessageBox.askquestion(title, message) # returns 'yes' or 'no'
result = tkMessageBox.askquestion(title, message, yesText='Yes Please', noText='No Thanks')
result = tkMessageBox.askretrycancel(title, message)
result = tkMessageBox.askyesno(title, message)
result = tkMessageBox.askyesnocancel(title, message) # Return True, False, or None for Cancel
result = tkMessageBox.showerror(title, message) # This group are "OK" only so no useful return, just "ok"
result = tkMessageBox.showinfo(title, message)
result = tkMessageBox.showwarning(title, message)
result = tkMessageBox.askdirectory(title, message)
'''
### Dialog Boxes ###
''' These are a collection of dialog boxes.  They are not standard widgets, but they are
    useful for getting information from the user.  They are not part of the GraphicsObject.
    Use them as a function call.

The following are the dialog boxes available.  The first two are the most common:
import tkinter.filedialog as tkFileDialog
result = tkFileDialog.askopenfilename(title, message, filetypes=[("Text files","*.txt")])
result = tkFileDialog.asksaveasfilename(title, message, filetypes=[("Text files","*.txt")])
result = tkFileDialog.askopenfilenames(title, message, filetypes=[("Text files","*.txt")])
result = tkFileDialog.asksaveasfile(title, message, filetypes=[("Text files","*.txt")])
result = tkFileDialog.askopenfile(title, message, filetypes=[("Text files","*.txt")])
result = tkFileDialog.askdirectory(title, message)
result = tkFileDialog.askopenfilenames(title, message, filetypes=[("Text files","*.txt")])
'''