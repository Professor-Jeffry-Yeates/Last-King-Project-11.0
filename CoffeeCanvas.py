# CoffeeCanvas
__version__ = '11.0'
"""This library contains basic graphics based on the Tkinter library.  All graphic
elements are based on the Canvas widget.  The library is designed to be simple to use
and to provide the complete range of Tkinter Canvas graphical objects.
Simple Graphical objects included:
    Canvas: A Tkinter widget that contains all the graphical objects. See the Canvas class.
    Pixel: A single point (a line with 1 width and 1 length) with a fill color.
    Line: A line from one point to another with a width and fill color.
    Circle: A circle with a center point and radius with a fill color.
    Rectangle: A rectangle with two points as corners and a fill color.
    Oval: An oval with two points as corners and a fill color.
    Polygon: A polygon with a list of points and a fill color.
    Text: A text string with a point and font.
    Image: An image with a point and a file name.
    GenericObject: Base-class for all of the drawable objects.
    Point: A named tuple class that holds an x and y coordinate.
    Environment: A collection of canvas environment variables useful for drawing.

Utility functions included:
    SimpleCanvas: With just a few parameters, create a resizable window with a scrollable canvas.
    IndependentProcess: Run a function in a separate and independent process.
    Sleep: Pause for a specified number of seconds (compatible with Tkinter).

Complex Graphical objects included:
    CountdownTimer: A countdown timer with a start and stop function.
    CanvasButton: A button with text and a function to call when clicked.
    Canvas Entry: A text entry box. 
    OK Popup: A window that pops up with a message and an OK button.
    YesNo Popup: A window that pops up with a message and Yes and No buttons.
    OK Button: A button with text and a function to call when clicked.
    Cancel Button: A button with text and a function to call when clicked.
    Popup: Base-class for popup windows.
    BasicButton: Base-class for all buttons.
    Panel: Contains a list based on some relationship of buttons and group commands.
    Group: A group of radio or check box buttons.

    NOTE: Rotation is not specifically included in the Tkinter library.  
    Polygons can be rotated using the provided .rotate() function.  Circles and Ovals
    must be converted to polygons to be rotates as well as rectangles.  That's hard!
    Text may be rotated using the angle keyword in the configuration dictionary unless
    thay have their own rotate() function. Images may be rotated using the PIL library.
    That library is not included in the standard Python library and must be installed.

CHANGES:
 
    """
from email.mime import text
import tkinter as tk
from tkinter import ttk
import datetime
try:  
    from PIL import Image as PILImage
    from PIL import ImageTk
    PIL_available = True
except:
    PIL_available = False
from tkinter.font import Font
from CoffeeBean import TextBox as _TextBox
from CoffeeBean import LabelFrame as _LabelFrame
from CoffeeBean import Frame as _Frame
from CoffeeBean import ComboBox as _ComboBox
import CoffeeColors
import time, os, math, threading, sys
from threading import Timer, Barrier
import platform, subprocess, re #  Regex
class Window():
    def __init__(self, title, **dictionary):
        self.root = tk.Tk()
        self.widget = self.root
        self.widget.title(title)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.columnconfigure(0, weight=1) 
        self.root.rowconfigure(0, weight=1) 
        self.canvas = None # Canvas widget will be the parent of most other widgets when used
        self.colors = CoffeeColors.ColorClass() # Color class for colors
        self.widgets = [] # Hold all current widget that can receive input
        self.comboboxFont = dictionary.get('checkBoxFont', None) # Combobox characteristics are set once just before starting the window loop
        self.comboboxBackgroundColor = None
        self.MacOS = (platform.system() == 'Darwin') # Used to adjust for MacOS
        self.darkMode = self.checkDarkMode()
        background = dictionary.pop('background', 'White')
        background = self.colors.get(background, background) 
        self.widget.configure(bg=background) # Set the background color of the window
        self.processArguments(dictionary)

        # Process the dictionary of attributes
    def processArguments(self, dictionary):
        if len(dictionary) > 0:
            placing = False
            sizing = False
            resizable = False
            xResize = None
            yResize = None
            height=0
            width=0
            x=0
            y=0
            for keyValue, value in dictionary.items():
                key = keyValue.lower()
                if   key == 'height': 
                    height = value
                    sizing = True
                elif key == 'width': 
                    width = value
                    sizing = True
                elif key == 'size':
                    (width,height) = value
                    sizing = True
                elif key == 'x': 
                    x = value
                    placing = True
                elif key == 'y': 
                    y = value
                    placing = True
                elif key == 'coord':
                    (x,y) = value
                    placing = True
                elif key == 'resizable': 
                    resizable = value
                elif key == 'x resizable': 
                    xResize = True
                    resizable = True
                elif key == 'y resizable': 
                    yResize = True
                    resizable = True

            if resizable:
                if xResize is None and yResize is None:
                    xResize = True
                    yResize = True
                elif xResize is None: 
                    xResize = False
                elif yResize is None: 
                    yResize = False
            else:
                xResize = False
                yResize = False 
            self.widget.resizable(xResize,yResize)
            
            maxwidth = self.widget.winfo_screenwidth()
            if width > maxwidth: width = maxwidth
            maxHeight = self.widget.winfo_screenheight()
            if height > maxHeight: height = maxHeight

            if placing and sizing:
                newGeometry = f"{width}x{height}+{x}+{y}" 
                self.widget.geometry(newGeometry)
            elif placing:
                newGeometry = f"+{x}+{y}" 
                self.widget.geometry(newGeometry)
            elif sizing:
                newGeometry = f"{width}x{height}"
                self.widget.geometry(newGeometry)
    
    # recursive function to search children of parent widget to find all children widgets
    def findChildren(self, parentWidget):
        widgetList = []
        childList = parentWidget.winfo_children()
        if len(childList) > 0: 
            widgetList.extend(childList)
            for widget in childList:
                childList = self.findChildren(widget)
                if len(childList) > 0: widgetList.extend(childList)
        return widgetList
    
    def getWidgetChildren( self, limitTo=None, exclude=None ):
        returnList = []
        for widget in self.widgets:
            keep = True
            if exclude is not None: 
                for eachClass in exclude:
                    if isinstance(widget, eachClass): 
                        keep = False
                        break
            if keep and limitTo is not None:
                keep = False
                for eachClass in limitTo:
                    if isinstance(widget, eachClass):  
                        keep = True
                        break
            if keep: 
                returnList.append(widget)
        return returnList
    def addWidget( self, widget):
        self.widgets.append(widget)

    def returnWidgetValues( self, clear=False, errorCheck = False, limitTo=None, exclude=None ):
        data = dict()
        for widget in self.widgets:
            keep = True
            if exclude is not None: 
                for eachClass in exclude:
                    if isinstance(widget, eachClass): 
                        keep = False
                        break
            if keep and limitTo is not None:
                keep = False
                for eachClass in limitTo:
                    if isinstance(widget, eachClass):  
                        keep = True
                        break
            if keep: 
                name = widget.name
                value = widget.get()
                if errorCheck: widget.errorCheck()
                data[name] = value
                if clear: widget.clear()
        return data

    def returnWidgets( self, limitTo=None, exclude=None ):
        data = dict()
        for widget in self.widgets:
            keep = True
            if exclude is not None: 
                for eachClass in exclude:
                    if isinstance(widget, eachClass): 
                        keep = False
                        break
            if keep and limitTo is not None:
                keep = False
                for eachClass in limitTo:
                    if isinstance(widget, eachClass):  
                        keep = True
                        break
            if keep: 
                name = widget.name
                data[name] = widget
        return data
    def removeWidgets( self, limitTo=None, exclude=None ):
        if limitTo is None and exclude is None:
            self.widgets.clear()
        else:
            for widget in self.widgets:
                keep = True
                if exclude is not None: 
                    for eachClass in exclude:
                        if isinstance(widget, eachClass): 
                            keep = False
                            break
                if keep and limitTo is not None:
                    keep = False
                    for eachClass in limitTo:
                        if isinstance(widget, eachClass):  
                            keep = True
                            break
                if keep: 
                    name = widget.name
                    del self.widgets[name]
    def removeWidget( self, widget):
        name = widget.name
        if name is not None and len(name) > 0:
            for i in range(len(self.widgets)):
                if name == self.widgets[i].name:
                    del self.widgets[i]
                    break
    def numberOfWidgets(self):
        return len(self.widgets)
    def validateWidgets(self, data, limitTo=None, exclude=None, checkActivated=False):
        list = []
        for key, value in data.items():
            keep = True
            if exclude is not None: 
                for name in exclude:
                    if name == key: 
                        keep = False
                        break
            if keep and limitTo is not None:
                keep = False
                for name in limitTo:
                    if name == key:  
                        keep = True
                        break
            if keep: 
                if value is None:
                    list.append(key)
                elif isinstance(value, str):
                    if len(value) == 0: list.append(key)
        return list
 
    def validateVisibleActivatedWidgets(self, clear=False, limitTo=None, exclude=None):
        widgetsDictionary = self.returnWidgets( limitTo=None, exclude=None )
        data = dict()
        for widgetName, eachWidget in widgetsDictionary.items():
            visible = eachWidget.checkVisibilityStatus()
            if eachWidget.activated and visible:
                
                keep = True
                if exclude is not None: 
                    for eachClass in exclude:
                        if isinstance(eachWidget, eachClass): 
                            keep = False
                            break
                if keep and limitTo is not None:
                    keep = False
                    for eachClass in limitTo:
                        if isinstance(eachWidget, eachClass):  
                            keep = True
                            break
                if keep: 
                    eachWidget.errorCheck()
                    if not eachWidget.answerIsCorrect(): #value != eachWidget.correctAnswer:
                        data[widgetName] = eachWidget
                    if clear: eachWidget.clear()
        return data
 
    def listVisibleActivatedWidgets(self, clear=False, limitTo=None, exclude=None):
        widgetsDictionary = self.returnWidgets( limitTo=None, exclude=None )
        data = dict()
        for widgetName, eachWidget in widgetsDictionary.items():
            visible = eachWidget.checkVisibilityStatus()
            if eachWidget.activated and visible:
                
                keep = True
                if exclude is not None: 
                    for eachClass in exclude:
                        if isinstance(eachWidget, eachClass): 
                            keep = False
                            break
                if keep and limitTo is not None:
                    keep = False
                    for eachClass in limitTo:
                        if isinstance(eachWidget, eachClass):  
                            keep = True
                            break
                if keep: 
                    value = eachWidget.get()
                    eachWidget.errorCheck()
                    correct = eachWidget.correctAnswer == value
                    data[widgetName] = (value,eachWidget.correctAnswer,correct)
        return data
    def eraseWidgetValues(self, limitTo=None, exclude=None ):
        data = dict()
        for widget in self.widgets:
            keep = True
            if exclude is not None: 
                for eachClass in exclude:
                    if isinstance(widget, eachClass): 
                        keep = False
                        break
            if keep and limitTo is not None:
                keep = False
                for eachClass in limitTo:
                    if isinstance(widget, eachClass):  
                        keep = True
                        break
            if keep: 
                widget.clear()
        return data

    def getGeometry(self):
        """Return window width, height, and also x, y position"""
        self.root.update_idletasks()
        newGeometry = self.widget.winfo_geometry()
        width = newGeometry.split("x")
        height = width[1].split("+")
        try:
            newWidth = int(width[0])
            newHeight = int(height[0])
            newX = int(height[1])
            newY = int(height[2])
        except:
            return None, None, None, None
        else:
            return newWidth, newHeight, newX, newY

    def saveCheckboxFont( self, font):
        self.comboboxFont = font
    def saveCheckboxBackgroundColor(self, color):
        self.comboboxBackgroundColor = self.colors.get(color, color)
    def setCanvas( self, canvas):
        self.canvas = canvas
    def close(self):
        """Close the window"""
        self.root.destroy()
        
    def checkDarkMode(self):
        darkMode = False
        if self.MacOS:
            cmd = 'defaults read -g AppleInterfaceStyle'
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            r = p.communicate()[0]
            darkMode = bool(r)
        else:
            checkingDarkmode = True
            try:
                import winreg
            except ImportError:
                checkingDarkmode = False
            if checkingDarkmode:
                try:
                    registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                    reg_keypath = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize'
                    reg_key = winreg.OpenKey(registry, reg_keypath)
                except FileNotFoundError:
                    pass
                else:
                    for i in range(1024):
                        try:
                            value_name, value, _ = winreg.EnumValue(reg_key, i)
                            if value_name == 'AppsUseLightTheme':
                                darkMode = value == 0
                                break
                        except OSError:
                            pass
        return darkMode    
    def returnMacOSAdjustment(self):
        if self.MacOS:
            return 4,4
        else:
            return 0,0
    def mainloop(self):
        # This changes the font for the selection list in a combobox
        if self.comboboxFont is not None:
            self.widget.option_add("*TCombobox*Listbox*Font", self.comboboxFont)
        if self.comboboxBackgroundColor is not None:
            self.widget.option_add("*TCombobox*Listbox*Background", self.comboboxBackgroundColor)
        self.widget.mainloop()

class KeySelect():
    """A class to manage keyboard key selection events.  The class is designed to be used with the Canvas class.
    The class is used to bind a key to a function.  The function is called when the key is pressed.  
    """
    def __init__(self, key, role, *functions):
        self.key = key
        self.usePress = False
        self.useRelease = False
        self.continuous = False
        self.ready = False # Ready to perform its function(s)
        self.pressActive = True
        self.functions = functions
        if role.lower() == "keypress": self.usePress = True
        elif role.lower() == "keyrelease": self.useRelease = True
        elif role.lower() == "continuous": self.continuous = True

    def __repr__(self):
        niceCopy = KeySelect(self.key, self.role, *self.functions)
        return niceCopy
    def __str__(self):
        return "KeySelect for key:{}".format(self.key)
    
    def actions(self, event=None):
        for action in self.functions:
            action(event)
 
class Canvas():    
    """A Canvas contains a widget that displays widgets as well as graphical objects like boxes, lines and text.  
    The root is the top window which can also hold widgets.  While it is assummed that a root window 
    already exists, if a root window is not provided, a simple one is created.  The title is the 
    window's title and the window is deleted upon being closed.  If the window dimensions
    are smaller than the canvas dimensions, scrolling is provided.  Note default values.
    REQUIRED ARGUMENTS:
        TopWindow is the window that the canvas is placed upon.

    DICTIONARY:
        The background color of the canvas
        The width and heigth dimensions of the canvas
    
    EVENT VS MANUAL CHECKING:
        Normal mouse selection is event driven using functions bound to an object.  If manual checking is desired,
        call the canvas function .checkSelectionManually() after defining the canvas to manually check for mouse 
        clicks and keystrokes.  The following canvas functions are used to get mouse clicks and keys:
            .getMouse() - Wait for mouse click and return Point object representing the click position
            .checkMouse() - Return last mouse click or None if mouse has not been clicked since last call
            .getKey() - Wait for user to press a key and return it as a string
            .checkKey() - Return last key pressed or None if no key pressed since last call
            .clickedItem() - Return the item if point is inside it, otherwise return None
            .currentValues() - Return the current return-values of the list of objects as a dictionary
            .getMouse() - Popup window function to return the button name of the button clicked 
    """
    DefaultConfigurations = dict(background="DarkGreen", width=800, height=600, confine=False)

    
    def __init__(self, parent, **kwargs):
        self.parent = parent # Class holding top window information
        self.widget = None # Canvas widget to be created
        self.root = None
        self.window = None
        self.frame = None
        self.pack = False
        self.place = False
        self.grid = False
        self.drawn = False
        self.state = tk.NORMAL
        params = ""
        for key, value in kwargs.items():
            params = f"{key}={value},"
        self.allDescriptions = "Canvas kwargs are " + params[:-1] + "\n"
        self.development = kwargs.pop('development', False) # Not currently used
        self.tags = kwargs.pop('tags', None) # Not currently used
        self.usePIL = kwargs.pop('PIL', PIL_available) 
        self.configuration = dict(**kwargs) # Library of mofifications to the canvas
        for key,value in Canvas.DefaultConfigurations.items(): self.configuration.setdefault(key, value)

        # Special processing for scrolling and positioning of a canvas within a canvas
        self.scrolling = False if 'scrolling' not in self.configuration else self.configuration.pop('scrolling')
        scrollingregion = None if 'scrollingregion' not in self.configuration else self.configuration.pop('scrollingregion')
        self.x = None if 'x' not in self.configuration else self.configuration.pop('x')
        self.y = None if 'y' not in self.configuration else self.configuration.pop('y')
        self.wasd_keys_allowed = False if 'WASD' not in self.configuration else self.configuration.pop('WASD')
        self.width = self.configuration.get('width',0) 
        self.height = self.configuration.get('height',0) 
        self.oldWidth = None
        self.oldHeight = None

        self.root = parent.widget._root()
        self.window = parent
        while not isinstance(self.window,Window):
            self.window = self.window.parent
        self.canvasIsTheParent = (self.x is not None and self.y is not None)
        # Canvas as the parent 
        if self.canvasIsTheParent:
            self.allDescriptions += "canvasIsTheParent, "
            self.parentWidget = parent.widget
            self.wasd_keys_allowed = parent.wasd_keys_allowed # Use the parent window's WASD setting
            self.development = parent.development # Use the parent window's development setting
        # A window is the parent
        else:
            self.frame = tk.Frame(self.root) # needed for scrolling if requested
            self.framePack = dict(side=tk.LEFT, expand=True, fill=tk.BOTH)
            self.frame.pack(**self.framePack)
            self.parentWidget = self.frame
            _width, _height, _, _ = self.window.getGeometry()
            self.width = max(_width,self.width)
            self.height = max(_height, self.height)
            self.allDescriptions += """self.frame = tk.Frame(self.root) # needed for scrolling if requested
            self.framePack = dict(side=tk.LEFT, expand=True, fill=tk.BOTH)
            self.frame.pack(**self.framePack)
            self.parentWidget = self.frame\n"""

        self.colors = self.window.colors
        background = self.configuration.get('background', 'DarkGreen')
        self.background = self.colors.get(background, background)
        self.configuration['background'] = self.background # Save the background color in the configuration
        self.widget = tk.Canvas(self.parentWidget, **self.configuration)
        self.drawn = True
        self.allDescriptions += "self.widget = tk.Canvas(self.parentWidget, **self.configuration)\n"

        # Canvas as the parent 
        if self.canvasIsTheParent:
            self.parentWidget.create_window(self.x, self.y, anchor="nw", window=self.widget)
            self.parentWidget.configure(scrollregion=parent.widget.bbox("all")) 
            self.place = True
            self.allDescriptions += """self.parentWidget.create_window(self.x, self.y, anchor="nw", window=self.widget)
            self.parentWidget.configure(scrollregion=parent.widget.bbox("all")) 
            self.place = True\n"""

        # A window is the parent
        else:
            if self.scrolling: self.setupCanvasScrolling()
            self.pack = dict(side=tk.LEFT, expand=True, fill=tk.BOTH)
            self.widget.pack(**self.pack)
            parent.canvas = self # Save self back into the window
            self.allDescriptions += """self.pack = dict(side=tk.LEFT, expand=True, fill=tk.BOTH)
            self.widget.pack(**self.pack)
            parent.canvas = self # Save self back into the window"""

        self._update_lasttime = time.time() # Used to time local update pauses
        self.backgroundImage = None # Background image for the canvas
        self.items = dict() # Dictionary of created objects
        self.design = dict() # List of designs
        self.keyEventDictionary = dict() # Dictionary of all event handlers
        self.keyPressActive = False
        self.keyReleaseActive = False
        self.millisecondsDelay = 20
        self.inputsActive = False
        self.activePanel = None # Any single active panel for user input
        self.bindingAllowed = True # Allow binding of actions to the object as opposed to checking manually for a selection
        self.mouseX = None # Used for manual checking of mouse clicks and keys
        self.mouseY = None
        self.lastKey = ""
        self.mouseFlag = tk.IntVar() # Set upon mouse click, used when waiting
        self.keyFlag = tk.IntVar() # Set upon key entered, used when waiting
        self.sleepBriefly = Sleep(.1, reuse=True) # Sleep class for .1 seconds when manually checking of mouse clicks and keys
        self.movementHalted = False # Manual stoppage of movement

        # Manual Checking of mouse clicks and keys as opposed to event driven user interface which is the default
        if 'manualChecking' in self.configuration: self.checkSelectionManually()
        self.root.update_idletasks() # Force all queued events to be processed
        
    def __repr__(self):
        niceCopy = Canvas(self.parent, **self.configuration)
        return niceCopy
    def __str__(self):
        return "Canvas: size {}x{})".format(self.width, self.height) 

    def changeState(self, newState):
        """Change the state of the canvas to normal or disabled. The canvas can also be HIDDEN by affecting it's packing.
        state: 'normal', 'disabled' or 'hidden'. Not working
        """
        if type(newState) is str:
            stateUsed = tk.NORMAL
            stateLowerCase = newState.lower()
            if stateLowerCase == 'disabled':
                stateUsed = tk.DISABLED
            elif stateLowerCase == 'hidden': 
                stateUsed = tk.HIDDEN

            if self.state != stateUsed:
                match stateUsed:
                    case tk.DISABLED:
                        self.widget.config(state=stateUsed)
                    case tk.HIDDEN: # Nice but not working
                        if self.pack:
                            self.widget.pack_forget()
                        elif self.place:
                            self.widget.place_forget()
                        elif self.grid:
                            self.widget.grid_forget()
                    case tk.NORMAL:
                        if self.state == tk.DISABLED:
                            self.widget.config(state=stateUsed)
                        if self.state == tk.HIDDEN:
                            if self.place:
                                self.widget.place(self.x, self.y)
                            elif self.pack:
                                self.widget.pack(**self.pack)
                            elif self.grid:
                                self.widget.grid(**self.grid)
                self.update()
                self.state = stateUsed

    def setBackground(self, color):
        """Set background color of the window"""
        self.background = self.colors.get(color, color)
        self.widget.config(bg=color) 
        self.update()

    def getCanvasHeight(self):
        """Return the height of the window"""
        return self.height
    def getCanvasWidth(self):
        """Return the width of the window"""
        return self.width 
    def getCanvasCoodinates(self):
        """Return the dimensions of the window as a tuple (width, height)"""
        return (self.x, self.y, self.width, self.height)
    
    def update(self, rate=None, usingWindows=False):
        """Update the window and pause for rate seconds"""
        if not self.drawn: return

        # self.canvas.update() has Tcl/Tk 8.6.1 regression issue in MacOS         
        usingMacOS = False if usingWindows else self.window.MacOS
        if usingMacOS: 
            pauseRate = 1 if rate is None else min(rate,500)
            self.root.after(pauseRate,self.root.update_idletasks())

        # Windows does not have the issue
        elif rate is not None:
            now = time.time()
            pauseLength = 1/rate-(now - self._update_lasttime)
            if pauseLength > 0:
                time.sleep(pauseLength)
                self._update_lasttime = now + pauseLength
            else:
                self._update_lasttime = now
            self.root.update_idletasks()

    def quit(self, *args):
        """Quit the window"""
        self.parent.close()  
        self.drawn = False 
        exit(0) 

    def addCanvasDesign(self, item, **kwargs):
        """Save the attribute(s) for a named design element."""
        self.design[item] = dict(**kwargs)

    def setupCanvasScrolling(self):
        """Create the x and y scroll bars in the frame holding the canvas which control 
        the view of the canvas.
        """
        canvas = self.widget
        frame = self.frame
        xscroll = ttk.Scrollbar(frame, command=canvas.xview, orient=tk.HORIZONTAL)
        xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.configure(xscrollcommand=xscroll.set)

        yscroll = ttk.Scrollbar(frame, command=canvas.yview, orient=tk.VERTICAL)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.configure(yscrollcommand=yscroll.set)

        # Bind configuration events to the canvas' scroll bars withing the scroll region provided
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=frame.bbox("all")))
        
        # Prevent the window from resizing larger than the canvas
        self.root.wm_maxsize(self.width, self.height)

        # Optionally, prevent resizing smaller than the canvas
        #self.root.wm_minsize(canvas_width, canvas_height)

        # Place a new frame inside the canvas as a window to hold everything else
        #self.widget = tk.Frame(self)
        self.scrollFrame = tk.Frame(canvas)
        canvas.create_window((0,0), window=self.scrollFrame, anchor="nw")
        canvas.configure(scrollregion=canvas.bbox("all")) 
        self.allDescriptions += """canvas = self.widget, frame = self.frame
        xscroll = ttk.Scrollbar(frame, command=canvas.xview, orient=tk.HORIZONTAL)
        xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.configure(xscrollcommand=xscroll.set)
        yscroll = ttk.Scrollbar(frame, command=canvas.yview, orient=tk.VERTICAL)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.configure(yscrollcommand=yscroll.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=frame.bbox("all")))
        self.root.wm_maxsize(self.width, self.height)
        #self.root.wm_minsize(canvas_width, canvas_height)
        #self.widget = tk.Frame(self)
        self.scrollFrame = tk.Frame(canvas)
        canvas.create_window((0,0), window=self.scrollFrame, anchor="nw")
        canvas.configure(scrollregion=canvas.bbox("all")) \n"""
    
    ## Update the scroll region when it changes
    def updateScrollRegion(self):
        if self.scrolling: 
            canvas = self.widget
            canvas.update_idletasks()
            canvas.config(scrollregion=self.frame.bbox()) 
            canvas.update_idletasks()

    # Track specific items on the canvas
    def addCanvasItem(self, item):
        if item is not None:
            if hasattr(item,"id") and item.id is not None:
                self.items[item.id] = item
    def findCanvasItemById(self, id):
        if id in self.items:
            return self.items[id]
        return None
    def deleteCanvasItem(self, item):
        del self.items[item.id]
    def redrawCanvas(self):
        for item in self.items[:]:
            item.undraw()
            item.draw()
        self.drawn = True
        self.update()
    def draw(self):
        for item in self.items.items():
            item.draw()
        self.drawn = True
        self.update()        
        if self.scrolling:
            canvas = self.widget
            canvas.configure(scrollregion=canvas.bbox("all"))

    # Utilities for using lists
    def displayList( self, list=None ):
        if list is None:
            for item in self.items:
                item.draw()
        else:
            for item in list:
                item.draw()
    def undisplayList( self, list=None ):
        if list is None:
            for item in self.items:
                item.undraw()
        else:
            for item in list:
                item.undraw()
    def findItemByNameInList( self, name, list=None):
        if list is None:
            for item,value in self.items.items():
                if value.name == name: return value
        else:
            for item in list:
                if item.name == name: return item
        return None
    def findItemByIdInList( self, id, list=None):
        if list is None:
            value = self.items.get(id, None)
            return value
        else:
            for item in list:
                if item.id == id: return item
        return None
    
    # Utilities for using bonding and actions
    def forEventAddFunction(self, item, action):
        """ Add a action to an event for the canvas.  The event is a string enclosed in <>."""
        try:
            event = '<'+item+'>'
            self.root.bind(event, action)
        except:
            pass
    def removeKeyFromEvent(self, item):
        """Remove an letter and action to a key press """
        if item in self.keyEventDictionary:
            canvas = self.widget
            key = self.keyEventDictionary[item]
            del self.keyEventDictionary[item]
            if len(self.keyEventDictionary) == 0: 
                canvas.unbind_all('<KeyPress>')
                canvas.unbind_all('<KeyRelease>')
        else:
            try:
                self.root.unbind('<'+item+'>')
            except:
                pass
    def keyPressDispatcher(self, event):
        """Identify a function associated with a keypress and run its function(s).
        Check first for a character or key symbol (like Left for the left arrow)"""
        if event.char in self.keyEventDictionary:
            keyPress = self.keyEventDictionary[event.char]
        elif event.keysym in self.keyEventDictionary:
            keyPress = self.keyEventDictionary[event.keysym]
            self.widget.find_overlapping
        else:
            return
        
        pressSelected = event.type == '2'
        releaseSelected = event.type == '3'
        if keyPress.continuous:
            keyPress.ready = pressSelected # Turns off on a Release of '3'
            
        elif keyPress.usePress:
            if pressSelected:
                if keyPress.pressActive:
                    keyPress.ready = True
                    keyPress.pressActive = False
            elif releaseSelected:
                keyPress.pressActive = True

        elif keyPress.useRelease:
            keyPress.ready = releaseSelected
        if keyPress.ready: self.inputsActive = True
    def checkKeyInputs(self):
        """Identify a function associated with a keypress and run its function(s).
        Check first for a character or key symbol (like Left for the left arrow)"""
        if self.inputsActive:
            continuousActive = False
            for keyPress in self.keyEventDictionary.values():
                if keyPress.ready:
                    keyPress.actions()
                    if keyPress.continuous:
                        continuousActive = True
                    else:
                        keyPress.ready = False
            self.inputsActive = continuousActive
        self.widget.after(self.millisecondsDelay, self.checkKeyInputs)
    def startKeyInput(self, millisecondsDelay=20):
        if self.bindingAllowed:
            if not self.inputsActive:
                self.inputsActive = True
                self.millisecondsDelay = millisecondsDelay
                self.checkKeyInputs()
    def keyPressFunction( self, letter, *actions):
        """Bind an action to a key press.  The action is a function."""
        if self.bindingAllowed:
            self.keyEventDictionary[letter] = KeySelect(letter, 'KeyPress', *actions)
            if not self.keyPressActive:
                self.root.bind('<KeyPress>', self.keyPressDispatcher)
                self.keyPressActive = True
    def keyReleaseFunction( self, letter, *actions):
        """Bind an action to a key press.  The action is a function."""
        if self.bindingAllowed:
            self.keyEventDictionary[letter] = KeySelect(letter, 'KeyRelease', *actions)
            if not self.keyReleaseActive:
                self.root.bind('<KeyRelease>', self.keyPressDispatcher)
                self.keyReleaseActive = True
    def keyContinuousFunction( self, letter, *actions):
        """Bind an action to a key press.  The action is a function."""
        if self.bindingAllowed:
            self.keyEventDictionary[letter] = KeySelect(letter, 'Continuous', *actions)
            if not self.keyPressActive:
                self.root.bind('<KeyPress>', self.keyPressDispatcher)
                self.keyPressActive = True
            if not self.keyReleaseActive:
                self.root.bind('<KeyRelease>', self.keyPressDispatcher)
                self.keyReleaseActive = True
  
    # Utilities for checking clicks and keystrokes
    def _onKey(self, event):
        """ Binding on keystroke when normal binding is not allowed"""
        self.lastKey = event.keysym   
        self.keyFlag.set(1)
    def _onClick(self, event):
        """ Binding on button 1 click when normal binding is not allowed"""
        self.mouseX = event.x
        self.mouseY = event.y
        self.mouseFlag.set(1)
    def getMouse(self):
        """Wait for mouse click and return Point object representing the click"""
        self.mouseX = None
        self.mouseY = None
        self.mouseFlag.set(0)
        self.root.wait_variable(self.mouseFlag)
        point = Point(self.mouseX,self.mouseY)
        self.mouseFlag.set(0)
        return point
    def checkMouse(self):
        """Return last mouse click or None if mouse has not been clicked since last call"""
        self.update()
        if self.mouseX is not None and self.mouseY is not None:
            point = Point(self.mouseX,self.mouseY)
            self.mouseX = None
            self.mouseY = None
            return point
        else:
            return None
    def getKey(self):
        """Wait for user to press a key and return it as a string."""
        self.lastKey = ""
        self.keyFlag.set(0)
        self.root.wait_variable(self.keyFlag)
        key = self.lastKey
        self.keyFlag.set(0)
        self.lastKey = ""
        return key
    def checkKey(self):
        """Return last key pressed or None if no key pressed since last call"""
        self.update()
        key = self.lastKey
        self.lastKey = ""
        return key   
    def clickedItem(self, point, *list):
        """Return the item if point is inside it, otherwise return None."""
        for item in list:
            if item.clicked(point):
                return item
        return None
    
    def currentValues( self, point, *list ):
        """Return the current return-values of the list of objects as a dictionary, including if an object was Selected."""
        data = dict()
        for item in list:
            try:
                data[item.name] = item.returnValue
                if point is not None:
                    if item.clicked(point):
                        data['Selected'] = item.name
            except:
                data[item.name] = 'Missing'
        return data
    def checkSelectionManually(self):
        """function to catch all points and keystrokes to check point against objects"""
        """Setting for not binding actions to objects     self.bindingAllowed"""
        canvas = self.widget
        self.bindingAllowed = False
        canvas.bind("<Button-1>", self._onClick)
        canvas.bind_all("<Key>", self._onKey)
    def undraw(self, *args):
        self.drawn = False
        self.widget.destroy()
        self.root.update_idletasks()
        
    def darkModeOn(self):
        return self.window.darkMode
    def changeDimensions(self, **dictionary):
        """Change the heightand width, keep old values incase a reset is required"""
        self.oldWidth = self.widget.cget('width') 
        self.oldHeight = self.widget.cget('height') 
        width = dictionary.get("width",self.oldWidth)
        height = dictionary.get("height",self.oldHeight)
        if self.oldHeight != height or self.oldWidth != width:
            self.widget.config(width=width, height=height)
        else:
            self.oldWidth = None
            self.oldHeight = None

    def getFourDimensions(self, arguments):
        """Extract coordinates from the arguments and return them as a tuple, often as (x,y,width,height),
        but fewer arguments may mean fewer values returned.  Pointa, Pointb, tuples, or lists may also be used."""
        newList = []
        length = len(arguments)
        if length == 0: 
            pass
        elif length == 1: 
            newList  = [*arguments]
        elif length <= 3:
            if len(arguments[0]) >= 2:
                newList.append(arguments[0][0])
                newList.append(arguments[0][1])
            else:
                newList.append(arguments[0])
            if len(arguments[1]) >= 2:
                newList.append(arguments[1][0])
                newList.append(arguments[1][1])
            else:
                newList.append(arguments[1])
            if length == 3:
                if len(arguments[2]) >= 2:
                    newList.append(arguments[2][0])
                    newList.append(arguments[2][1])
                else:
                    newList.append(arguments[2])   
        elif length >= 4:
            for index in range(4):
                newList.append(arguments[index])
                
        if len(newList) > 4: newList = newList[:4]
        resultTuple = tuple(newList)
        return resultTuple            
            
    def resetDimensions(self):
        """Reset to the previously saved height and width"""
        if self.oldHeight is not None and self.oldWidth is not None:
            self.widget.config(width=self.oldWidth, height=self.oldHeight)
        self.oldWidth = None
        self.oldHeight = None
        
    def mainloop(self):
        """Run the main loop for the entry."""
        self.parent.mainloop()
    def description(self):
        print(self.allDescriptions)

class Environment():
    """A collection of canvas environment variables useful for drawing"""
    def __init__(self, width, height, buffer=0, canvas=None):
        self.x_width = width
        self.y_height = height
        self.canvas = canvas
    
        # The remaining variables are all based on the previous ones
        self.top = buffer
        self.bottom = self.y_height - buffer
        self.left = buffer
        self.right = self.x_width - buffer
        self.windowWidth = self.x_width
        self.windowDepth = self.y_height
        self.middleWidth = self.x_width/2
        self.middleDepth = self.y_height/2
        self.centerPoint = Point(self.middleWidth, self.middleDepth)

    # Make sure to use these to access the canvas enviroment 
    def getCanvas(self ): return self.canvas 
    def setCanvas(self, canvas ): self.canvas = canvas
    def setRatio(self, ratio):
        self.ratio = ratio
        self.x_width *= ratio
        self.y_height *= ratio
        self.bottom = self.y_height - self.buffer
        self.right = self.x_width - self.buffer
        self.windowWidth = self.x_width
        self.windowDepth = self.y_height
        self.middleWidth = self.x_width/2
        self.middleDepth = self.y_height/2
        self.centerPoint = Point(self.middleWidth, self.middleDepth)

    def useRatio(self, number):
        return self.ratio * number

def SimpleCanvas(title, **dictionary):
    """Create a simple window with a canvas.  The canvas is returned"""
    _background = dictionary.pop("background","White" )
    _eventDriven = dictionary.pop("EventDriven", True)
    width = dictionary.get("width", 1000) 
    height  = dictionary.get("height", 800)
    width, height = int(width), int(height)
    windowWidth = dictionary.pop("windowWidth", None)
    windowHeight = dictionary.pop("windowHeight", None)
    usingPIL = dictionary.get("PIL", True)
    development = dictionary.get("development", False)
    canvasDictionary = dict(background=_background, height=height, width=width, 
                            PIL=usingPIL, development=development)
    tags = dictionary.get("tags", None)
    if tags is not None: canvasDictionary['tags'] = tags

    if windowWidth is None or windowHeight is None:
        windowWidth = width if windowWidth is None else int(windowWidth)
        windowHeight = height if windowHeight is None else int(windowHeight)
        resizable = False
        scrolling = False
    else:
        windowWidth = width if windowWidth is None else int(windowWidth)
        windowHeight = height if windowHeight is None else int(windowHeight)
        resizable = width > windowWidth or height > windowHeight
        scrolling = resizable
    window = Window(title, coord=(10,10), size=(windowWidth, windowHeight), resizable=resizable, background=_background)
    canvas = Canvas(window, scrolling=scrolling, **canvasDictionary)
    if _eventDriven:
        canvas.startKeyInput()
    else:
        canvas.checkSelectionManually()
    return canvas

def DrawSimple( objectKind, canvas, *args, **kwargs):
    """Create a simple Tkinter object.  The objectName is the kind of the object, such as "circle" or "rectangle".
    The objectName can also be a class.
    The parent is the canvas or abother object to draw the object on.  The arguments are the specific arguments for the object.
    The keyword arguments are the optional keyword arguments for the object.  The function returns the 
    Tkinter object and displays it on the canvas immediately.  The CoffeeCanvas object(s) are not retained."""
    tkinterID = None
    if isinstance(objectKind, str):
        name = objectKind.lower()[:4]
        if name == "circ":
            object = Circle(canvas, *args, simpleDraw=True, **kwargs)
        elif name == "rect":
            object = Rectangle(canvas, *args, simpleDraw=True, **kwargs)
        elif name == "oval":
            object = Oval(canvas, *args, simpleDraw=True, **kwargs)
        elif name == "line":
            object = Line(canvas, *args, simpleDraw=True, **kwargs)
        elif name == "poly":
            object = Polygon(canvas, *args, simpleDraw=True, **kwargs)
        elif name == "text":
            object = Text(canvas, *args, simpleDraw=True, **kwargs)
        elif name == "imag":
            object = Image(canvas, *args, simpleDraw=True, **kwargs)
        elif name == "pixe":
            object = Pixel(canvas, *args, simpleDraw=True, **kwargs)
        elif name == "mult":
            object = MultipleLines(canvas, *args, simpleDraw=True, **kwargs)
        else:
            return None
            #raise Exception(f"Unknown object type: {name}")
    else:
        try:
            object = objectKind(canvas, *args, simpleDraw=True, **kwargs)
        except:
            #raise Exception(f"Unknown object type: {name}")
            return None

    tkinterID = object.id
    object = None # Remove all the structure from memory, keep just the Tkinter id
    return tkinterID

def CreateSimpleObject( objectKind, *args, **kwargs):
    # create an dictionary that contains the objectKind, args, and kwargs 
    object = {
        "objectKind": objectKind,
        "args": args,
        "kwargs": kwargs
    }
    return object
def DrawSimpleObjects( canvas, *objects, offset=None): # offset is an (x,y) offset for all objects
    ids = []
    for item in objects:
        id = DrawSimple(item['objectKind'], canvas, *item['args'], offset=offset, **item['kwargs'])
        ids.append(id)
    return ids
class Point():
    """A Point is an immutable tuple class that holds an x and y coordinate.  
    Note it is a named tuple and can be used as such or as a standard tuple.  For a 
    named tuple you can access its contents by name or index.
    Note it returns it's (x,y) values as floats in a named tuple like a function call."""
    def __init__(self, x,y):
        self.x = float(x)
        self.y = float(y)

    def __repr__(self):
        return self.clone(self.x, self.y)
    
    def __str__(self):
        return f"Point({self.x:.2f},{self.y:.2f})"
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Point): return False
        return self.x == value.x and self.y == value.y
    
    def clone(self):
        return Point(self.x,self.y)  
class GenericObject():
    """Generic base class for all of the drawable objects.  Provides common fields and methods.
     Note this is not instantiated by itself, but is only a parent class.
     
     ARGUMENTS:
        canvas: The canvas object is placed upon

     DICTIONARY:
        name: Optional name for the object pulled out of the configuration dictionary
        action: A function to call upon any selection
        autoDraw: Drawn automatically after creation, otherwise the draw() function is needed
        Additional elements are processed by a child object
     """
    possibleColors =["fill", "outline", "border", "color", "background", "foreground","fg","bg",
                            "selectbackground", "selectforeground","activebackground","activeforeground",
                            "disabledforeground","highlightbackground","highlightcolor"]
    def __init__(self, canvas, *args, **kwargs):
        self.canvas = canvas # Canvas object is placed upon
        self.arguments = list(args) # Each non-default arguments required for the object
        self.configuration = dict(**kwargs) # Dictionary of all other named arguments with defaults

        self.id = None # Canvas id for object upon being drawn
        self.p1 = Point(0,0) # Point or tuple class
        self.p2 = Point(0,0) # Point or tuple class. For single point objects this duplicates point 1
        self.twoDimensionalShape = False # Used to move objects using both p1 and p2
        self.drawn = False
        self.visible = False # Used to determine if the object is available for interaction without looking at the widget state, set upon draw()
        self.selectable = False
        self.code = "" # Tracks how the widget is made
        self.parameters = ""
        self.extraCode = ""
        self.design = None # One design at a time allowed
        self.offset = None if 'offset' not in self.configuration else self.configuration.pop('offset')
        self.autoDraw = True if 'autoDraw' not in self.configuration else self.configuration.pop('autoDraw')
        self.simpleDraw = False if 'simpleDraw' not in self.configuration else self.configuration.pop('simpleDraw')
        self.name = "" if 'name' not in self.configuration else self.configuration.pop('name')
        self.returnValue = self.name # Default return value is the name
        self.bindingAllowed = canvas.bindingAllowed if 'bindingallowed' not in self.configuration else self.configuration.pop('bindingallowed') # Allow binding of actions to the object as opposed to checking manually for a selection
        self.actions = []        
        actions = self.configuration.get('action', None)
        self.saveObjectActions(actions)

    def __eq__(self, object):
        if(id:= self.id):
            if hasattr(object, 'id'):
                if (objectId:= object.id):
                    return objectId == id
        return False
    def __str__(self):
        if self.drawn:
            bbox = self.getBoundingBox()
        else:
            bbox = [self.p1.x, self.p1.y, self.p2.x, self.p2.y]
        text = f"{self.name} at coordinates {bbox}"
        return text

    def description(self):
        config = ""
        for key, value in self.configuration.items():
            config += f"{key}={value},"
        code = f"{self.code}\n{self.parameters}, {config[:-1]}), {self.extraCode}\n"
        return code
    def initializeShape(self, defaultParameters, allowedParameters, evenPointsOnly=True):
        
        if len(self.arguments) == 0:
            raise Exception(f"Invalid number of arguments (0), cannot calculate coordinates")
        
        # Extract a Canvas object and/or list if provided
        argumentList = self.arguments
        start = 0 # Track where to start for each argument / parameter
        object = argumentList[start]
        if isinstance(object, Canvas ): 
            self.canvas = argumentList[start]
            start += 1
        
        # Get the next non-canvas argument.  If it is a list, use that instead of the argument list
        object = argumentList[start]
        if type(object) == list:
            argumentList = object
            start = 0

        # Convert all remaining elements into single numbers in a list
        newList = []
        numberOfArguments = len(argumentList)
        for i in range(start, numberOfArguments):
            item = argumentList[i]
            if type(item) == tuple:
                for subitem in item:
                    newList.append(subitem)
            elif type(item) == list:
                    newList.extend(item)
            elif type(item) == Point:
                newList.append(item.x)
                newList.append(item.y)
            else:
                newList.append(item)

        # If there are at least 2 arguments, the first 2 are a (x,y) coordinate pair
        numberOfArguments = len(newList)
        if numberOfArguments >= 2:
            self.twoDimensionalShape = True # Assume this

        # Extract the coordinates based on the number of arguments provided
        match (numberOfArguments):
            case 0:
                raise Exception(f"Invalid number of arguments (0), cannot calculate coordinates")
            case 1:
                raise Exception(f"Invalid number of arguments (1), cannot calculate coordinates")
            
            case 2: # One point or tuple or (x,y) provided
                self.p1 = Point(newList[0],newList[1])
                self.p2 = self.p1.clone()        
            case 3: # Circle point/tuple/(x,y) plus radius, create the bounding box
                self.radius = newList[2]
                self.p1 = Point(newList[0]-self.radius,newList[1]-self.radius)
                self.p2 = Point(newList[0]+self.radius,newList[1]+self.radius)
            case 4: # 2 points or tuples or (x,y) provided
                self.p1 = Point(newList[0],newList[1])
                self.p2 = Point(newList[2],newList[3])
            case _: # Multiple point object such as polygon or multiple lines
                polyList = []
                length = len(newList)
                self.twoDimensionalShape = False
                if not evenPointsOnly or length % 2 == 0:
                    max_x = 0
                    min_x = 10000
                    max_y = 0
                    min_y = 10000
                    for index in range(0, length, 2):
                        x = newList[index]
                        y = newList[index+1]
                        polyList.append((x,y))
                        if x > max_x: 
                            max_x = x
                        if x < min_x: 
                            min_x = x
                        if y > max_y: 
                            max_y = y
                        if y < min_y: 
                            min_y = y
                    self.p1 = Point(min_x,min_y)
                    self.p2 = Point(max_x,max_y)
                    self.arguments = polyList
                    self.twoDimensionalShape = True
                elif length == 0 and len(self.options) > 0: # Polygon
                    self.arguments = self.options
                    self.twoDimensionalShape = True
                else: 
                    raise Exception(f"Invalid number of arguments({len(self.arguments)}), cannot calculate coordinates")
        
        # If an offset was included, offset all coordinates
        if self.offset is not None and len(self.offset) == 2:
            if self.offset[0] != 0 and self.offset[1] != 0:
                offset_x = self.offset[0]
                offset_y = self.offset[1]
                self.p1.x += offset_x
                self.p1.y += offset_y
                self.p2.x += offset_x
                self.p2.y += offset_y

                if self.twoDimensionalShape:
                    for index in range(len(self.arguments)):
                        x = self.arguments[index][0]+offset_x
                        y = self.arguments[index][1]+offset_y
                        self.arguments[index] = (x,y)

        # Designs can be saved in the canvas
        if 'design' in self.configuration:
            designName = self.configuration['design']
            if designName in self.canvas.design:
                self.design = designName
                self.configuration |= self.canvas.design[designName]
        
        # Only allow default and allowed configuration from here on out
        dictionary = dict(defaultParameters)
        for key in self.configuration:
            if key in allowedParameters:
                dictionary[key] = self.configuration[key]

        # Get any correct colors from the canvas color dictionary
        self.configuration = dictionary
        for checkColor in GenericObject.possibleColors:
            if checkColor in self.configuration:
                self.configuration[checkColor] = self.canvas.colors.get(self.configuration[checkColor], self.configuration[checkColor])

        # Add the item to the canvas and possibly draw it
        #self.canvas.addCanvasItem(self)
        if self.autoDraw: self.draw()

    def offsetPosition(self, *args):
        if len(args) == 2:
            self.offset = (args[0], args[1])
        elif len(args) == 1 and len(args[0]) == 2:
            self.offset = (args[0][0], args[0][1])
        else:
            self.offset = None

        if self.offset is not None:
            if self.offset[0] != 0 and self.offset[1] != 0:
                offset_x = self.offset[0]
                offset_y = self.offset[1]
                self.p1.x += offset_x
                self.p1.y += offset_y
                self.p2.x += offset_x
                self.p2.y += offset_y

                if self.twoDimensionalShape:
                    for index in range(len(self.arguments)):
                        x = self.arguments[index][0]+offset_x
                        y = self.arguments[index][1]+offset_y
                        self.arguments[index] = (x,y)

    def _extractArgsAsNumbers(arguments, start = 0):
        list = []
        length = len(arguments)
        for number in range(start, length):
            item = arguments[number]
            if isinstance(item, Point):
                list.append(item.x)
                list.append(item.y)
            elif isinstance(item, tuple):
                list.append(item[0])
                list.append(item[1])
            else:
                list.append(item)
        return list
    _extractArgsAsNumbers = staticmethod(_extractArgsAsNumbers)

    def _setDefaultConfigurations(self, **dictionary):
        """Add default values to the configuration dictionary if they are not already there.
        If a design element is named, use all attributes associated with it.
        There is no check for unknown attributes."""
        if 'design' in self.configuration:
            designName = self.configuration.pop('design')
            if designName in self.canvas.design:
                self.design = designName
                self.configuration |= self.canvas.design[designName]
        
        # Now that all attributes are decided upon, place new attributes in a dictionary
        for key,value in dictionary:
            lowerCaseKey = key.lower()
            self.configuration.setDefault(lowerCaseKey,value)

    def _removeSpecificConfigurations(self, limitTo=None, exclude=None, lowercaseKey=True):
        """Remove all but the listed configurations from the configuration dictionary"""
        dictionary = {}
        for key, value in self.configuration.items():
            if lowercaseKey: key = key.lower()
            if exclude is not None and key in exclude: 
                pass
            elif limitTo is not None and key not in limitTo: 
                pass
            else:
                dictionary[key] = value
        self.configuration = dictionary

    def _setCoordinatesFromArgs(self, providedArguments=None, evenCountEnforced=True):
        """Set the coordinates of the object based on the arguments provided
        or if none provided, on self.arguments. """ 
        # Initialize then check for an error if no argument are available
        self.p1 = Point(0,0)
        self.p2 = Point(0,0)
        self.twoDimensionalShape = None
        multipleCoordinates = False
        argumentList = self.arguments if providedArguments is None else providedArguments
        if len(argumentList) == 0:
            raise Exception(f"Invalid number of arguments (0), cannot calculate coordinates")
              
        # There are arguments 
        else:
            # Extract a Canvas object and/or list if provided
            start = 0 # Track where to start for each argument / parameter
            object = argumentList[start]
            if isinstance(object, Canvas ): 
                self.canvas = argumentList[start]
                start += 1
            
            # Get the next non-canvas argument.  If it is a list, use that instead of the argument list
            object = argumentList[start]
            if object.__class__.__name__ == 'list':
                argumentList = object
                start = 0

            # Convert all remaining elements into single numbers in a list
            list = self._extractArgsAsNumbers( argumentList, start=start)

            # If there are at least 2 arguments, the first 2 are a (x,y) coordinate pair
            numberOfArguments = len(list)
            if numberOfArguments >= 2:
                self.twoDimensionalShape = True # Assume this
            
            # Extract the coordinates based on the number of arguments provided
            match (numberOfArguments):
                case 0:
                    raise Exception(f"Invalid number of arguments (0), cannot calculate coordinates")
                case 1:
                    raise Exception(f"Invalid number of arguments (1), cannot calculate coordinates")
                
                case 2: # One point or tuple or (x,y) provided
                    self.p1 = Point(list[0],list[1])
                    self.p2 = self.p1.clone()        

                case 3: # Circle point/tuple/(x,y) plus radius, create the bounding box
                    self.radius = list[2]
                    self.p1 = Point(list[0]-self.radius,list[1]-self.radius)
                    self.p2 = Point(list[0]+self.radius,list[1]+self.radius)

                case 4: # 2 points or tuples or (x,y) provided
                    self.p1 = Point(list[0],list[1])
                    self.p2 = Point(list[2],list[3])

                case _: # Multiple point object such as polygon or multiple lines
                    self._extractMultipleArgsAsCoordinatePairs(list,evenCountEnforced=evenCountEnforced)
                    multipleCoordinates = True

         # If the list of arguments are not multiple points, self.arguments are longer needed
        if not multipleCoordinates: 
            self.arguments.clear()

    def _extractMultipleArgsAsCoordinatePairs(self, numberList, evenCountEnforced=True):
        """Set multiple coordinates of the object based on the numberList provided. 
        Lines and Polygons.  
        The resulting list must be a list of tuples (x,y) and not Points. """
        newList = []
        length = len(numberList)
        self.twoDimensionalShape = False
        if not evenCountEnforced or length % 2 == 0:
            max_x = 0
            min_x = 10000
            max_y = 0
            min_y = 10000
            for index in range(0, length, 2):
                x = numberList[index]
                y = numberList[index+1]
                newList.append((x,y))
                if x > max_x: 
                    max_x = x
                if x < min_x: 
                    min_x = x
                if y > max_y: 
                    max_y = y
                if y < min_y: 
                    min_y = y
            self.p1 = Point(min_x,min_y)
            self.p2 = Point(max_x,max_y)
            self.arguments = newList
            self.twoDimensionalShape = True

        elif length == 0 and len(self.options) > 0: # Polygon
            self.arguments = self.options
            self.twoDimensionalShape = True
        else: 
            raise Exception(f"Invalid number of arguments({len(self.arguments)}), cannot calculate coordinates")
   
    def bindSingleObjectAction(self, *args): # Now in action interface
        """Bind only one function to be called when the object is selected.  There can
        be multiple functions called by that function in the order they were added.
        If functions is None, use the first function in self.actions[] list.
        Canvas class must have an id to bind to a funtion (Canvas Entry, for example, does not)"""
        if self.bindingAllowed and self.id is not None:
            function = self.actions
            if function is not None: 
                if isinstance(function, list):
                    length = len(function)
                    if length == 0:
                        function = None
                    elif length > 1:
                        function = self.callActions
                    else:
                        function = self.actions[0]
            if function is not None: 
                self.canvas.widget.tag_bind(self.id, '<Button-1>', function)
    
    def draw(self, *args): # Child class should override this method then call this method
        """ Any remaining system call needed after an object is drawn """
        # Add this item to the Canvas' list of items (if not a simple Tkinter object)
        self.visible = True
        if not self.simpleDraw:
            self.canvas.addCanvasItem(self)
            self.bindSingleObjectAction() 
            if hasattr(self, 'dragActive') and self.dragActive:
                self.dragInfo.dragSetup()

    def undraw(self, *args):  
        """Undraw the object from the canvas"""
        if self.drawn:
            self.canvas.widget.tag_unbind(self.id, '<Button-1>')
            self.canvas.deleteCanvasItem(self)
            self.canvas.widget.delete(self.id)
            self.drawn = False

    def hide(self, *args):
        """Hide the object from the canvas but it is still available to become visible again"""
        if self.drawn and self.visible:
            self.visible = False
            self.reconfigure("state","hidden")

    def unhide(self, *args):
        """Unhide a hidden object from the canvas and make it visible again"""
        if self.drawn and not self.visible:
            self.visible = True
            self.reconfigure("state", "normal")
    def delete(self, *args):
        """Delete the object from the canvas and remove it from the list of items"""
        if self.drawn: 
            self.undraw()

    def reconfigure(self, option, value):
        options = {option:value}
        self.canvas.widget.itemconfig(self.id, options)
        self.canvas.update()

    def getConfiguration(self, option):
        """Get the current configuration of the object"""
        if self.canvas.widget:
            return self.canvas.widget.itemcget(self.id, option)
        else:
            return None

    def _getFill(self):
        return self.canvas.widget.itemcget(self.id, 'fill')
    def _setFill(self, color, extra=None):
        self.reconfigure('fill', color)
    color = property(_getFill, _setFill)
    
    def _setOutlineColor(self, color, extra=None):
        goodColor = self.canvas.colors.get(color, color)
        self.reconfigure('outline', goodColor)
    outlineColor = property(None, _setOutlineColor)
        
    def _getOutlineWidth(self):
        return self.canvas.widget.itemcget(self.id, 'width')
    def _setOutlineWidth(self, width, extra=None):
        self.reconfigure('width', width)
    outlineWidth = property(_getOutlineWidth, _setOutlineWidth)

    def levelUp(self, *args):
        """Raise the object up one level in the canvas"""
        self.canvas.widget.tag_raise(self.id)

    def levelDown(self, *args):
        """Lower the object up one level in the canvas"""
        self.canvas.widget.tag_lower(self.id)

    def setToTopObject(self, *args):
        ids = self.canvas.widget.find_all()
        if len(ids) > 1:
            highest = ids[0]
            self.canvas.widget.tag_raise(self.id, highest)
            
    def setToBottomObject(self, *args):
        ids = self.canvas.widget.find_all()
        if len(ids) > 1:
            lowest = ids[len(ids)-1]
            self.canvas.widget.tag_lower(self.id, lowest)
            
    def setBeforeObject(self, *args):
        object = args[0] if len(args) > 0 else None
        if object is not None: self.canvas.widget.tag_lower(self.id, object.id)
            
    def setAfterObject(self, *args):
        object = args[0] if len(args) > 0 else None
        if object is not None: self.canvas.widget.tag_raise(self.id, object.id)

    # Get location values or Points     
    def getX(self): return self.p1.x
    def getY(self): return self.p1.y         
    def getP1(self): return self.p1.clone()
    def getP2(self): return self.p2.clone()
    def getCenter(self): # Must allow for recalculation due to movement
        if not self.canvas: return None
        a,b,c,d = self.canvas.widget.bbox(self.id)
        if self.twoDimensionalShape:
            x = (a+c)/2.0
            y = (b+d)/2.0
            return Point(x,y)
        else:
            return Point(a,b)
    def getBoundingBox(self):
        """Return the bounding box of the object as a tuple (x1,y1,x2,y2)"""
        if self.canvas:
            bbox = self.canvas.widget.bbox(self.id)
            return (bbox)
        return None
    def move(self, dx, dy, extra=None):
        """move object dx units in x direction and dy units in y direction"""
        if self.canvas:
            self.canvas.widget.move(self.id, dx, dy)
            self.p1 = Point(self.p1.x + dx, self.p1.y + dy)
            if self.twoDimensionalShape:
                self.p2 = Point(self.p2.x + dx, self.p2.y + dy)
            self.canvas.widget.update_idletasks()
    def _move(self, dx, dy, extra=None):
        """Duplicate in case the move() function is overwritten for group moves"""
        if self.canvas:
            self.canvas.widget.move(self.id, dx, dy)
            self.p1 = Point(self.p1.x + dx, self.p1.y + dy)
            if self.twoDimensionalShape:
                self.p2 = Point(self.p2.x + dx, self.p2.y + dy)
            self.canvas.widget.update_idletasks()  
    def jump(self, x, y, extra=None):
        """move object to x,y location"""
        if self.canvas:
            bbox = self.getBoundingBox()
            width = bbox[2]-bbox[0] - 2 #2 is the magic number to keep the box from growing each time
            height = bbox[3]-bbox[1] - 2 # I think 2 works because the bbox is outside the object by 1 pixel
            half_x = width/2
            half_y = height/2
            x1 = x - half_x 
            y1 = y - half_y
            x2 = x1 + width
            y2 = y1 + height
            try: # Four points is the default here. Two point objects (text, pictures) override this function.
                self.canvas.widget.coords(self.id, x1, y1, x2, y2)
            except:
                pass
            else:
                if self.twoDimensionalShape: # May not be possible with the four points aove
                    self.p1 = Point(x,y)
                    self.p2 = Point(x,y)
                else:
                    self.p1 = Point(x1,y1)
                    self.p2 = Point(x2,y2)
                self.canvas.widget.update_idletasks()  

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

    def replaceActions( self, *args ):
        actionCopy = self.actions.copy()
        self.actions.clear()
        self.saveObjectActions(args)
        return actionCopy

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
    def clicked(self, point):
        """If on manual control, Returns true if the object is drawn and the point is inside (an alternative to binding)."""
        "Any action is executed"
        clickedUpon = False
        if all([self.drawn, self.visible]):
            #items = self.canvas.find_closest(point.x, point.y, halo=1)
            x = point.x + 1
            y = point.y + 1
            items = self.canvas.widget.find_overlapping(point.x, point.y, x, y)
            if len(items) > 0:
                for item in items:
                    if item == self.id:
                        clickedUpon = True
                        self.callActions()
                        break
        return clickedUpon                          

class DragInfoClass():
    def __init__(self, object, dictionary):
        self.object = object
        self.canvas = object.canvas
        self.dictionary = {}
        for key,value in dictionary.items():
            self.dictionary[key.lower()] = value

        self.widget = self.dictionary.get('widget', None)
        self.ghostImage = self.dictionary.get('ghosted',None)
        self.cage = self.dictionary.get('cage',[])
        self.restricted = self.dictionary.get('restricted',[])
        self.restrictions = len(self.restricted) > 0 or len(self.cage) > 0
        self.dragActivated = False
        
        def doNothing(self, *args, **kwargs): return
        self.targetFunction = doNothing
        self.missFunction = doNothing
        self.hitFunction = doNothing
        self.targetAcquiredFunction = doNothing
        
        self.target = self.dictionary.get('target',[])
        self.specials = len(self.target) > 0

        if 'targetfunction' in self.dictionary:
            self.targetFunction = self.dictionary['targetfunction']
            self.specials = True
        if 'missfunction' in self.dictionary:
            self.missFunction = self.dictionary['missfunction']
            self.specials = True
        if 'hitfunction' in self.dictionary: 
            self.hitFunction = self.dictionary['hitfunction']
            self.specials = True
        if 'targetacquiredfunction' in self.dictionary:
            self.hitFunction = self.dictionary['targetacquiredfunction']
            self.specials = True

        self.drag_start_x = 0
        self.drag_start_y = 0
        self.dragSetup()

    def dragStarted(self, event):
        self.dragChange = False
        self.drag_start_x = self.canvas.root.winfo_pointerx()
        self.drag_start_y = self.canvas.root.winfo_pointery()
        if ( ghost:= self.ghostImage):
            pass
        #print(f"Start moving by ({self.drag_start_x},{self.drag_start_y})")

    def drag(self, event):
        """drag object to mouse location"""
        if self.canvas:
            dx = event.x_root - self.drag_start_x
            dy = event.y_root - self.drag_start_y
            if dx != 0 or dy != 0:
                if self.restrictions:
                    pass
                self.dragChange = True

                # For combined objects, move all of them using the parent of this class
                self.object.move(dx,dy)
                self.drag_start_x = event.x_root
                self.drag_start_y = event.y_root
                self.canvas.widget.update_idletasks()
                #print(f"      Moving by ({dx},{dy})")

    def dragComplete(self, event):
        # If nothing moved, treat this as a selection
        if not self.dragChange:
            if self.object.selectable: 
                self.object.callActions() # Only call actions that are selectable actions
                #print(f"      Clicked at ({event.x_root},{event.y_root})")
            elif self.specials:
                pass
        #print(f"Stop moving at ({self.drag_start_x},{self.drag_start_y})")
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.dragChange = False

        # Print bounding box in ctrl key is held down
        if self.canvas.development:
            if event is not None:
                if hasattr(event, 'state') and type(event.state) == int:
                    if event.state & 0x0004: # 4 is click, +Control key is 8, +Shift is 12
                        print(self.object)

    def dragSetup(self):
        """Prepare the widget or canvas object to be dragged with the mouse"""
        if not self.dragActivated:
            if self.canvas.bindingAllowed:
                if self.widget is not None: # We are working with a widget, not a canvas item
                    self.dragActivated = True
                    self.widget.unbind('<Button-1>') # Unbind anything already bound to Button-1, like a selection
                    self.widget.bind('<B1-Motion>', self.drag)
                    self.widget.bind('<ButtonPress-1>', self.dragStarted)
                    self.widget.bind('<ButtonRelease-1>', self.dragComplete)
                elif self.object.id is not None:
                    self.dragActivated = True
                    self.canvas.widget.tag_unbind(self.object.id, '<Button-1>') # Unbind anything already bound to Button-1, like a selection
                    self.canvas.widget.tag_bind(self.object.id, '<B1-Motion>', self.drag)
                    self.canvas.widget.tag_bind(self.object.id, '<ButtonPress-1>', self.dragStarted)
                    self.canvas.widget.tag_bind(self.object.id, '<ButtonRelease-1>', self.dragComplete)

    def dragRelease(self):
        """Stop allowing the dragging of the object with the mouse"""
        if self.dragActivated:
            if self.widget is not None: # We are working with a widget, not a canvas item
                self.dragActivated = False
                self.widget.unbind('<B1-Motion>')
                self.widget.unbind('<ButtonPress-1>')
                self.widget.unbind('<ButtonRelease-1>')
            elif self.object.id is not None:
                self.dragActivated = False
                self.canvas.widget.tag_unbind(self.object.id, '<B1-Motion>')
                self.canvas.widget.tag_unbind(self.object.id, '<ButtonPress-1>')
                self.canvas.widget.tag_unbind(self.object.id, '<ButtonRelease-1>')

class ActionInterface():
    """ Interface / Mixin to add functionality to a class"""
    def __init__(self, canvas, dictionary, *args):
        draggingSpecificallyAllowed = dictionary.get('dragging', True)
        self.dragActive = False if 'dragging' not in dictionary else dictionary.pop('dragging')
        config = ""
        for key,value in dictionary.items():   
            try:
                config += f"{key}={str(value)},"
            except:
                continue
        self.extraCode += f"\nAction Interface: dictionary={config}"
        config = ""
        for item in args:
            config += f"{item},"
        self.extraCode += f" arguments={config[:-1]}"
        self.delay = False if 'delay' not in dictionary else dictionary.pop('delay') # Allow delay for example so a color change is visible
        self.toggle = False
        self.group = None if 'group' not in dictionary else dictionary.pop('group') # Object to hold and process radio or check buttons
        self.event = None if 'event' not in dictionary else dictionary.pop('event') # Event info upon button press
        self.invisibleObject = False

        # Drag variables needing initialization
        if not draggingSpecificallyAllowed:
            self.dragActive = draggingSpecificallyAllowed
        elif self.canvas.development: 
            self.dragActive = True
        self.dragInfo = None 
        if self.dragActive:
            self.dragInfo = DragInfoClass(self, dictionary)
            
class Pixel(GenericObject):
    """A Pixel is a single point (a line with 1 width and 1 length) with a fill color.
    Use example: point = Pixel(canvas, (100,100). fill="red")
                      
     REQUIRED ARGUMENTS:
        canvas: The canvas object is placed upon
     ARGUMENTS:
        x,y or tuple or Point: The location of the pixel (x,y)
     DICTIONARY:
        fill: color of pixel
        autoDraw=True: Drawn automatically after creation, otherwise the draw() function is needed
    DEFAULTS:
        fill=Black
    """

    # Class variables:
    allowedParameters = ['fill']

    def __init__(self, canvas, *args, **kwargs):
        """Required to instantiate the class into an object.  Arguments are a list (*args) of unnamed values (Points, tuples, or numbers)
        and they are followed by named values as **kwargs (key word arguments placed into a dictionary)."""
        super().__init__( canvas, *args, **kwargs)
        defaultParameters = dict(fill=canvas.colors["Black"])
        self.initializeShape(defaultParameters, Pixel.allowedParameters )
        
    def draw(self):
        """Tkinter methods to draw the object on the canvas"""
        if not self.drawn: # Only draw once
            self.drawn = True
            x, y = self.p1.x, self.p1.y
            self.id = self.canvas.widget.create_line( x, y, x+1, y+1, **self.configuration )
            if self.name == "": self.name = f"Pixel_({self.id})"
            self.code += f"#Pixel {self.name}:\nself.id = self.canvas.widget.create_line( x, y, x+1, y+1, **self.configuration )"
            self.parameters = f"({x},{y},{x+1},{y+1}"
            super().draw() # Call any parent functions after drawing
    
    def jump(self, x, y, extra=None):
        """move pixel object to x,y location, only x,y needed for movement"""
        if self.canvas:
            try:
                self.canvas.widget.coords(self.id, x, y)
            except:
                pass
            else:
                self.p1 = Point(x,y)
                self.p2 = Point(x,y)
                self.canvas.widget.update_idletasks()  
                        
    def __repr__(self):
        return self.clone()
    def __str__(self):
        return f"Pixel({self.x:.2f}, {self.y:.2f})"
    
    def clone(self):
        """Return a copy of the object that is separate from the original in memory"""
        other = Pixel(self.x,self.y)
        other.configuration = self.configuration.copy()
        return other

class CanvasEntry(GenericObject,ActionInterface):
    """Provide text entry in a window.  The entry is a rectangle with text inside.  The text can be retrieved.
    Entry size must be estimnated as it is not automatically determined.  Example:
        myEntry = CanvasEntry( canvas, Point(100,100), 20) where the 20 is the size of the entry window based on letters.
        myEntry = CanvasEntry( canvas, Point(100,100), Point(100,100)) where the size of the entry window based on pixels.
        If a text editWidth (width) is not provided then one will be guessed based on the width of the Entry/Frame.
        If editWidth (width or editCharacterWidth) is provided then the minimum of it and Entry's actual width is used.
        Note that 3 numbers match a circle's definition so radius may be used to extract as the editWidth variable.
        Use the .getText() function (from an OK button, for example) to retrieve the entered text and .setText() to set it. 
        There are other built-in tkinter functions (such as the <enter> key or any key press) - see tkinter documentation.
        Defaults: fill=LightGray, color=Black, outline=Black, width=1, font=("TKDefaultFont", 16), editWidth of 20 letters.
        This object is in a Tkinter frame and Entry maybe within a canvas.  It is not moveable at this time.
        CanvasEntry does not have a widget or id so you cannot add a function to it, use provided tkinter functions.
    """
    # Class variables:
    allowedParameters = ['fill','color','outline','editwidth','font','state','tags','text']

    def __init__(self, canvas, *args, **kwargs): 
        super().__init__(canvas, *args, **kwargs)
        self.font = ("TKDefaultFont", 16)
        self.localCanvasWindow = None
        self.entryFrame = None
        self.borderWidth = 0
        self.entry = None
        self.text = tk.StringVar(self.canvas.root)
        self.text.set("")
        self.noCopyPaste = self.configuration.pop('noCopyPaste', False) # Disable copy/paste of text in the textbox
        defaultParameters = dict(fill=canvas.colors["LightGray"], color=canvas.colors["Black"], font=("TKDefaultFont", 16))
        
        self.originalColor = canvas.colors[self.configuration.get("fill", "LightGray")]
        self.originalFontColor = canvas.colors[self.configuration.get("color", "Black")]
        self.originalFont = self.configuration.get("font", ("TKDefaultFont", 16))
        self.editWidth = self.configuration.get("editCharacterWidth", self.configuration.get("width",0))

        # Allows for dragging using an ActionInterface with CanvasEntry
        dragging = kwargs.get('dragging', False) # Allow dragging of the textbox
        if dragging: self.borderWidth = 3
        
        self.initializeShape(defaultParameters, CanvasTextEntry.allowedParameters)
        self.setEntryFromDictionary(self.configuration)
        dragDictionary = dict( widget=self.entryFrame, dragging=dragging )
        ActionInterface.__init__(self, canvas, dragDictionary)       
    def bindReturn( self, function):
        self.shape.bind("<Return>", function)    
 
    def draw(self):
        self.entryFrame = tk.Frame(self.canvas.root, borderwidth=self.borderWidth)

        # Calculate the entry width 
        if self.p1 == self.p2: # Single point is the center of the object
            if self.editWidth == 0:  self.editWidth = 20
            
        # A bounding box was provided, insure Entry fits inside using the estimated edit width based on the font
        else:
            weight = "normal" if len(self.originalFont) < 3 else self.originalFont[2].lower()
            family = self.originalFont[0]
            try:
                size = int(self.originalFont[1])
            except:
                size = 16
            quickFont = Font(family=family, size=size, weight=weight)
            quickWidth = quickFont.measure("W")
            letterWidth = max(1,quickWidth/3.6) # Magic number for font size being large
            estimatedAllowedEditWidthInLetters = int( ((self.p2.x - self.p1.x) / letterWidth)-1)
            if self.editWidth == 0:
                self.editWidth = max(estimatedAllowedEditWidthInLetters, 2)
            else: 
                self.editWidth = max(min(estimatedAllowedEditWidthInLetters,self.editWidth), 2)
        
        # Create the entry box. 
        self.shape = tk.Entry(self.entryFrame,
                                width=self.editWidth,
                                textvariable=self.text,
                                bg = self.originalColor,
                                fg = self.originalFontColor,
                                font=self.originalFont)
        self.shape.pack()
        self.shape.focus_set()
        x = self.p1.x
        y = self.p1.y
        self.localCanvasWindow = self.canvas.widget.create_window(x,y,window=self.entryFrame)
        self.canvas.widget.configure(scrollregion=self.canvas.widget.bbox("all")) 
        self.drawn = True
        
        if self.noCopyPaste:
            self.entry.bind('<Control-v>', lambda _:'break')
            self.entry.bind('<Control-c>', lambda _:'break')
        super().draw()

    def undraw(self):
        """Remove and delete the entry, frame, and local canvas"""
        if self.drawn:
            if self.entryFrame is not None: 
                self.entryFrame.destroy() # Destroys all children as well
                self.localCanvasWindow = None
                self.entryFrame = None
                self.shape = None
            self.drawn = False

    def getText(self):
        return self.text.get()

    def move(self, x, y, *args):
        point_x = self.p1.x + x
        point_y = self.p1.y + y
        new_x = point_x #- (self.p2.x-self.p1.x)/2
        new_y = point_y #- (self.p2.y-self.p1.y)/2
        self.p1 = Point(point_x,point_y)
        self.entryFrame.place(x=new_x, y=new_y)

    def getAnchor(self):
        return self.p1.clone()

    def setText(self, t):
        self.text.set(t)

    def setFill(self, color):
        self.fill = self.canvas.colors.get(color, color)
        if self.entry:
            self.entry.config(bg=color)

    def resetFillToOriginalColor(self):
        self.fill = self.originalColor
        if self.entry:
            self.entry.config(bg=self.originalColor)

    def _setFontComponent(self, which, value):
        font = list(self.font)
        font[which] = value
        self.font = tuple(font)
        if self.entry:
            self.entry.config(font=self.font)

    def setFace(self, face):
        self._setFontComponent(0, face)

    def setSize(self, size):
        self._setFontComponent(1,size)

    def setStyle(self, style):
        self._setFontComponent(2,style)

    def setTextColor(self, color):
        self.color = self.canvas.colors.get(color, color) 
        if self.entry:
            self.entry.config(fg=color)
            
    def setEntryFromDictionary(self, dictionary):
        """Dictionary used to set many button characteristics"""
        if len(dictionary) > 0:
            for key in dictionary:
                self.setEntryDetail( key, dictionary[key])
         
    def setEntryDetail( self, attribute, value ):
        entryAttribute = attribute.lower()
        try:
            if entryAttribute in ["fill","fillcolor"]:
                self.fill = value
            elif entryAttribute == "linecolor":
                self.outline = value
            elif entryAttribute == "linewidth":
                self.lineWidth = value
            elif entryAttribute == "text":
                self.text.set(value)
            elif entryAttribute == "name":
                self.name = value
            elif entryAttribute in ["face","font"]:
                self.setFace(value)
            elif entryAttribute == "size":
                self.setSize(value)
            elif entryAttribute in [ "color","fontcolor"]:
                self.setTextColor(value)
            elif entryAttribute == "style":
                self.setStyle(value)
            elif entryAttribute == "editwidth":
                self.editWidth = value
            else:
                pass
                print( f"setEntryDetail: Unknown entry attribute: {entryAttribute}  {value}")
        except:
            pass
            print( f"setEntryDetail: Error on entry attribute: {entryAttribute}  {value}")

    def __repr__(self):
        return self.clone()
    def __str__(self):
        return "Entry({}, {})".format(self.p1, self.editWidth)

    def clone(self):
        other = CanvasTextEntry(self.anchor, self.editWidth)
        other.config = self.config.copy()
        other.text = tk.StringVar()
        other.text.set(self.text.get())
        other.fill = self.fill
        return other
class CanvasTextEntry(GenericObject,ActionInterface):
    """Provide text entry on a canvas.  The entry is a rectangle (frame) with text inside.  The text can be retrieved.
    Entry size must be estimnated as it is not automatically determined.  Example:
        myEntry = CanvasTextEntry( canvas, Point(100,100), 20) where the 20 is the size of the entry window based on letters.
        myEntry = CanvasTextEntry( canvas, Point(100,100), Point(100,100)) where the size of the entry window based on pixels.
        If a text editWidth (width) is not provided then one will be guessed based on the width of the Entry/Frame.
        If editWidth (width or editCharacterWidth) is provided then the minimum of it and Entry's actual width is used.
        Note that 3 numbers match a circle's definition so radius may be used to extract as the editWidth variable.
        Use the .getText() function to retrieve the entered text and .setText() to set it. 
        There are other built-in tkinter functions (such as the <enter> key or any key press) - see tkinter documentation.
        Defaults: fill=LightGray, color=Black, outline=Black, width=1, font=("TKDefaultFont", 16), editWidth of 20 letters.
        This object is in a Tkinter frame and Entry maybe within a canvas.
        CanvasEntry does not have a widget or id so you cannot add a function to it, use provided tkinter functions.
        NOTE: Error checking is not turned on or debugged
        NOTE: Hints and Dates can be added
        NOTE: add class=class to Canvas button
    """
    # Class variables:
    allowedParameters = ['fill','color','outline','editwidth','font','state','tags','text','background','foreground']

    def __init__(self, canvas, *args, **kwargs): 
        super().__init__(canvas, *args, **kwargs)

        # Setup the frame characteristics
        self.tags = kwargs.get('tags', "canvastextbox")
        borderWidth = kwargs.get('borderwidth', 1)
        self.font = ("TKDefaultFont", 16)
        self.boxFormat = dict( sticky="ew")
        self.frameFormat = dict( sticky="full", relief=tk.SOLID, borderwidth=borderWidth, 
                            rowweights=2, columnweights=1)
        
        # Entry characteristics
        self.entry = None
        self.textVariable = tk.StringVar(self.canvas.root)
        self.textVariable.set("")
        self.noCopyPaste = self.configuration.pop('noCopyPaste', False) # Disable copy/paste of text in the textbox
        defaultParameters = dict(fill=canvas.colors["LightGray"], color=canvas.colors["Black"], font=("TKDefaultFont", 16))
        self.originalColor = self.configuration.get("fill", canvas.colors["LightGray"])
        self.originalFontColor = self.configuration.get("color", canvas.colors["Black"])
        self.originalFont = self.configuration.get("font", ("TKDefaultFont", 16))
        self.editWidth = self.configuration.get("editCharacterWidth", self.configuration.get("width",0))

        # Get font information to determine the width of a letter
        weight = "normal" if len(self.originalFont) < 3 else self.originalFont[2].lower()
        family = self.originalFont[0]
        try:
            size = int(self.originalFont[1])
        except:
            size = 16
        quickFont = Font(family=family, size=size, weight=weight)
        quickWidth = quickFont.measure("W")
        if quickWidth == 0: quickWidth = 16 # Fallback in case of error

        # Set up coordinates optionally using font information
        coordinates = canvas.getFourDimensions(args)
        if len(coordinates) == 3:
            self.x, self.y, self.editWidth = coordinates
            self.frameWidth = self.editWidth * quickWidth
            self.height = quickWidth
            x2 = self.x + self.frameWidth
            y2 = self.y + self.height
            self.arguments = [self.x, self.y, x2, y2] # Save new boundry box
        else:
            self.x, self.y, x2, y2 = coordinates
            self.frameWidth = abs(x2-self.x)
            self.editWidth = int( 1 + (self.frameWidth / quickWidth))
            self.height = abs(y2-self.y)

        # Password characteristics
        self._password = ""
        self.hint  = "" # Stores any hint text
        self.showDot = self.configuration.get("showdot", None)
        self.usePassword = self.configuration.get("password", False)
    
        # Error characteristics
        self.errorLabel = None
        if self.errorLabel is None:
            self._originalLabelText = ""
        else:
            self._originalLabelText = self.errorLabel.get()
        self._errorState = False
        self.currentValue = None

        # Allows for dragging using an ActionInterface 
        dragging = kwargs.get('dragging', False) # Allow dragging of the textbox
        if dragging: 
            self.frameFormat['borderwidth'] = max(3, borderWidth)
        
        # Final setup and draw
        self.initializeShape(defaultParameters, CanvasTextEntry.allowedParameters)
        self.setEntryFromDictionary(self.configuration)

        # Once drawn, allow any dragging
        dragDictionary = dict( widget=self.entryFrame.widget, dragging=dragging )
        ActionInterface.__init__(self, canvas, dragDictionary)

    #############################################################################
    # Handling errors or changes in text entry - these occur on key presses and focus out
    # TODO: Implement error checking with provided function parameter (or None) to take current entry as parameter
    # and return error message or either None or empty string if no error. Regex could be handled this
    # way if not a specific feature of the class. A text are needs to be provided below/above the Entry for error
    # messages, and removed when no error or maybe on focus out. A color change could remain until fixed.
    # Errors: Override with specific error checking
    def errorCheck(self):
        pass
    # Errors: Override with specific validity method
    def _on_validate(self, action, result, current, index, char, event):
        valid = True
        return valid
    # Errors: Override with specific error checking
    def errorCheck(self):
        pass       
    # Errors: Override with specific invalidity method (this works for many methods)
    def _on_invalid(self, action, result, current, index, char, event):
        pass
    # if event != 'key':   
    # Errors: turn colors back to their original colors
    def _turnOffErrorColors(self, color="Black"):
        #print(f"Error colors -off- with {color}")
        goodColor = self.colors.get(color, color)
        self.widget.config(foreground=goodColor)
        if self.errorLabel is not None and self.errorLabel.widget is not None:
            self.errorLabel.widget.config(foreground=color)
    # Errors: Turn colors to the error colors
    def _turnOnErrorColors(self, color="Red"):
        #print(f"Error colors ON with {color}")
        goodColor = self.colors.get(color, color)
        self.widget.config(foreground=goodColor)
        if self.errorLabel is not None and self.errorLabel.widget is not None:
            self.errorLabel.widget.config(foreground=color)
    # Errors: Toggle between showing error colors and normal colors
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
            if self.errorLabel is not None and self.errorLabel.widget is not None:
                newLabelMessage = f"{error} {self._originalLabelText}"
                self.errorLabel.widget.config(text=newLabelMessage)

        elif self._errorState: # otherwise, if there was an error but not now
            #print(f"{self.name}: value: {currentValue}, error now over for new?={errorMessageprovided}, current?={self._errorState}, no message provided to ValidityBasisMixin")
            self._turnOffErrorColors(self.canvas.colors["Blue"])
            self._errorState = False
            self.set(self.currentValue)
            if self.errorLabel is not None and self.errorLabel.widget is not None:
                self.errorLabel.widget.config(text=self._originalLabelText)

        else: # No current error and no previous error
            #print(f"{self.name}: value: {currentValue}, never was an error for new?={errorMessageprovided}, current?={self._errorState}, no message provided to ValidityBasisMixin")
            self._turnOffErrorColors()
            self.set(self.currentValue)
    
    #############################################################################
    # Editing: On each letter, check to make sure the edit width is enforced by ignoring extra letters
    def _on_length_validate(self, proposed):
        if len(proposed) <= self.editWidth:
            return True
        else:
            return False

    #############################################################################
    # Passwords: They have no immediate restrictions on characters inputted and they show the spot character
    # TODO: The spot character is imbedded so its width does not match the edit width
    def _on_password_validate(self, action, result, current, index, char, event):
        valid = True
        if event == 'key':
            #self._toggle_error()
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
                        pass
                        #self._toggle_error('Invalid')
        return valid  
    # Passwords: Change past charaters to bullets, leaving just the last char visible
    def _on_password_edit(self, *_):
        visiblePassword = self.textVariable.get()
        length = len(visiblePassword)
        if length > 1:
            newPassword = self.showDot*(length-1) + visiblePassword[-1]
            self.textVariable.set(newPassword)     
    # Passwords: Change all charaters to bullets
    def _focus_out(self, *_):
        visiblePassword = self.textVariable.get()
        length = len(visiblePassword)
        if length > 0:
            newPassword = self.showDot*(length)
            self.textVariable.set(newPassword)   

    #############################################################################
    def draw(self):
        self.entryFrame = _Frame( self.canvas, self.frameFormat, x=self.x, y=self.y, width=self.frameWidth, height=self.height) 
        self.shape = tk.Entry(self.entryFrame.widget,
                                width=self.editWidth,
                                textvariable=self.textVariable) 
        self.shape.configure(
            validate='all',
            validatecommand=(self.shape.register(self._on_length_validate), '%P')
        )
        self.entry = self.shape
        self.code += f"CanvasTextEntry: "
        self.extraCode += """\nself.entryFrame = _Frame( self.canvas, self.frameFormat, x=self.x, y=self.y, width=self.frameWidth, height=self.height) 
        self.shape = tk.Entry(self.entryFrame.widget,
                                width=self.editWidth,
                                textvariable=self.textVariable) 
        self.shape.configure(
            validate='all',
            validatecommand=(self.shape.register(self._on_length_validate), '%P')
        )"""
        self.parameters = f"x={self.x}, y={self.y}, width={self.frameWidth}, height={self.height}, and width={self.editWidth}\n"
        param = ""
        for key, value in self.frameFormat.items():
            param += f"{key}={value},"
        self.parameters += f"self.frameFormat is: {param[:-1]}, self.editWidth={self.editWidth}\n"
        # Password
        if self.usePassword:
            if self.showDot is None: self.showDot = '•' # Calibri bullet character, can't get it larger
            self.shape.config(show=self.showDot) # Show an optional dot instead of the text
            self.textVariable.trace_add('write', self._on_password_edit)
            self.shape.bind('<FocusOut>', self._focus_out)

        # Error detection    
        if self.errorLabel is not None:
            action, result, current, index, char, event = '%d','%P','%s','%i','%S','%V'
            self.shape.configure(
                validate='all', # after idle {%W config -validate %v}
                validatecommand=(self.shape.register(self._on_validate), action, result, current, index, char, event),
                invalidcommand=(self.shape.register(self._on_invalid), action, result, current, index, char, event)
            )    
        
        self.shape.pack()
        self.shape.icursor(tk.END)
        self.shape.focus_set()
        self.drawn = True
        if self.noCopyPaste:
           self.entry.bind('<Control-v>', lambda _:'break')
           self.entry.bind('<Control-c>', lambda _:'break')
        super().draw()

    def undraw(self):
        """Remove and delete the entry, frame, and local canvas"""
        if self.drawn:
            if self.entryFrame is not None: 
                self.entryFrame.destroy() # Destroys all children as well
                self.localCanvasWindow = None
                self.entryFrame = None
                self.shape = None
            self.drawn = False

    def getText(self):
        return self.textVariable.get()

    def setText(self, t):
        self.textVariable.set(t)
    text = property(getText,setText)    
    def clear(self):
        self.setText("")   
         
    def move(self, x, y, *args):
        self.p1 = Point(self.p1.x+x,self.p1.y+y)
        self.entryFrame.widget.place(x=self.p1.x, y=self.p1.y)

    def getAnchor(self):
        return self.p1.clone()

    def setFill(self, color):
        self.fill = self.canvas.colors.get(color, color)
        if self.entry:
            self.entry.config(bg=color)

    def resetFillToOriginalColor(self):
        self.fill = self.originalColor
        if self.entry:
            self.entry.config(bg=self.originalColor)

    def _setFontComponent(self, which, value):
        newFontList = [*self.font]
        font = list(self.font)
        font[which] = value
        self.font = tuple(font)
        if self.entry:
            self.entry.config(font=self.font)

    def setFont(self, fontTuple):
        self.font = fontTuple
        if self.entry:
            self.entry.config(font=self.font)

    def setFace(self, face):
        self._setFontComponent(0, face)

    def setSize(self, size):
        self._setFontComponent(1,size)

    def setStyle(self, style):
        self._setFontComponent(2,style)

    def setTextColor(self, color):
        self.color = self.canvas.colors.get(color, color) 
        if self.entry:
            self.entry.config(fg=color)

    def setLineWidth(self, width):
        self.lineWidth = width
        if self.entry:
            self.entry.config(borderwidth=width)

    def setEntryFromDictionary(self, dictionary):
        """Dictionary used to set many button characteristics"""
        if len(dictionary) > 0:
            for key in dictionary:
                self.setEntryDetail( key, dictionary[key])
         
    def setEntryDetail( self, attribute, value ):
        entryAttribute = attribute.lower()
        try:
            if entryAttribute in ["fill","fillcolor","background","bg"]:
                self.setFill(value)
            elif entryAttribute == "linecolor":
                self.outline = value
            elif entryAttribute == "linewidth":
                self.setLineWidth(value)
            elif entryAttribute == "text":
                self.textVariable.set(value)
            elif entryAttribute == "name":
                self.name = value
            elif entryAttribute in "face":
                self.setFace(value)
            elif entryAttribute in "font":
                self.setFont(value)
            elif entryAttribute == "size":
                self.setSize(value)
            elif entryAttribute in [ "color","fontcolor","foreground","fg"]:
                self.setTextColor(value)
            elif entryAttribute == "style":
                self.setStyle(value)
            elif entryAttribute == "editwidth":
                self.editWidth = value
            else:
                pass
                print( f"setEntryDetail: Unknown entry attribute: {entryAttribute}  {value}")
        except:
            pass
            print( f"setEntryDetail: Error on entry attribute: {entryAttribute}  {value}")

    def __repr__(self):
        return self.clone()
    def __str__(self):
        width=self.frameWidth
        height=self.height
        halfHeight = height//2
        halfWidth = width//2
        bbox = (self.p1.x-halfWidth, self.p1.y-halfHeight, self.p1.x+halfWidth, self.p1.y+halfHeight)
        return "Entry {} at {} with edit width of {} centered at {})".format(self.tags, bbox, self.editWidth, self.p1)

    def clone(self):
        other = CanvasTextEntry(self.anchor, self.editWidth)
        other.config = self.config.copy()
        other.text = tk.StringVar()
        other.text.set(self.textVariable.get())
        other.fill = self.fill
        return other


class Arc(GenericObject):
    """An Arc is an outlines & filled (or None color) arc (extent and start angles provided) with a modifiable border.
    The three style(s)) are tk.PIESLICE, tk.CHORD, and tk.ARC.
    Use example: arc = Arc( canvas, (100,100),(120,120), fill="red", outline="black", width=2, extent=90.0, start=0.0)
                      
     REQUIRED ARGUMENTS:
        canvas: The canvas object is placed upon
     ARGUMENTS:
        x,y or tuple or Point: The location of one point for the box surrounding the circle
        x,y or tuple or Point: The location of the other point for the box
     DICTIONARY:
        fill: color of object
        Outline characteristics of 'outline','width','dash','dashoffset','joinstyle','splinesteps','stipple'
        'smooth=True': smoothes the outline of corners (used in squaricles)
        state: 'normal' or 'hidden' for the visibility of the object
        tags: list of tags for the object used by Tkinter
        autoDraw=True: Drawn automatically after creation, otherwise the draw() function is needed
        extent: The angle in degrees of the arc
        start: The angle in degrees of the start of the arc
    DEFAULTS:
        start=0.0, extent=90.0, fill=None, outline=Black, width=1
        """
    # Class variables:
    allowedParameters = ['fill','outline','width','dash','dashoffset','joinstyle','smooth','splinesteps','state','stipple','tags','extent','start','start','extent']

    def __init__(self, canvas, *args, **kwargs):
        super().__init__(canvas, *args, **kwargs)
        defaultParameters = dict(fill=None, outline=canvas.colors["Black"], width=1, extent=90.0, start=0.0)
        self.initializeShape(defaultParameters, Arc.allowedParameters )

    def draw(self):
        if not self.drawn: # Only draw once
            self.drawn = True
            self.id = self.canvas.widget.create_arc( self.p1.x, self.p1.y, self.p2.x, self.p2.y, **self.configuration )
            if self.name == "": self.name = f"Arc_({self.id})"  
            self.code += f"#Arc {self.name}:\nself.id = self.canvas.widget.create_arc( self.p1.x, self.p1.y, self.p2.x, self.p2.y"
            self.parameters = f"({self.p1.x},{self.p1.y},{self.p2.x},{self.p2.y}"   
            super().draw()
        
    def __repr__(self):
        return self.clone()
    def __str__(self):
        extent = self.configuration['extent'] 
        start = self.configuration['start'] 
        text = super().__str__()
        text = f"Arc {text}, extent:{extent:.2f}, start: {start:.2f}"
        return text
    
    def clone(self):
        other = Arc(self.p1, self.p2)
        other.configuration = self.configuration.copy()
        return other
class Line(GenericObject):
    """A Line is a line with a modifiable thickness, color, and pattern.
    Use example: line = Line( canvas, (100,100),(120,120), fill="red", outline="black", width=2)
                      
     REQUIRED ARGUMENTS:
        canvas: The canvas object is placed upon
     ARGUMENTS:
        x,y or tuple or Point: The location of one end of the line
        x,y or tuple or Point: The location of other end of the line
     DICTIONARY:
        fill: color of object
        Outline characteristics of 'outline','width','dash','dashoffset','joinstyle','splinesteps','stipple'
        'smooth=True': smoothes the outline of corners (used in squaricles)
        state: 'normal' or 'hidden' for the visibility of the object
        tags: list of tags for the object used by Tkinter
        autoDraw=True: Drawn automatically after creation, otherwise the draw() function is needed
    DEFAULTS:
        fill=Black, width=1
        """
    # Class variables:
    allowedParameters = ['fill','outline','width','dash','arrow','dashoffset','joinstyle','smooth','splinesteps','state','stipple','tags']

    def __init__(self, canvas, *args, **kwargs):
        super().__init__(canvas, *args, **kwargs)
        defaultParameters = dict(fill=canvas.colors["Black"], width=1)
        self.initializeShape(defaultParameters, Line.allowedParameters )
    
    def draw(self):
        if not self.drawn: # Only draw once
            self.drawn = True
            self.id = self.canvas.widget.create_line( (self.p1.x, self.p1.y), (self.p2.x, self.p2.y), **self.configuration )
            if self.name == "": self.name = f"Line_({self.id})"
            self.code += f"#Line {self.name}:\nself.id = self.canvas.widget.create_arc( self.p1.x, self.p1.y, self.p2.x, self.p2.y"
            self.parameters = f"({self.p1.x},{self.p1.y},{self.p2.x},{self.p2.y}" 
            super().draw()
               
    def __repr__(self):
        return self.close()
    def __str__(self):
        text = super().__str__()
        return f"Line {text})"

    def clone(self):
        other = Line(self.p1, self.p2)
        other.configuration = self.configuration.copy()
        other.arguments = self.arguments.copy()
        return other
class MultipleLines(GenericObject):
    """A MultipleLines is a series of lines (based on a list of points) with a modifiable thickness, color, and pattern.
    Use example: shape = MultipleLines( canvas, (100,100),(120,120),(130,130) fill="red", outline="black", width=2)
                      
     REQUIRED ARGUMENTS:
        canvas: The canvas object is placed upon
     ARGUMENTS:
        Some number of x,y or tuple or Point: The location of one point.  They are all linked.
     DICTIONARY:
        fill: color of object
        Outline characteristics of 'outline','width','dash','dashoffset','joinstyle','splinesteps','stipple'
        'smooth=True': smoothes the outline of corners (used in squaricles)
        state: 'normal' or 'hidden' for the visibility of the object
        tags: list of tags for the object used by Tkinter
        autoDraw=True: Drawn automatically after creation, otherwise the draw() function is needed
    DEFAULTS:
        fill=Black, width=1
        """
    # Class variables:
    allowedParameters = ['fill','outline','width','dash','arrow','capstyle','dashoffset','joinstyle','smooth','splinesteps','state','stipple','tags']

    def __init__(self, canvas, *args, **kwargs):
        super().__init__(canvas, *args, **kwargs)
        defaultParameters = dict(fill=canvas.colors["Black"], width=1)
        self.initializeShape(defaultParameters, MultipleLines.allowedParameters, evenPointsOnly=False )

    def draw(self):
        if not self.drawn: # Only draw once
            self.drawn = True
            self.id = self.canvas.widget.create_line( *self.arguments, **self.configuration )
            if self.name == "": self.name = f"Multilines_({self.id})"
            self.code += f"#Multiple Lines {self.name}:\nself.id = self.canvas.widget.create_line( *self.arguments, **self.configuration )"
            params = "("
            for item in self.arguments:
                params += f"{str(item)},"
            self.parameters = params[:-1] + ")"
            super().draw()

    def __repr__(self):
        return self.clone()
    def __str__(self):
        text = super().__str__()
        length = len(self.arguments)
        bbox = self.getBoundingBox()
        x = bbox[0] + (bbox[2]-bbox[0])//2
        y = bbox[1] + (bbox[3]-bbox[1])//2
        return f"Multiple Lines {text} of {length} points centered on ({x:.2f}, {y:.2f})"
    
    def clone(self):
        other = Line(self.p1, self.p2)
        other.configuration = self.configuration.copy()
        other.arguments = self.arguments.copy()
        return other    

class Rectangle(GenericObject):
    """A Rectangle is a filled (or None color) rectangle witha  modifiable border.
    Use example: rectangle = Rectangle(canvas, (100,100),(120,120), fill="red", outline="black", width=2)
                      
     REQUIRED ARGUMENTS:
        canvas: The canvas object is placed upon
     ARGUMENTS:
        x,y or tuple or Point: The location of upper left corner
        x,y or tuple or Point: The location of lower right corner
     DICTIONARY:
        fill: color of object
        Outline characteristics of 'outline','width','dash','dashoffset','joinstyle','splinesteps','stipple'
        'smooth=True': smoothes the outline of corners (used in squaricles)
        state: 'normal' or 'hidden' for the visibility of the object
        tags: list of tags for the object used by Tkinter
        autoDraw=True: Drawn automatically after creation, otherwise the draw() function is needed
    DEFAULTS:
        fill=None, outline=Black, width=1
        """      
    # Class variables:
    allowedParameters = ['fill','outline','width','dash','dashoffset','joinstyle','smooth','splinesteps','state','stipple','tags']
    
    def __init__(self, canvas, *args, **kwargs):
        super().__init__(canvas, *args, **kwargs)
        defaultParameters = dict(fill=None, outline=canvas.colors["Black"], width=1)
        self.initializeShape(defaultParameters, Rectangle.allowedParameters )
 
    def draw(self):
        """Tkinter methods to draw the object on the canvas"""
        if not self.drawn: # Only draw once
            self.drawn = True
            self.id = self.canvas.widget.create_rectangle( self.p1.x, self.p1.y, self.p2.x, self.p2.y, **self.configuration )
            if self.name == "": self.name = f"Box_({self.id})"
            self.code += f"#Rectangle {self.name}:\nself.id = self.canvas.widget.create_rectangle( self.p1.x, self.p1.y, self.p2.x, self.p2.y"
            self.parameters = f"({self.p1.x},{self.p1.y},{self.p2.x},{self.p2.y}"   
            super().draw()
        
    def __repr__(self):
        return self.clone()
    def __str__(self):
        text = super().__str__()
        return f"Rectangle {text})"
            
    def clone(self):
        other = Rectangle(self.p1, self.p2)
        other.configuration = self.configuration.copy()
        return other
class Circle(GenericObject):
    """A Circle is a filled (or None color) circle with a modifiable border based on an Oval with identical points.
    Use example: circle = Circle(canvas, (100,100),50, fill="red", outline="black", width=2)
                      
     REQUIRED ARGUMENTS:
        canvas: The canvas object is placed upon
     ARGUMENTS:
        x,y or tuple or Point: The location of circle center
        radius: The radius of the circle
     DICTIONARY:
        fill: color of object
        Outline characteristics of 'outline','width','dash','dashoffset','joinstyle','splinesteps','stipple'
        'smooth=True': smoothes the outline of corners (used in squaricles)
        state: 'normal' or 'hidden' for the visibility of the object
        tags: list of tags for the object used by Tkinter
        autoDraw=True: Drawn automatically after creation, otherwise the draw() function is needed
    DEFAULTS:
        fill=None, outline=Black, width=1
        """
    # Class variables:
    allowedParameters=['fill','outline','width','dash','dashoffset','smooth','splinesteps','state','stipple','tags']

    def __init__(self, canvas, *args, **kwargs):
        super().__init__(canvas, *args, **kwargs) # kwargs placed into self.configuration, args into self.arguments
        defaultParameters = dict(fill=None, outline=canvas.colors["Black"], width=1)
        self.initializeShape(defaultParameters, Circle.allowedParameters )
 
    def __repr__(self):
        return self.clone()
    def __str__(self):
        text = super().__str__()
        return f"Circle {text} with center: {self.p1}, radius: {self.radius:.2f})"

    def draw(self):        
        if not self.drawn: # Only draw once
            self.drawn = True
            self.id = self.canvas.widget.create_oval( (self.p1.x, self.p1.y), (self.p2.x, self.p2.y), **self.configuration )
            if self.name == "": self.name = f"Circle_({self.id})"
            self.code += f"#Circle {self.name}:\nself.id = self.canvas.widget.create_oval( self.p1.x, self.p1.y, self.p2.x, self.p2.y"
            self.parameters = f"({self.p1.x},{self.p1.y},{self.p2.x},{self.p2.y}"  
            super().draw()
        
    def clone(self):
        other = Oval(self.p1, self.p2)
        other.configuration = self.configuration.copy()
        return other

    def clicked(self, point):
        """OVERRIDE: Returns true if the object is drawn and the point is inside (an alternative to binding)."""
        "Any action is executed.  Circles with negative points in their bounding box do not .find_overlapping() correctly."
        clickedUpon = False
        if self.drawn:
            #items = self.canvas.find_closest(point.x, point.y, halo=1)
            x = point.x + 1
            y = point.y + 1
            items = self.canvas.widget.find_overlapping(point.x, point.y, x, y)

            # Circles with negative points in their bounding box do not select correctly
            if len(items) == 0:
                if self.p1.x < 0 or self.p2.x < 0 or self.p1.y <0 or self.p2.y <0:
                    centerPoint = self.getCenter()
                    if centerPoint is not None: 
                        distance = math.sqrt((centerPoint.x - point.x)**2 + (centerPoint.y - point.y)**2)
                        if distance <= self.radius:
                            items = [self.id]
            
            # Found at least one, now check if it is the circle
            if len(items) > 0:
                for item in items:
                    if item == self.id:
                        clickedUpon = True
                        if len(self.actions) > 0:
                            for function in self.actions:
                                if isinstance(function, list):
                                    for nestedFunction in function:
                                        if nestedFunction is not None:
                                            nestedFunction(self)
                                else:
                                    function(self)
                        break
        return clickedUpon

class Oval(GenericObject):
    """An Oval is a filled (or None color) oval (2 center points) with a modifiable border.
    Use example: oval = Oval( canvas, (100,100),(120,120), fill="red", outline="black", width=2)
    A bounding box is actually used to build the oval (no automatic rotation)
                      
     REQUIRED ARGUMENTS:
        canvas: The canvas object is placed upon
     ARGUMENTS:
        x,y or tuple or Point: The location of upper left bounding box
        x,y or tuple or Point: The location of lower right bounding box
     DICTIONARY:
        fill: color of object
        Outline characteristics of 'outline','width','dash','dashoffset','joinstyle','splinesteps','stipple'
        'smooth=True': smoothes the outline of corners (used in squaricles)
        state: 'normal' or 'hidden' for the visibility of the object
        tags: list of tags for the object used by Tkinter
        autoDraw=True: Drawn automatically after creation, otherwise the draw() function is needed
    DEFAULTS:
        fill=None, outline=Black, width=1
        """
    def __init__(self, canvas, *args, **kwargs):
        super().__init__(canvas, *args, **kwargs)
        defaultParameters = dict(fill=None, outline=canvas.colors["Black"], width=1)
        self.initializeShape(defaultParameters, Circle.allowedParameters )

    def draw(self):
        if not self.drawn: # Only draw once
            self.drawn = True
            self.id = self.canvas.widget.create_oval( (self.p1.x, self.p1.y), (self.p2.x, self.p2.y), **self.configuration )
            if self.name == "": self.name = f"Oval_({self.id})"
            self.code = f"#Oval {self.name}:\nself.id = self.canvas.widget.create_oval( self.p1.x, self.p1.y, self.p2.x, self.p2.y"
            self.parameters = f"({self.p1.x},{self.p1.y},{self.p2.x},{self.p2.y}"  
            super().draw()
        
    def __repr__(self):
        return self.clone()
    def __str__(self):
        text = super().__str__()
        return "Oval {text}"
    
    def clone(self):
        other = Oval(self.p1, self.p2)
        other.configuration = self.configuration.copy()
        return other

class Polygon(GenericObject):
    """A Polygon is a filled (or None color) polygon (based on a list of points) with a modifiable border.
    Use example: shape = Polygon( canvas, (100,100),(120,120),(130,130) fill="red", outline="black", width=2)
                      
     REQUIRED ARGUMENTS:
        canvas: The canvas object is placed upon
     ARGUMENTS:
        Some number of x,y or tuple or Point: The location of one point.
     DICTIONARY:
        fill: color of object
        Outline characteristics of 'outline','width','dash','dashoffset','joinstyle','splinesteps','stipple'
        'smooth=True': smoothes the outline of corners (used in squaricles)
        state: 'normal' or 'hidden' for the visibility of the object
        tags: list of tags for the object used by Tkinter
        squaricle=True: Make a squaricle polygon using the two provided points
        autoDraw=True: Drawn automatically after creation, otherwise the draw() function is needed
    DEFAULTS:
        fill=Black, outline=Black, width=1
        """
    # Class variables:
    allowedParameters = ['fill','outline','width','dash','arrow','capstyle','dashoffset','joinstyle','smooth','splinesteps','state','stipple','tags']

    def __init__(self, canvas, *args, **kwargs):
        super().__init__(canvas, *args, **kwargs)
        self._adjustShapeForSquaricle()
        defaultParameters = dict(fill=canvas.colors["Black"], outline=canvas.colors["Black"], width=1)
        self.initializeShape(defaultParameters, Polygon.allowedParameters)

    def draw(self):
        if not self.drawn: # Only draw once
            self.drawn = True
            self.id = self.canvas.widget.create_polygon( *self.arguments, **self.configuration )
            if self.name == "": self.name = f"Poly_({self.id})"
            self.code += f"#Polygon {self.name}:\nself.id = self.canvas.widget.create_polygon( *self.arguments, **self.configuration )"
            params = "("
            for item in self.arguments:
                params += f"str{item},"
            self.parameters = params[:-1] + ")"
            super().draw()
                      
    def __repr__(self):
        return self.clone()
    def __str__(self):
        text = super().__str__()
        length = len(self.arguments)
        return f"Polygon {text} with {length} points centered on ({self.p1.x:.2f}, {self.p1.y:.2f})"
    
    def clone(self):
        other = Polygon(self.p1, self.p2)
        other.configuration = self.configuration.copy()
        other.arguments = self.arguments.copy()
        return other
    
    def squaricleList(point1, point2):
        ''' Used to make a squaricle shape (rounded rectangle common for buttons).  Example:
        shape = Polygon.squaricleList( Point(100,100),Point(120,220) ).
        NOTE: This function can be called ffrom other classes or code.        
        '''
        p1 = Point( round(point1.x,0), round(point1.y,0) ) # round() used to prevent floating point errors in drawinf lines
        p2 = Point( round(point2.x,0), round(point1.y,0) )
        p3 = Point( round(point2.x,0), round(point2.y,0) )
        p4 = Point( round(point1.x,0), round(point2.y,0) )
        step = 20
        if (p2.x - p1.x)/4 < step: step = (p2.x - p1.x)/4
        if (p3.y - p2.y)/4 < step: step = (p3.y - p2.y)/4
        polygonList = [(p1.x,p1.y), 
            (p1.x+step,p1.y),(p2.x-step,p1.y), (p2.x,p2.y),
            (p2.x,p2.y+step), (p2.x,p3.y-step), (p3.x,p3.y),
            (p3.x-step,p3.y),(p4.x+step,p3.y),(p4.x,p4.y),
            (p4.x,p4.y-step),(p4.x,p1.y+step)]
        return polygonList
    squaricleList = staticmethod(squaricleList)

    def _adjustShapeForSquaricle(self):
        """Check for a squaricle shape and replace it with a list of points"""
        if "squaricle" in self.configuration and len(self.arguments) == 2:
            self.configuration['smooth'] = True
            self.arguments = self.squaricleList(self.arguments[0], self.arguments[1])

    def _rotatePolygon(points, angle, centerPoint): # stackOverflow by PM 2Ring
        """Rotate a list of points counterclockwise by a given angle around a given center.
        Only works on polygons, so all objects with a bounding box must be converted to a polygon
        before rotation.  Example: 
            rotatedPoints = self.poly._rotatePolygon(old_points, 45, center)
            use the self.canvas.coords( object.id, *rotatedPoints ) 
        """
        angle = math.radians(angle)
        cos_val = math.cos(angle)
        sin_val = math.sin(angle)
        cx = centerPoint.x
        cy = centerPoint.y
        new_points = []
        for x_old, y_old in points:
            x_old -= cx
            y_old -= cy
            x_new = x_old * cos_val - y_old * sin_val
            y_new = x_old * sin_val + y_old * cos_val
            new_points.append((x_new + cx, y_new + cy))
        return new_points
    _rotatePolygon = staticmethod(_rotatePolygon)
    
    def rotate(self, angle, center=None):
        """Rotate the object by angle degrees counterclockwise around center.  
        If center is None if you rotate from a non-center point, use the center of the object."""
        if center is None:
            center = Point(self.p1.x + abs(self.p2.x-self.p1.x)/2, self.p1.y + abs(self.p2.y-self.p1.y)/2)
        self.arguments = Polygon._rotatePolygon(self.arguments, angle, center)
        position = []
        for tuple in self.arguments:
            position.append(tuple[0])
            position.append(tuple[1])
        self.canvas.widget.coords(self.id, *position)
        self.canvas.update()

    def jump(self, x, y):
        """Move the object to a new location based on the center of the object being at (x,y)"""
        center = Point(self.p1.x + abs(self.p2.x-self.p1.x)/2, self.p1.y + abs(self.p2.y-self.p1.y)/2)
        dx = x - center.x
        dy = y - center.y
        self.move(dx, dy) # Jump does not work well with a polygon

class Squaricle(Polygon):
    """A SquariclePolygon is a polygon in the shape of a squaricle (rounded rectangle).
    Use example: squaricle = SquariclePolygon(canvas, (100,100),(120,120), fill="red", outline="black", width=2)
                      
     REQUIRED ARGUMENTS:
        canvas: The canvas object is placed upon
     ARGUMENTS:
        x,y or tuple or Point: The location of upper left corner
        x,y or tuple or Point: The location of lower right corner
     DICTIONARY:
        fill: color of object
        Outline characteristics of 'outline','width','dash','dashoffset','joinstyle','splinesteps','stipple'
        'smooth=True': smoothes the outline of corners (used in squaricles)
        state: 'normal' or 'hidden' for the visibility of the object
        tags: list of tags for the object used by Tkinter
        autoDraw=True: Drawn automatically after creation, otherwise the draw() function is needed
    DEFAULTS:
        fill=None, outline=Black, width=1
        """
    def __init__(self, canvas, *args, **kwargs):
        kwargs['squaricle'] = True
        super().__init__(canvas, *args, **kwargs)   
        self.code += f"#Squaricle-"

    def __str__(self):
        text = super().__str__()
        return f"Squaricle {text})"
class Text(GenericObject):
    """A Text is a string of text with a modifiable font, size, and color.  
    Anchor determines 2D justication. Example of anchor: 
    Font is in quotes and is the "family size styles". All fonts and sizes available on the computer are
    allowed. Styles include bold, italic.  Default system fonts begin with "Tk" and end with "Font";
       Caption, Default, Fixed, Heading, Icon, Menu, SmallCaption, Text, Toooltip.
    For color use the standard "fill" or "color" if it interferes with object fill.
    Use example: text = Text(canvas, Point(100,100), anchor='w', text="Hello World!", 
            font="Times 20 bold", fill="red")
                      
     REQUIRED ARGUMENTS:
        canvas: The canvas object is placed upon
     ARGUMENTS:
        x,y or tuple or Point: The location of the anchor point for the text.
     DICTIONARY:
        text: Text to display
        fill or color: color of text
        font: font of text and its size and any styling (ex: Times 16 Bold)
        anchor: ["center","w","e","s","n","sw","se","nw","ne"] for 2D justification
        angle: New feature to angle text, many not work with any or all fonts
        autoDraw=True: Drawn automatically after creation, otherwise the draw() function is needed
    DEFAULTS:
        anchor=center, fill=Black, font=Times 12, angle=0
        """
    # Class variables:
    defaultParameters = dict(anchor='center')
    allowedParameters = ["fill","font","anchor","angle","width","justify"]

    def __init__(self, canvas, *args, **kwargs):
        super().__init__(canvas, *args, **kwargs)
        if canvas.darkModeOn():
            self.configuration['fg'] = canvas.colors["White"]
        self._text = ""
        if 'text' in self.configuration: 
            self._text = self.configuration['text']
        if 'color' in self.configuration:
            providedColor = self.configuration['color']
            goodColor = self.canvas.colors.get(providedColor, providedColor)
            self.configuration['fill'] = goodColor
        self.noCopyPaste = self.configuration.pop('noCopyPaste', False) # Disable copy/paste of text in the textbox
        self.initializeShape(Text.defaultParameters, Text.allowedParameters)
        self.anchor = self.configuration['anchor'] 

    # Property is not working yet so both pairs are available
    def setTextColor(self, color):
        goodColor = self.canvas.colors.get(color, color) 
        self.reconfigure('fill', goodColor)
    def getTextColor(self):
        return self.configuration.get('fill',self.canvas.colors["Black"])
    def _setTextColor(self, color):
        goodColor = self.canvas.colors.get(color, color) 
        self.reconfigure('fill', goodColor)
    def _getTextColor(self):
        return self.configuration.get('fill',self.canvas.colors["Black"])
    color = property(_getTextColor, _setTextColor)

    # Property is not working yet so both pairs are available
    def setFont(self, font):
        self.reconfigure('font', font)
    def getFont(self):
        return self.configuration.get('font',"")

    def _setFont(self, font):
        self.reconfigure('font', font)
    def _getFont(self):
        return self.configuration.get('font',"")
    font = property(_getFont, _setFont)
    
    # Property is not working yet so both pairs are available
    def setText(self, text):
        self._text = text
        self.reconfigure('text', text)
    def getText(self):
        return self._text
    def _setText(self, text):
        self._text = text
        self.reconfigure('text', text)
    def _getText(self):
        return self._text
    text = property(_getText, _setText)

    def setFontSize(self, size):
        """Set text size to size"""
        font = self.configuration.get('font',"")
        partsOfTheFont = font.split(" ")
        if len(partsOfTheFont) == 1: partsOfTheFont[0] = 'Calibri'
        if len(partsOfTheFont) < 2: partsOfTheFont.append('12')
        if len(partsOfTheFont) < 3: partsOfTheFont.append('normal')
        newFont = f"{partsOfTheFont[0]} {size} {partsOfTheFont[2]}"
        self.setFont(newFont)

    def draw(self):
        if not self.drawn: # Only draw once
            self.drawn = True
            self.id = self.canvas.widget.create_text( (self.p1.x, self.p1.y), text=self.text, **self.configuration )
            if self.name == "": self.name = f"Text_({self.id})"
            self.code += f"#Text {self.name}:\nself.id = self.canvas.widget.create_text( self.p1.x, self.p1.y, text=self.text, **self.configuration )"
            self.parameters = f"({self.p1.x},{self.p1.y}, text='{self.text}'"  
            super().draw()

    def undraw(self):
        self._text = ""
        super().undraw()
    
    def details(self, font=None, text=None, width=0, buffer=0):
        """Return the characteristics of any provided text object or this text object if nothing is passed in"""
        useFont = self.configuration['font'] if font is None else font
        useText = self.text if text is None else text
        partsOfTheFont = useFont.split(" ")
        if len(partsOfTheFont) == 1 and len(partsOfTheFont[0])==0: partsOfTheFont[0] = "TKDefaultFont"
        if len(partsOfTheFont) < 2: partsOfTheFont.append('12')
        if len(partsOfTheFont) < 3: partsOfTheFont.append('normal')
        quickFont = Font(family=partsOfTheFont[0], size=int(partsOfTheFont[1]), weight=partsOfTheFont[2])
        letterHeight = quickFont.metrics("linespace")
        letterWidth = quickFont.measure("W")
        length = quickFont.measure(useText)

        useWidth = length + buffer if width == 0 else min(width, length + buffer)
        bufferedWidth =  min(useWidth-buffer, length)
        lines = 1
        if width > 0 and length > useWidth:
            lines += length//useWidth
        newLines = text.split("\n")
        if len(newLines) > lines: # New lines can count as more lines than they look
            lines = len(newLines)
        height = lines * letterHeight

        # Save everything into the dictionary
        dictionary = quickFont.actual()
        dictionary['font'] = useFont
        dictionary['letterHeight'] = letterHeight
        dictionary['letterWidth'] = letterWidth
        dictionary['length'] = length
        dictionary['width'] = useWidth
        dictionary['bufferedWidth'] = bufferedWidth
        dictionary['height'] = height
        dictionary['lines'] = lines
        return dictionary

    def fontStats(text, font):
        """Return details about the font.  Does not use self"""
        partsOfTheFont = font.split(" ")
        if len(partsOfTheFont) == 1 and len(partsOfTheFont[0])==0: partsOfTheFont[0] = "TKDefaultFont"
        if len(partsOfTheFont) < 2: partsOfTheFont.append('12')
        if len(partsOfTheFont) < 3: partsOfTheFont.append('normal')
        quickFont = Font(family=partsOfTheFont[0], size=int(partsOfTheFont[1]), weight=partsOfTheFont[2])
        letterWidth = quickFont.measure("W")
        letterHeight = quickFont.metrics("linespace")
        length = quickFont.measure(text)
        return( letterWidth, letterHeight, length)
       
    def jump(self, x, y, extra=None):
        """move text object to x,y location, only x,y needed for movement"""
        if self.canvas:
            try:
                self.canvas.widget.coords(self.id, x, y)
            except:
                pass
            else:
                self.p1 = Point(x,y)
                self.p2 = Point(x,y)
                self.canvas.widget.update_idletasks()  
                 
    def __repr__(self):
        return self.clone()
    def __str__(self):
        text = super().__str__()
        return f"Text {text} with anchor {self.anchor} centered at {self.p1}: '{self.text}'"
       
    def clone(self):
        other = Text(self.p1)
        other.text = self.text
        other.anchor = self.anchor
        other.configuration = self.configuration.copy()
        return other
   
class Image(GenericObject):
    """An Image is a picture (based on a full url) with a modifiable size and anchor.  
    Anchor determines 2D justication.
    Example for anchor: anchor=tk.NW, anchor=tk.CENTER, anchor=tk.SW   Note these are actually text values
    Use example: image = Image( canvas, Point(100,100), anchor='center',url="https://www.python.org/static/community_logos/python-logo-master-v3-TM.png")
                      
     REQUIRED ARGUMENTS:
        canvas: The canvas object is placed upon
     ARGUMENTS:
        x,y or tuple or Point: The location of the anchor point for the image.
     DICTIONARY:
        url: URL of the image -or- one or both of the following:
        file: file name of the picture, can be "" if path is provided
        path: path to get to the picture file, can contain the file name
        anchor: ["center","w","e","s","n","sw","se","nw","ne"] for 2D justification
        state: 'normal' or 'hidden' for the visibility of the object
        tags: list of tags for the object used by Tkinter
        width: for the picture
        height: for the picture
        autoDraw=True: Drawn automatically after creation, otherwise the draw() function is needed
    DEFAULTS:
        None
        """
    # Class variables:
    defaultParameters = dict(anchor=tk.CENTER)
    allowedParameters = ['anchor','state','tags','width','height']

    def __init__(self, canvas, *args, **kwargs):
        GenericObject.__init__(self, canvas, *args, **kwargs)
        # Given several options, determine the full path to to file
        self.url = self.configuration['url'] if 'url' in self.configuration else ""
        self.file = self.configuration['file'] if 'file' in self.configuration else ""
        self.path = self.configuration['path'] if 'path' in self.configuration else "" # CWD if none
        self.fullPath = self.setPathToImageFile()
        if self.fullPath is None:
            self.img = None
            self.image = self.configuration['image'] if 'image' in self.configuration else None
        elif canvas.usePIL:
            self.img = PILImage.open(self.fullPath)
            self.image = ImageTk.PhotoImage(self.img) # self.image = tk.PhotoImage(file=self.fullPath)
        else:
            self.img = None
            self.image = tk.PhotoImage(file=self.fullPath)
        self.initializeShape(Image.defaultParameters, Image.allowedParameters)
        if self.image is None:
            self.imageWidth = 0
            self.imageHeight = 0
        else:
            self.imageWidth = self.image.width()
            self.imageHeight = self.image.height()

    def draw(self):
        if not self.drawn: # Only draw once
            self.drawn = True
            if self.image is not None:
                self.id = self.canvas.widget.create_image( (self.p1.x, self.p1.y), image=self.image, **self.configuration )
                if self.name == "": self.name = f"Image_({self.id})"
                self.code += f"#Image {self.name}:\nself.id = self.canvas.widget.create_image self.p1.x, self.p1.y, image=self.image, **self.configuration )"
                self.parameters = f"({self.p1.x},{self.p1.y}, image={self.image}\n" 
                super().draw()
                
    def resize( self, size, useCurrent=False):
        if self.canvas.usePIL:
            if useCurrent:
                if self.img is None: self.img = PILImage.open(self.fullPath)
                img = self.img
            elif self.img is None: 
                img = PILImage.open(self.fullPath)
            else:
                img = self.img
            width = int(img.width * size)
            height = int(img.height * size)
            newImage = img.resize([width,height])
            selfPhotoImage = ImageTk.PhotoImage(newImage)
            if useCurrent: self.img = newImage
            self.updateImage(selfPhotoImage)
        
    def fitInto( self, width=0, height=0, useCurrent=False):
        if self.canvas.usePIL:
            if useCurrent:
                if self.img is None: self.img = PILImage.open(self.fullPath)
                img = self.img
            elif self.img is None: 
                img = PILImage.open(self.fullPath)
            else:
                img = self.img
            if width > 0:
                size = width/self.img.width
            elif height > 0:
                size = height/self.img.height
            else:
                return
            self.resize(size, useCurrent=True)
        
    def zoom(self, x,y, x1,y1, width=0 ,height=0, useCurrent=False):
        if self.canvas.usePIL:
            if useCurrent:
                if self.img is None: self.img = PILImage.open(self.fullPath)
                img = self.img
            elif self.img is None: 
                img = PILImage.open(self.fullPath)
            else:
                img = self.img
            newImage = img.crop( (x,y, x1,y1))
            if useCurrent: self.img = newImage
            if width == 0 and height == 0:
                selfPhotoImage = ImageTk.PhotoImage(newImage)
                self.updateImage(selfPhotoImage)
            else:
                self.fitInto(width=width, height=height, useCurrent=True)
    
    def rotate(self, cc_degrees, useCurrent=False):
        """Rotate the picture counter clockwise in degrees withing its frame. 
        Edges can be cut off as the frame remains in its position and does not rotate.
        useCurrent modifies the current picture, not the original"""
        if self.canvas.usePIL:
            if useCurrent:
                if self.img is None: self.img = PILImage.open(self.fullPath)
                img = self.img
            elif self.img is None: 
                img = PILImage.open(self.fullPath)
            else:
                img = self.img
            newImage = img.rotate(cc_degrees)
            if useCurrent: self.img = newImage
            selfPhotoImage = ImageTk.PhotoImage(newImage)
            self.updateImage(selfPhotoImage)
        
    def removeBackground(self, removeBlack=True, useCurrent=False):
        if self.canvas.usePIL:
            if useCurrent:
                if self.img is None: self.img = PILImage.open(self.fullPath)
                img = self.img
            elif self.img is None: 
                img = PILImage.open(self.fullPath)
            else:
                img = self.img
            rgba_img = img.convert("RGBA")
            datas = rgba_img.getdata()
            x = 0 if removeBlack else 255
            target_color = (x, x, x, 255)  
            new_data = []
            for item in datas:
                if item == target_color:
                    transparentItem = (item[0], item[1], item[2], 0)
                    new_data.append(transparentItem)
                else:
                    new_data.append(item)
            rgba_img.putdata(new_data)
            newImage = ImageTk.PhotoImage(rgba_img)
            if useCurrent: self.img = ImageTk.getimage(newImage)
            self.updateImage(newImage)
            
    def fade( self, *args, useCurrent=False):
        """Fade the object out of existence"""
        if self.canvas.usePIL:
            if useCurrent:
                if self.img is None: self.img = PILImage.open(self.fullPath)
                img = self.img
            elif self.img is None: 
                img = PILImage.open(self.fullPath)
            else:
                img = self.img
            r,g,b,a = img.split()
            amount = args[1] if len(args)>1 else args[0]
            useAmount = min(max(0,amount),255)
            a = a.point(lambda alphaPoint: min(useAmount,alphaPoint))
            newImage = PILImage.merge('RGBA', (r,g,b,a))
            self.image = ImageTk.PhotoImage(newImage)
            if useCurrent: self.img = newImage
            self.updateImage(self.image)
        else:
            self.undraw()
        
    def updateImage(self, newImage):
        if self.drawn:
            if newImage is not None:
                self.canvas.widget.itemconfig(self.id, image=newImage)
                self.image = newImage
                self.canvas.update()   

    def getP1(self):
        return Point(self.p1.x-self.width/2, self.p2.y-self.height/2)
    def getP2(self):
        return Point(self.p1.x+self.width/2, self.p2.y+self.height/2)

    def setPathToImageFile(self):
        """Look for a provided url or a directory path (or cwd) maybe separate from a file name.
        If the filename is None then the object does not have an image.
        """
        path = self.url # Use the url if provided, no checking it for validity
        if path == "":
            if self.file is None:
                path = None
            else:
                if self.path == "": # No provided path, use the file name once and then CWD once
                    if self.file != "":
                        path = self.file
                        if not os.path.exists(path):
                            path = os.path.join(os.getcwd(), self.file)

                else: # try the provided path and the file name
                    path = os.path.join(self.path, self.file)
                    if not os.path.exists(path): # Failed, try the cwd in front of the path and filename
                        path = os.path.join(os.getcwd(), path)
                        if not os.path.exists(path): # Failed, try just adding the path and filename
                            path = self.path + self.file
                if not os.path.exists(path):
                    path = None
        return path
    
    def getWidth(self):
        """Returns the width of the image in pixels"""
        return self.imageWidth 

    def getHeight(self):
        """Returns the height of the image in pixels"""
        return self.imageHeight

    def getPixel(self, x, y, opacity=False):
        """Returns a list [r,g,b] with the RGB color values for pixel (x,y)
        r,g,b are in range(256) """
        if self.image is None:
            resposeList = []
        else:
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

    def setPixel(self, x, y, color):
        """Sets pixel (x,y) to the given color """
        if self.image is not None:
            opacity = False
            if len(color) == 9:
                opacity = True
            self.image.put("{" + color[0:7] +"}", (x, y))
            if opacity:
                try:
                    colorValue = int(color[8:9])
                except:
                    colorValue = 255
                self.image.transparency_set(x,y, colorValue, 16)

    def save(self, filename):
        """Saves the pixmap image to filename.
        The format for the save image is determined from the filname extension.  """
        path, name = os.path.split(filename)
        ext = name.split(".")[-1]
        self.img.write( filename, format=ext)
       
    def jump(self, x, y, extra=None):
        """move picture object to x,y location, only x,y needed for movement"""
        if self.canvas:
            try:
                self.canvas.widget.coords(self.id, x, y)
            except:
                pass
            else:
                self.p1 = Point(x,y)
                self.p2 = Point(x,y)
                self.canvas.widget.update_idletasks()  
       
    def __repr__(self):
        return self.clone()
    def __str__(self):
        bbox = self.getBoundingBox()
        return f"Image {self.name} {bbox} with path: {self.fullPath})"
    
    def clone(self):
        other = Image(self.p1, url=self.url)
        other.configuration = self.configuration.copy()
        return other

# Basic Shapes with the Action Interface
class SmartLine( Line, ActionInterface):
    def __init__(self, canvas, *args, **kwargs):
        super().__init__(canvas, *args, **kwargs)
        ActionInterface.__init__(self, canvas, kwargs)

class SmartMultipleLines( MultipleLines, ActionInterface):
    def __init__(self, canvas, *args, **kwargs):
        super().__init__(canvas, *args, **kwargs)
        ActionInterface.__init__(self, canvas, kwargs)

class SmartImage( Image, ActionInterface):
    def __init__(self, canvas, *args, **kwargs):
        super().__init__(canvas, *args, **kwargs)
        ActionInterface.__init__(self, canvas, kwargs)

class SmartCircle( Circle, ActionInterface):
    def __init__(self, canvas, *args, **kwargs):
        super().__init__(canvas, *args, **kwargs)
        ActionInterface.__init__(self, canvas, kwargs)

class SmartOval( Oval, ActionInterface):
    def __init__(self, canvas, *args, **kwargs):
        super().__init__(canvas, *args, **kwargs)
        ActionInterface.__init__(self, canvas, kwargs)

class SmartRectangle(Rectangle, ActionInterface):
    def __init__(self, canvas, *args, **kwargs):
        super().__init__(canvas, *args, **kwargs)
        ActionInterface.__init__(self, canvas, kwargs)

class SmartSquaricle(Squaricle, ActionInterface):
    def __init__(self, canvas, *args, **kwargs):
        super().__init__(canvas, *args, **kwargs)
        ActionInterface.__init__(self, canvas, kwargs)

class SmartPolygon(Polygon, ActionInterface):
    def __init__(self, canvas, *args, **kwargs):
        super().__init__(canvas, *args, **kwargs)
        ActionInterface.__init__(self, canvas, kwargs)

class SmartText(Text, ActionInterface):
    def __init__(self, canvas, *args, **kwargs):
        super().__init__(canvas, *args, **kwargs)
        ActionInterface.__init__(self, canvas, kwargs)

class SmartCanvasEntry(CanvasTextEntry, ActionInterface):
    def __init__(self, canvas, *args, **kwargs):
        super().__init__(canvas, *args, **kwargs)
        ActionInterface.__init__(self, canvas, kwargs)

class IndependentProcess():
    """A class for running a process in a separate thread.  
    The process is automatically started and running when the object is created unless "pause" is in the kwargs.
    The process will continue to restart after finishing until either:
    a)  the stop() method is called.
    b)  "runOnce=True" is in the kwargs.
    If paused from the beginning, the process will wait until calling the resume() method.
    Stopped by calling the stop() method and then the process ends.
    Paused by calling the pause() method and then resumed by calling the resume() method.

    REQUIRED ARGUMENTS:
        function: Function to be run in the separate thread
    ARGUMENTS:
        Arguments and keyword arguments for the function (except for "pause" and "runOnce")
        Remaining arguments are passed into the function
    DICTIONARY:
        pause: Pause until resumed
        runOnce: run only once, not repeatedly (often very rapidly)
        Remaining dictionary items are passed into the function
        """
    def __init__(self, function, *args, **kwargs):
        self.function = function
        self.args = args
        self.dictionary = dict(**kwargs )
        self.stopped = False
        self.sleep = Sleep(0.1, reuse=True)
        self.thread = threading.Thread(target=self.run)
        self.paused = False if "pause" not in self.dictionary else self.dictionary.pop("pause")
        self.runOnce = False if "runOnce" not in self.dictionary else self.dictionary.pop("runOnce")
        self.thread.start()

    def run(self):
        while not self.stopped:
            if self.paused:
                self.sleep.start()
            else:
                self.function(*self.args, **self.dictionary)
                self.stopped = self.runOnce or self.stopped

    def stop(self, ignore=None):
        self.paused = False
        self.stopped = True

    def pause(self, ignore=None):
        self.paused = True

    def resume(self, ignore=None):
        self.paused = False
 
class Sleep():
    """A class for pausing a process for a specified number of seconds (compatible with Tkinter).
    The normal sleep() function is incompatible with Tkinter.  Seconds can be integer or float.
    Used once if the "setup" parameter is False (which is the default setting) with just: Sleep(1).  
    Used for multiple sleeps if "reuse" is True and the start() function used each time as in:
    timer = Sleep(5,reuse=True) then used as  timer.start()    ."""
    def resetWait(self):
        """Sets a barrier to allow a pause until the sleep time finishes"""
        self.barrier.wait()

    def __init__(self, seconds, reuse=False):
        """Barrier set to two threads, one for the timer and one for the main thread.  The timer thread
        will reset the barrier after the specified number of seconds.  The main thread will wait for the barrier to reset."""
        self.barrier = Barrier(2)
        self.seconds = float(seconds)
        if not reuse:
            self.start()

    def start(self):
        """Start the timer when there is an instantiated object.  The timer will reset the barrier after the specified number of seconds."""
        self.thread = Timer(self.seconds, self.resetWait).start()
        self.barrier.wait()

class Panel(): 
    """A Panel is a collection of graphic elements than appear together and used for organization.
    The Panel can be drawn, undrawn, moved, and have its buttons refreshed.  The Panel can be filled with
    buttons, entries, and other graphic elements.  They are separately stored in lists so, for example,
    only buttons are checked for selection and only Entry widgets for text input.  The Panel can be 
    hidden and shown.
    """
    def __init__(self, name="Simple", offset=None):
        """ Collects a list of graphic items """ 
        self.offset = offset
        self.staticList = [] # Elements that are not always undrawn, like top level icons)
        self.refreshList = [] # Items in other lists that are available to refresh
        self.buttonList = [] # For buttons only
        self.entryList = [] # For entry widgets - unused until we have these
        self.queuedList = [] # Items waiting to be processed
        self.iconList = [] # Checked but not drawn or erased
        self.simpleBefore = [] # For simple objects drawn first
        self.simpleAfter = [] # For simple objects drawn last
        self.ids = []
        self.displayed = False
        self.filled = False
        self.simple = True
        self.name = name
        self.step = 0 # Milliseconds between elements being displayed
        self.allLists= [self.staticList,self.refreshList,self.buttonList,self.entryList]
        self.otherLists = [self.refreshList,self.queuedList,self.simpleBefore,self.simpleAfter,self.ids]

    def addListToLists(self, list):
        for item in list:
            answer = type(item)
            result = str(answer)
            if result.find("Entry") > 0:
                self.entryList.append(item)
            elif result.find("Button") > 0:
                self.buttonList.append(item)
            elif result.find("Card") > 0 and item.selectable:
                self.buttonList.append(item)
            elif  result.find("SmartText") > 0: #  can be refreshed
                self.refreshList.append(item)
            elif type(item) != type(()):
                self.staticList.append(item)
        self.filled = True

    # Add buttons from the Icon list for checking.  Icon list items are pre-existing
    # so they are neither drawn or undrawn.  The icon list can contain non-buttons.
    def addListOfIcons(self, list):
        if len(list) > 0:
            for item in list:
                answer = type(item)
                result = str(answer)
                if result.find("Button") > 0:
                    self.iconList.append(item)
    
    def addItemsToIcons( self, *list):
        if len(list) > 0:
            for item in list:
                answer = type(item)
                result = str(answer)
                if result.find("Button") > 0:
                    self.iconList.append(item)         

    def addItems( self, *list):
        if len(list) > 0:
            if self.filled and self.displayed:  # there are existing items already drawn
                for item in list:
                    self.queuedList.append(item)  # Save for later
            else:
                self.addListToLists(list)

    def addSimpleBefore(self, *list):
        """Add simple objects to be drawn before the panel is drawn"""
        if len(list) > 0:
            for item in list:
                self.simpleBefore.append(item)
    def addSimpleAfter(self, *list):
        """Add simple objects to be drawn after the panel is drawn"""
        if len(list) > 0:
            for item in list:
                self.simpleAfter.append(item)

    def drawPanel(self, *list):
        self.ids = DrawSimpleObjects(self.canvas, *self.simpleBefore, offset=self.offset)
        if len(list) == 0: 
            if len(self.queuedList) > 0:
                for item in self.queuedList: 
                    item.offsetPosition(self.offset)
                    item.draw()
                self.addListToLists(self.queuedList)
                self.queuedList.clear()
            else:
                for eachItem in self.allLists:
                    for item in eachItem: 
                        item.offsetPosition(self.offset)
                        item.draw()
        else:
            for item in list: 
                item.offsetPosition(self.offset)
                item.draw()
        self.ids += DrawSimpleObjects(self.canvas, *self.simpleAfter, offset=self.offset)

        self.displayed = True
        self.offset = None # Only do once

    def updateButtonsAndCards(self):
        for item in self.buttonList: 
            item.draw()

    def undrawPanel(self, *list):
        if len(list) == 0:
            for eachItem in self.allLists:
                for item in eachItem: 
                    item.undraw()
        else:
            for item in list: 
                item.undraw()
                
        for item in self.simpleBefore: 
            self.canvas.widget.delete(item)
        self.displayed = False
        for item in self.allLists: item = []
        for item in self.otherLists: item = []

    def undrawEntirePanel(self, *args):
        anyDelay = self.step/1000.0
        for eachItem in self.allLists:
            for item in eachItem: 
                item.undraw()
                if self.step > 0: time.sleep(anyDelay)
            eachItem.clear()
        for item in self.simpleBefore: 
            self.canvas.widget.delete(item)
            if self.step > 0: time.sleep(anyDelay)
        self.displayed = False
        self.simpleBefore.clear()
        for item in self.allLists: item = []
        self.allLists.clear()
        for item in self.otherLists: item = []
        self.otherLists.clear()
        self.ids = []
        self.name = ""

    def movePanel(self, x, y, delay=0):
        anyDelay = delay/1000.0
        for item in self.simpleBefore: 
            self.canvas.widget.coord(item, x, y) 
        for eachItem in self.allLists:
            for item in eachItem: 
                item.move(x, y)
        if delay > 0: time.sleep(anyDelay)

    def currentValues( self, point=None ):
        """Return the current return-values of the list buttons and entries as a dictionary, including if an object was Selected."""
        data = dict()
        for eachList in [self.buttonList, self.entryList]:
            for item in eachList:
                try:
                    data[item.name] = item.returnValue
                    if point is not None:
                        if item.clicked(point):
                            data['Selected'] = item.name
                except:
                    data[item.name] = 'Missing'
        return data

    # Refresh certain items if refresh==True and there is generally an action method
    # If there is no action method, then the text is updated from self.text
    def refreshPanel(self):
        for item in self.refreshList: 
            if item.visible and item.refresh:
                if item.action is not None:
                    item.action(item.text)

        for item in self.buttonList: 
            if item.visible and item.refresh:
                if item.action is not None:
                    item.setText(item.text)

    def removePanel( self, doomedItem):
        if doomedItem in self.entryList:
            self.entryList.remove(doomedItem)
        elif doomedItem in self.buttonList:
            self.buttonList.remove(doomedItem)
        elif doomedItem in self.refreshList:
            self.staticList.remove(doomedItem)
        elif doomedItem in self.staticList:
            self.staticList.remove(doomedItem)
 
    def reconfigure(self, id, option, value):
        """Reconfigure the item with the given id.  The id is the canvas id of the item."""
        options = {option:value}
        self.canvas.widget.itemconfig(id, options)
        self.canvas.update() 

    # Use these to provide an automatic row and column guide useful
    # for using labels (which use screen coordinates).  There are better tools in Tkinter for this.
    def grid_X( self, x, totalNumberColumns, buffer=10):
        width = abs(self.p2.x - self.p1.x)
        divisor = 2 * totalNumberColumns
        part = width / divisor
        number = x if  x > 0 else 0
        if number > totalNumberColumns: number = totalNumberColumns
        columnPosition = self.p1.x + buffer + (number * part * 2)
        return columnPosition
    
    def grid_Y( self, y, totalNumberRows, buffer=10):
        heigth = abs(self.p2.y - self.p1.y)
        divisor = 2 * totalNumberRows
        part = heigth / divisor
        number = y if  y > 0 else 0
        if number > totalNumberRows: number = totalNumberRows
        rowPosition = self.p1.y + buffer + (number * part * 2)
        return rowPosition

    def gridPoint( self, x, y ): # Assumes a 12 x 12 grid in the panel area with 10 px buffers
        _x = self.grid_X(x, 12)
        _y = self.grid_Y(y, 12)
        return Point(_x, _y)

    def gp( self, x, y ): # Assumes a 12 x 12 grid in the panel area with 10 px buffers
        _x = self.grid_X(x, 12)
        _y = self.grid_Y(y, 12)
        return Point(_x, _y)

class BasicButton(GenericObject, ActionInterface):
    """Basis for all buttons, probably not instantiated by itself.  Buttons have a label and box

    REQUIRED ARGUMENTS: 
        canvas: The canvas object is placed upon
        x,y or tuple or Point: The location of the upper left corner of the button
        x, x,y or tuple or Point: The location of the lower right corner or the radius of a circle
        text: text for the button, yes, it is here too
     ARGUMENTS:
        None
    DICTIONARY:
        BUTTON:
            returning: Returned value, defaults to the text
            fill,fillcolor: Button color
            linecolor: Color of the line around the button
            linewidth: Width of the line around the button
            delay: Any delay between selection and some action
            toggle: Button is a toggle push button which stays in until pressed
            text: text for the button, yes, it is here too
            pushtext: Color of the text when selected on a push button, also set a delay
            pushbutton: Color of a pushbutton when selected, also set a delay
            name: Name for the button, defaults to the text
            circle: Button is a circle
            squaricle: Button is a squaricle
        TEXT:
            face or font: Font for the button text, default is "TkDefaultFont 12" with no styling
            color,fontcolor,fill: Color of the text, defaulrt is Black
            text: Text for the button, default is blank
            pushtext: color for the text when pushed on a pushbutton

    """
    def __init__(self, canvas, p1, p2, text, **dictionary):
        super().__init__(canvas, p1, p2, text, **dictionary)
        ActionInterface.__init__(self, canvas, dictionary)

        self.p1 = p1
        self.p2 = p1 if p2 is None else p2
        self.buttonText = "" if text is None else text
        self.font = dictionary.get("font","TkDefaultFont 12")
        self.returnValue = self.buttonText # What is returned on a selection as the value
        self.name = self.buttonText # Default name of the button
        self.selected = False
        self.selectable = True

        # Default colors for all buttons
        self.buttonColor = canvas.colors["LightGray"]
        self.buttonTextColor = canvas.colors["Black"]
        self.pushColor = canvas.colors["Black"]
        self.pushTextColor = canvas.colors["White"]
        self.outline = canvas.colors["Black"]
        self.lineWidth = 1

        # Shape values used by shapeButton()
        self.shape = None # Shape of the button (circle, square, etc.)
        self.label = None # Text label on button
        self.center = None # Center of the button
        self.circle = False # Click on a circle instead of a rectangle
        self.squaricle = False # Click on a squaricle instead of a rectangle
        self.radius = 0 # Radius of a circle taken from p2

        # Now save button characteristics
        self.setButtonFromDictionary(dictionary)

    def __eq__(self, value: object) -> bool:
        return self.shape.id == value.shape.id

    def allMove(self, dx, dy, *args):
        self.shape._move(dx, dy)
        self.label._move(dx, dy)
    def move(self, dx, dy):
        self.shape.move(dx, dy)
        self.label.move(dx, dy)
              
    def draw(self):
        """ Provide a window for it to be drawn in"""
        if not self.visible:
            if self.shape is not None:
                self.shape.draw()
                self.shape.move = self.allMove
            if self.label is not None:
                self.label.draw()
                self.label.move = self.allMove
            self.visible = True

    def undraw(self):
        """Remove the button from being displayed"""
        if self.visible:
            if self.shape is not None:
                self.label.undraw()
            if self.label is not None:
                self.shape.undraw()
            self.visible = False
  
    def jump(self, x, y):
        self.shape.jump(x, y)
        self.label.jump(x, y)

    def getBoundingBox(self):
        return self.shape.getBoundingBox()

    def raiseButton(self):
        self.shape.levelUp()
        self.label.levelUp()

    def lowerButton(self):
        self.shape.levelDown()
        self.label.levelDown()

    def clicked(self, point):
        """Return True if the button/shape or text/label was clicked, False otherwise"""
        self.selected = False
        if self.visible:
            buttonWasClicked = self.shape.clicked(point)
            if not buttonWasClicked:
                buttonWasClicked = self.label.clicked(point)
            else:
                self.selected = True
        return buttonWasClicked

    def setButtonFromDictionary(self, dictionary):
        """Dictionary used to set many button characteristics"""
        if len(dictionary) > 0:
            for key in dictionary:
                self.setButtonDetail( key, dictionary[key])
         
    def setFontDetail( self, attribute, value ):
        fontAttribute = attribute.lower()
        try:
            if fontAttribute == "face" or fontAttribute == "font":
                self.font = value
            elif fontAttribute in [ "color","fontcolor","fill"]:
                self.buttonTextColor = self.canvas.colors.get(value, value)
            elif fontAttribute == "text":
                self.name = value
            elif fontAttribute == "pushtext":
                self.pushTextColor = self.canvas.colors.get(value, value)
            else:
                pass
                print( f"Button.setFontDetail: Unknown font attribute: {fontAttribute}  {value}")
        except:
            pass
            print( f"Button.setFontDetail: Error on font attribute: {fontAttribute}  {value}")

    def setButtonDetail( self, attribute, value):
        buttonAttribute = attribute.lower()
        try:
            if buttonAttribute == "returning":
                self.returnValue = value
            elif buttonAttribute in ["fill","fillcolor"]:
                self.buttonColor = self.canvas.colors.get(value, value)
            elif buttonAttribute == "linecolor":
                self.outline = self.canvas.colors.get(value, value)
            elif buttonAttribute == "linewidth":
                self.lineWidth = value
            elif buttonAttribute == "delay":
                try:
                    self.delay = int(value)
                except:
                    pass
            elif buttonAttribute == "text":
                self.label.setText(value)
            elif buttonAttribute == "toggle":
                self.pushColor = self.canvas.colors.get(value, value)
                self.delay = 0
                self.toggle = True
            elif buttonAttribute == "pushtext":
                self.pushTextColor = self.canvas.colors.get(value, value)
                if self.delay == 0 or self.delay == False: self.delay = 0.1
            elif buttonAttribute == "pushbutton":
                self.pushColor = self.canvas.colors.get(value, value)
                if self.delay == 0 or self.delay == False: self.delay = 0.1
            elif buttonAttribute == "name":
                self.name = value
            elif buttonAttribute == "circle": # Bad click results if not a circle in a square
                self.circle = (value == True)
            elif buttonAttribute == "squaricle":
                self.squaricle = (value == True)
            elif buttonAttribute == "group":
                self.group = value
                if value is not None: self.group.addItem(self)
            else:
                self.setFontDetail( attribute, value )
        except:
            print( f"setButtonDetail: Error on button attribute: {buttonAttribute}  {value}")

    def addMissingKeyValuePairs(self, dictionary, **kwargs):
        """Add unique key value pairs to the provided dictionary"""
        for keyValue, value in kwargs.items():
            key = keyValue.lower()
            if not key in dictionary:
                dictionary[key] = value 

    def turnButtonOn(self):
        self.forceButtonOn()

    def turnButtonOff(self):
        self.forceButtonOff()
            
    def forceButtonOff(self):
        self.selected = False
        self.shape.color = self.buttonColor
        self.label.color = self.buttonTextColor
            
    def forceButtonOn(self):
        self.selected = True
        self.shape.color = self.pushColor
        self.label.color = self.pushTextColor

    def turnButton(self, state):
        if state:
            self.turnButtonOn()
        else:
            self.turnButtonOff()
        
    def extractPoints(self, listing, dictionary={}):
        """Extract p1, p2, and optional text from a listing of various formats. Points defaulted to (0,0).
        If p2 is not included it is a copt of p1. If text is not included it is blank.
        If only the points are needed then dictionary not provided and any text is ignored."""

        # Disassemple all lists, Points and tuples in single numbers
        newList = []
        for item in listing:
            if type(item) == tuple:
                for subitem in item:
                    newList.append(subitem)
            elif type(item) == list:
                    newList.extend(item)
            elif type(item) == Point:
                newList.append(item.x)
                newList.append(item.y)
            else:
                newList.append(item)

        # See if text is in the dictionary, if so extract and delete it from the dictionary
        text = dictionary.get("text",None)
        if text is None:
            text = ""
        else:
            del dictionary["text"]

        # Put them back together as points with an optional text (last item or in the dictionary)
        length = len(newList)
        if length < 2:
            p1 = Point(0,0)
            p2 = Point(0,0)
        else:
            p1 = Point(newList[0], newList[1])
            if length == 3:
                text = str(newList[2])
                p2 = Point(newList[0], newList[1])
            else:
                p2 = Point(newList[2], newList[3])
                if length > 4:
                    text = str(newList[4])
                    
        if len(dictionary) == 0: 
            return p1, p2 
        return p1, p2, text
    
    def exchangeActions(self, *newActions):
        result = self.actions.copy()
        self.action.clear()
        self.actions.extend(newActions)
        return result
  
class CanvasButton(BasicButton):
    """A Button is a labeled rectangle in a window. See BasicButton for Arguments and Dictioinary elements.
    It has a user-supplied label, position, and other attributes.
    The clicked(p) method returns True or False on it being clicked if event coding not implemented. 
    
    DICTIONARY:
        action: single or list of functions to execute upon a selection
        master: Not implemented, use for radio and check boxes
        refresh: force a refresh of the text
        collectvalue=True: Not implemented, values are collected elsewhere
        numberformat: Use a number .format for the provided text in the button
        zeroformat: Format the number of zeroes in the number
        number: Provide the number to be formatted with the number format
    """

    def __init__(self, canvas, *args, **dictionary):
        p1, p2, text = self.extractPoints(args, dictionary=dictionary)
        shape = dictionary.pop("shape", None)
        super().__init__(canvas, p1, p2, text, **dictionary)

        def delayPressRelease(event, *args):
            """Button delay, in single thread everything pauses.  Multithread is not enabled!"""
            self.event = event
            self.turnButtonOn()
            Sleep(self.delay)
            self.turnButtonOff()

            # Run any remaining actions
            # if len(self.actions) > 0:
            #     for function in self.actions:
            #         if isinstance(function, list) or isinstance(function, tuple):
            #             for nestedFunction in function:
            #                 if nestedFunction is not None:
            #                     nestedFunction(event)
            #         else:
            #             function(event)
        
        def toggleButton(event, *args):
            """Button toggled on and off with events"""
            self.event = event
            if self.toggle:
                if self.selected:
                    self.selected = False
                    self.turnButtonOff()
                else:
                    self.selected = True
                    self.turnButtonOn()

                ############################################################################
                # Should be handled by GenericObject.callActions() so not needed here
                # Run any remaining actions (both toggles use this so check toggleOn)
                # if len(self.actions) > 0:
                #     useActions = self.actions.copy()
                #     for function in useActions:
                #         if isinstance(function, list) or isinstance(function, tuple):
                #             for nestedFunction in function:
                #                 if nestedFunction is not None:
                #                     nestedFunction(event)
                #         elif function is not None:
                #             function(event)  

        # Various extra attributes
        self.master = False # Controls the values of other buttons in a panel (use action parameter)
        self.collectValue = False
        self.refresh = False
        self.numberFormat = "{0}"
        self.zeroFormat = "0.00"
        self.number = 0
        self.drawn = False

        # Make the button shape
        if shape is not None:
            try:
                self.shape = shape(self.canvas, self.p1, self.p2, 
                                fill=self.buttonColor, outline=self.outline, 
                                width=self.lineWidth, autoDraw=False, dragging=self.dragActive)
            except:
                self.shape = SmartRectangle(self.canvas, self.p1, self.p2, 
                                width=self.lineWidth, fill=self.buttonColor,
                                outline=self.outline, autoDraw=False, dragging=self.dragActive)
                
        elif self.squaricle:
            self.shape = SmartSquaricle(self.canvas, self.p1, self.p2, squaricle=True, 
                                fill=self.buttonColor, width=self.lineWidth,  
                                outline=self.outline, autoDraw=False, dragging=self.dragActive)
        elif self.circle:
            self.shape = SmartCircle(self.canvas, self.p1, self.p2, 
                                fill=self.buttonColor, outline=self.outline, 
                                width=self.lineWidth, autoDraw=False, dragging=self.dragActive)
        else: # Rectangle
            self.shape = SmartRectangle(self.canvas, self.p1, self.p2, 
                                width=self.lineWidth, fill=self.buttonColor,
                                outline=self.outline, autoDraw=False, dragging=self.dragActive)
        
        
        
        
        
        self.shape.selectable = self.selectable

        # Make the centered text label that floats above the button
        if isinstance(self.p2, Point):
            width = self.p2.x - self.p1.x
            height = self.p2.y - self.p1.y
            self.center = Point(self.p1.x + width/2,self.p1.y + height/2)
        else: # p2 is a radius not a point
            self.center = self.p1

        # Make the label
        self.label = SmartText(self.canvas, self.center, text=self.buttonText, fill=self.buttonTextColor, 
                    font=self.font, autoDraw=False, dragging=self.dragActive) 
        self.label.selectable = self.selectable
           
        # Save the button actions for both the label and box
        if self.toggle:
            self.shape.saveObjectActions(toggleButton)
            self.label.saveObjectActions(toggleButton)
        elif self.delay > 0 or self.label.delay > 0 or self.shape.delay > 0:
            delay = self.delay 
            if hasattr(self.label, 'delay'): 
                delay = max(delay, self.label.delay)
                self.label.delay = delay
            if hasattr(self.shape, 'delay'): 
                delay = max(delay, self.shape.delay)
                self.shape.delay = delay
            self.delay = delay
            self.label.saveObjectActions(delayPressRelease, makeFirst=True)
            self.shape.saveObjectActions(delayPressRelease, makeFirst=True)
        self.label.saveObjectActions(self.actions)
        self.shape.saveObjectActions(self.actions)
        self.draw() # Also binds any actions

    def deselectToggleButton(self, *args):
        if self.toggleOn:
            self.toggleOn = False
            self.turnButtonOff()   
    
    def setButtonDetail( self, attribute, value):
        buttonAttribute = attribute.lower()
        try:
            if  buttonAttribute == "master": 
                self.master = (value == True)
            elif buttonAttribute == "action": 
                if len(self.actions) == 0: 
                    self.setButtonFunction(value) # Only use if not other actioins have been entered
            elif buttonAttribute == "refresh": 
                self.refresh = True
                self.action = value 
            elif buttonAttribute == "collectvalue": 
                self.collectValue = (value == True)
            elif buttonAttribute == "numberformat":
                self.setNumberFormat(value)
            elif buttonAttribute == "zeroformat":
                self.setZeroFormat(value)
            elif buttonAttribute == "number":
                self.setNumber(value)
            else:
                BasicButton.setButtonDetail( self, attribute, value )
        except:
            print( f"setButtonDetail: Error on button attribute: {buttonAttribute}  {value}")

    # Override for specific buttons as these are generic responses
    def processResponse(self, option=None):
        dictionary = {}

        if self.collectValue:
            dictionary[self.name] = self.returnValue
        
        return dictionary

    def getNumber(self):
        return self.number

    def setNumber(self, number):
        self.number = number
        if number < 0.00005:
            text = self.zeroFormat.format(number)
        else:
            text = self.numberFormat.format(number)
        self.label.setText(text)

    def setNumberFormat(self, formatting):
        if len(formatting) == 0:
            self.numberFormat = "{0}"
        else:
            self.numberFormat = formatting

    def setZeroFormat(self, formatting):
        if len(formatting) == 0:
            self.zeroFormat = "0.00"
        else:
            self.zeroFormat = formatting

    def setButtonFunction(self, function, makeFirst=False):
        """Set the function to be called when the button is selected.  There can
        be multiple functions called in the order they were added and
        function may be a list or tuple of functions"""
        #if not isinstance(self.actions, list):  self.actions = []
        if isinstance(function, list) or isinstance(function, tuple):
            if makeFirst:
                newList = function.reverse()
                for eachFunction in newList:
                    if eachFunction is not None:
                        self.actions.insert(0,eachFunction)
            else:
                for eachFunction in function:
                    if eachFunction is not None:
                        self.actions.append(eachFunction)
        elif function is not None:
            self.actions.append(function)

class CancelButton(CanvasButton):
    """Companion to the OK button in a panel of buttons.  Will self-align on a point taking into
    account the width of the text.  Placement in the middle (when OK is on the right) or on the left.
    See default button for other options.
                      
     REQUIRED ARGUMENTS:
        canvas: The canvas object is placed upon
     ARGUMENTS:
        x,y or tuple or Point: The location of the upper left corner of the button
        x,y or tuple or Point: The location of the lower right corner of the button.
     DICTIONARY:
        text: Text to display in cancel button, "Cancel" is the default.
        font: Font to use (will be bolded) with default of TkDefaultFont 18"
        Center: center or default to the left
    DEFAULTS:
        Button color: red, Pushbutton text color: white, Bush button color when pushed: White
        push button text color when pushed: Red, Button shape is squaricle 
    """
    def __init__( self, canvas, *args, **dictionary):

        # Initialize, note the button is the same size but its own font family
        text = dictionary.get("text", None )
        if text is None:
            text = "cancel"
        else:
            dictionary.pop("text")
        font = "TkDefaultFont 18" #dictionary.get("font", "TkDefaultFont 18" )
        useFont = font if font.find("bold") > 0 else font+" bold"
        (letterWidth, letterHeight, cancelLength ) = Text.fontStats(text, useFont)
        p1, p2 = self.extractPoints( args )
        if p1.x == p2.x:
            halflength = letterWidth + cancelLength / 2
            p1.x -=  halflength
            p2.x += halflength
        if p1.y == p2.y:
            halfHeight = letterHeight * 0.75
            p1.y -= halfHeight
            p2.y += halfHeight
        
        # Set up a specific dictionary for the cancel button
        cancelDictionary = dictionary.copy()
        if "text" in cancelDictionary: del cancelDictionary["text"]
        self.addMissingKeyValuePairs( cancelDictionary, color=canvas.colors["White"], 
                                     pushText=canvas.colors["Red"], pushbutton=canvas.colors["White"], 
                                     fill=canvas.colors["Red"], lineWidth=2, squaricle=True )
        cancelDictionary["font"] = useFont
        super().__init__(canvas, p1, p2, text, **cancelDictionary)

    def undraw(self):
        self.label.undraw()
        self.shape.undraw()

class OKButton(CanvasButton): 
    """OK button in a panel of buttons.  Will self-align on a point taking into
    account the width of the text.  Placement in the middle or on the right.
    See default button for other options.
                                            
     REQUIRED ARGUMENTS:
        canvas: The canvas object is placed upon
     ARGUMENTS:
        x,y or tuple or Point: The location of the upper left corner of the button
        x,y or tuple or Point: The location of the lower right corner of the button.
     DICTIONARY:
        text: Text to display in the button, "OK" is the default.
        font: Font to use (will be bolded) with default of TkDefaultFont 18"
        Center: center or default to the right
    DEFAULTS:
        Button color: white, Pushbutton text color: black, Bush button color when pushed: black
        push button text color when pushed: white, Button shape is squaricle 
    """
    def __init__( self, canvas, *args, **dictionary):
        
        # Initialize, note the button is the same size but its own font family
        OkText = dictionary.get("OkText", "OK" )
        font = dictionary.get("font", "TkDefaultFont 18 bold" )
        details = Text.details(self, font=font, text=OkText)
        useFont = ' '.join(["TkDefaultFont", str(details['size']), "bold"])
        action = dictionary.get("action", None )
        
        # if the x coordinates are the same, center the text there (otherwise hope the box is big enough)
        (letterWidth, letterHeight, OkLength ) = Text.fontStats(OkText, useFont)
        p1, p2 = self.extractPoints( args )
        if p1.x == p2.x:
            halflength = letterWidth + OkLength / 2
            p1.x -=  halflength
            p2.x += halflength
        if p1.y == p2.y:
            halfHeight = letterHeight * 0.75
            p1.y -= halfHeight
            p2.y += halfHeight
        
        OkDictionary = dict(color=canvas.colors["Black"], lineWidth=2, pushText=canvas.colors["White"], font=useFont, action=action,
                       fill=canvas.colors["White"], pushbutton=canvas.colors["Black"], squaricle=True)
        super().__init__(canvas, p1, p2, OkText, **OkDictionary)

    def undraw(self):
        self.label.undraw()
        self.shape.undraw()
        # self.numberFormat = "{0}"
        # self.zeroFormat = "0.00"
        # super().undraw()

class Popup():
    """ Popup area with a rectangle background and an OK button at the bottom placed
    into a Panel so all objects are accessible.  Calling code determines the rectangle shape,
    this function adds room at the bottom for button(s).
    ARGUMENTS:
       canvas, points defining rectangle
    DICTIONARY:
       action=None: function called when OK selected; default is local function deactivatePopup()
       OkText="OK": alternate text for the OK button
       font: Defaults to "TkDefaultFont 18"
       center=True: Center the OK button instead of placed on the right side
    """
    def __init__(self, canvas, p1, p2, **dictionary):
        """Initialize the Popup object"""
        self.canvas = canvas
        self.panel = Panel() # Manages graphics in the OK area
        OkText = dictionary.get("OkText", "OK" )
        font = dictionary.get("font", "TkDefaultFont 18")
        center = dictionary.get("center", False)

        # Set the default colors based on the Dark/Light mode
        if canvas.darkModeOn():
            self.foreground = canvas.colors["White"]
            self.background = canvas.colors["Black"]
        else:
            self.foreground = canvas.colors["Black"]
            self.background = canvas.colors["White"]

        # Determine the placement of the OK button
        (letterWidth, letterHeight, textLength ) = Text.fontStats(OkText, font)
        newP2 = Point(p2.x, p2.y + 2*letterHeight)
        textWidth = textLength + 2 * letterWidth
        y1 = newP2.y-10-letterHeight
        y2 = newP2.y-10
        x1 = p2.x - 10
        x1 -= textWidth
        x2 = x1+textWidth
        buttonP1 = Point(x1,y1)
        buttonP2 = Point(x2,y2)
        if center:
            buttonWidth = (buttonP2.x - buttonP1.x)
            boxWidth = (p2.x - p1.x)
            correction =  10 - boxWidth/2 + buttonWidth/2
            buttonP1.x += correction
            buttonP2.x += correction

        # Function called when OK selected bound to the actual button shape
        # NOTE: self is available as the button selected, canvas is the event.widget
        def deactivatePopup(event, *args):  # Default if none provided, just undraw everything
            self.panel.undrawEntirePanel()

        # Make the box and button for the popup and store in the panel object   
        actionList = [deactivatePopup]
        if "action" in dictionary and dictionary["action"] is not None:
            actionList.append(dictionary["action"])
        self.box = Polygon(self.canvas, p1, newP2, squaricle=True, fill=self.background, width=2, outline=self.foreground)
        self.okButton = OKButton(self.canvas, buttonP1, buttonP2, OkText=OkText, action=actionList, font=font)
        self.panel.addListToLists([self.box,self.okButton])

    def getMouse(self):
        """If on manual control, wait for a mouse click and return the return-value of the button clicked"""
        name = "Unknown"
        looping = True
        while looping:
            point = self.canvas.getMouse()
            for item in self.panel.buttonList:
                if item.clicked(point):
                    name = item.returnValue
                    looping = False
        return name

class OkPopup( Popup ):
    """Provide a bordered Popup at the center of the window.  Adjust the height of
    the panel to hold all the words.  OK added at the end by the Popup class.
    ARGUMENTS:
       canvas, text placed into Popup box, width of the box
    DICTIONARY:
       width: width of the popup, font size to use, and an alternate text to OK
       action: Default is none provided: function called when OK selected; default is local function deactivatePopup()
       OkText="OK": alternate text for the OK button
       font: Defaults to "TkDefaultFont 18"
       anchor: Anchor for text placement of: ["center","w","e","s","n","sw","se","nw","ne"]: default is "center"
       center=True: Center the OK button instead of placed on the right side
       wait=True: Wait for a mouse click to continue but wait internally to the function
    """
    def __init__(self, canvas, text, **dictionary):

        # Initialize and correct from the dictionary provided
        width = dictionary.get("width", min(400,int(canvas.width/3)))
        self.font = dictionary.get("font", "TkDefaultFont 18")
        OkText = dictionary.get("OkText", "OK")
        center = dictionary.get("center", False )
        wait = dictionary.get("wait", False)
        if wait:
            action = canvas._onClick
        else:
            action = dictionary.get("action", None)
        anchor = dictionary.get("anchor", "n").lower()
        if anchor not in ["center","w","e","s","n","sw","se","nw","ne"]: anchor = "n"
        justify = "center"
        if anchor in ["nw","w","sw"]:
            justify = "left"
        elif anchor in ["ne","e","se"]:
            justify = "right"
        justify = dictionary.get("justify",justify)

        # Determine the size characteristics to hold the text based on the font details of the text
        details = Text.details( self, font=self.font, text=text, width=width, buffer=10 )
        x1 = (canvas.width-details['width'])/2
        y1 = (canvas.height-details['height'])/2
        x2 = x1 + details['width']
        y2 = y1 + details['height'] + details['letterHeight']
        p1 = Point(x1,y1)
        p2 = Point(x2,y2)
        if anchor in ["center","n","s"]:
            p3 = Point((p2.x + p1.x)/2, p1.y+details['letterHeight']/4)
        else:
            p3 = Point(p1.x + details['letterWidth'], p1.y+details['letterHeight']/4 )

        # Initialize the popup part (box and OK button provided)
        super().__init__(canvas, p1, p2, font=details['font'], OkText=OkText, center=center, action=action)
        lineOfText = Text(canvas, p3, text=text, font=details['font'], anchor=anchor, 
                          width=details['bufferedWidth'], justify=justify, fill=self.foreground)
        self.okButton.raiseButton()
        self.panel.addItems( lineOfText )
        if wait: canvas.getMouse()

class YesNoPopup( OkPopup ):
    """Provide a bordered Popup at the center of the window for a Yes/No type popup box.
    Adjust the height of the panel to hold all the words.  
    Cancel made here, OK added at the end by the Popup class.
    ARGUMENTS:
       canvas, text placed into Popup box
    DICTIONARY:
       width: width of the popup, font size to use, and an alternate text to OK
       action: Default is none provided: function called when OK selected; default is local function deactivatePopup()
       font: Defaults to "TkDefaultFont 18"
       anchor: Anchor for text placement of: ["center","w","e","s","n","sw","se","nw","ne"]: default is "center"
       center: True: Center the OK button instead of placed on the right side
       OkText: Alternative to "OK", which is the default
       cancelText: Alternative text to "Cancel"
       OkAction: Optional function to call when OK selected
       cancelAction: Optional function to call when Cancel selected
       wait=True: Wait for a mouse click to continue but wait internally to the function  The response
                    is stored in the self.response dictionary.  ex:
            popup = YesNoPopup( canvas, "Do you want to continue?", cancelText="Quit", wait=True)
            if "Quit" in popup.response:
    """
    def __init__(self, canvas, text, **dictionary):
        # Default functions called when CANCEL selected are bound to the actual button shapes
        # NOTE: self is available as the button selected, canvas is the event.widget
        self.response = None # Set by the button selected
        def cancelFunction(event, *args):  # Default if none provided
            self.response = "Cancel" if self.cancel.returnValue is None else self.cancel.returnValue
        def oKFunction(event,*args):  # Default if none provided
            self.response = "OK" if self.okButton.returnValue is None else self.okButton.returnValue
        
        # Extract and remove from the dictionary specific dictionary items
        dictionary.setdefault("font", "TkDefaultFont 20")
        cancelText = "Cancel" if 'cancelText' not in dictionary else dictionary.pop("cancelText")
        center = False if "center" not in dictionary else dictionary.pop("center")
        wait = False if "wait" not in dictionary else dictionary.pop("wait" )
        if wait:
            cancelAction = cancelFunction
            dictionary["action"] = oKFunction
        else:
            cancelAction = cancelFunction if "cancelAction" not in dictionary else dictionary.pop("cancelAction")
            dictionary["action"] = oKFunction if "OkAction" not in dictionary else dictionary.pop("OkAction")

        # Initialize the OK popup part (box and OK button provided)
        super().__init__(canvas, text, **dictionary)

        # Determine content and location of the cancel button (based on the OK button)
        cancelDictionary = {"text": cancelText, "font":dictionary['font'], "action": (cancelAction,self.panel.undrawEntirePanel)}

        (letterWidth, letterHeight, cancelLength ) = Text.fontStats(cancelText, self.font)
        textWidth = cancelLength + 2 * letterWidth
        x1 = self.box.p1.x + 10
        y1 = self.okButton.p1.y
        x2 = x1 + textWidth
        y2 = self.okButton.p2.y
        buttonP1 = Point(x1,y1)
        buttonP2 = Point(x2,y2)
        if center:
            boxWidth = (self.box.getP2.x - self.box.getP1().x)
            correction =  boxWidth/2 - 10 - textWidth/2
            buttonP1.x += correction
            buttonP2.x += correction
            cancelDictionary["center"] = True

        self.cancel = CancelButton( canvas, buttonP1, buttonP2, **cancelDictionary)
        self.panel.addListToLists([self.cancel])
        self.cancel.raiseButton()
        self.cancel.draw()
        canvas.update()
        if wait:
            popupTimer = Sleep(0.1, reuse=True)
            while self.response is None:
                canvas.update()
                popupTimer.start()
            popupTimer = None
            self.response = {self.response:True}
    
class CountdownTimer():
    """Countdown timer in a circle.  Unfortuanalty no user IO during the wait.  Modify using any of the following:
    REQUIRED ARGUMENTS:
        canvas to draw on 
    ARGUMENTS:
        None
    DICTIONARY:
        point: Center of timer, defaults to Point(canvas.width/2, canvas.height/2 )
        radius: Radius of timer shape, defaults to 50
        color: Color of font, defaults to White??
        fill: Color of timer backbrouind, defaults to Brown
        font: Font for countdown text, defaults to "Ariel 60 bold"
        outline: Outline color, defaults to Black
        width: Width of something??, defaults to 2
        count: Starting number, defaults to 3
        wait=True: Wait for the .start() function to start, defaults to False which automatically starts
        independent=True: Run in an independent and parallel thread, defaults to False
        start=True: Start timer immediately after creation, defaults to False
    """
    def __init__(self, canvas, **dictionary):
        self.canvas = canvas
        self.point = dictionary.get("point", Point(canvas.width/2, canvas.height/2))
        self.radius = dictionary.get("radius", 50 )

        color = dictionary.get("color", "White")
        self.color = canvas.colors.get(color, color)
        fill = dictionary.get("fill", "Brown")
        self.fill = canvas.colors.get(fill, fill)
        outline = dictionary.get("outline", "Black")
        self.outline = canvas.colors.get(outline, outline)

        self.font = dictionary.get("font", "Ariel 60 bold" )
        self.width = dictionary.get("width", 2 )
        self.count = dictionary.get("count", 3 )
        self.wait = dictionary.get("wait", False )
        self.independent = dictionary.get("independent", False )
        self.stopTimer = False

        if "start" in dictionary and dictionary["start"]:
            self.startCountdownTimer()
            
    def displayIndependentCount(self):
        """Independent thread counts while the main program continues"""
        if self.count > 0:
            self.text.reconfigure('text', str(self.count))
            self.count -= 1
            self.canvas.master.after(1000, self.displayIndependentCount) 
        else:
            self.text.undraw()
            self.circle.undraw()

    def startCountdownTimer(self):
        """Start the countdown timer.  If independent, the main thread will run a separate thread and the main
        program will continue in parallel.  Note that the main thead may not use .sleep() when using Tkinter graphics.
        If wait is set, the timer will wait for the countdown to finish using .sleep() which may be incompatible with Tkinter.
        Normally, the timer will run in the background and the program will wait for a time before continuing"""
        self.circle = Circle(self.canvas, self.point, self.radius,fill=self.fill, outline=self.outline, width=self.width ) 
        self.text = Text(self.canvas, self.point, text=str(self.count), font=self.font, fill=self.color)
        self.sleep = Sleep(1, reuse=True)

        if self.independent:
            self.displayIndependentCount()
        else:
            while self.count > 0:
                self.text.reconfigure('text', str(self.count))
                self.count -= 1
                self.sleep.start()
            self.text.undraw()
            self.circle.undraw() 

class CanvasTextBox(ActionInterface):
    def __init__(self, canvas, x, y, x2, y2, **kwargs):
        self.canvas = canvas
        self.extraCode = ""
        frameWidth = x2-x
        height = y2-y
        overWide = kwargs.pop('overWide', frameWidth-30)
        self.name = kwargs.pop('name', "Unknown")
        self.replacementDictionary = {}
        text = kwargs.pop('text', "Missing text")
        label = kwargs.pop('label', "Missing Label")
        self.tags = kwargs.pop('tags', "canvastextbox")
        standardFont = kwargs.pop('font', ("TkDefaultFont", 12))
        scrolling = kwargs.pop('scrolling', True)
        defaultKind = "vertical" if scrolling else None
        kind = kwargs.pop('kind', defaultKind)
        readonly = kwargs.pop('readonly', True)
        copyPaste = kwargs.pop('copyPaste', True)
        borderWidth = kwargs.pop('borderwidth', 1)
        textAnchor = kwargs.pop('anchor', 'NE')
        boxRelief = "flat"
        frameRelief = tk.SOLID
    
        textBoxFormat = dict( sticky="ew", padx=10, pady=5, font=standardFont, relief=boxRelief, wrap="word" )
        frameFormat = dict( sticky="full", relief=frameRelief, borderwidth=borderWidth, 
                             padx=10, pady=5, rowweights=1, columnweights=1, 
                            font=(standardFont[0], standardFont[1], 'bold italic'))
        if len(label) == 0:
            self.textBoxFrame = _Frame( canvas, sticky="full", padx=10, pady=5, rowweights=1, columnweights=1,
                           x=x, y=y, width=frameWidth, height=height, borderwidth=borderWidth) 
        else:
            self.textBoxFrame = _LabelFrame( canvas, frameFormat, 
                           text=label, x=x, y=y, width=frameWidth, height=height) 
        self.textBoxArea = _TextBox(self.textBoxFrame, textBoxFormat, width=overWide, anchor=textAnchor,
                                      text=text, label=label, scrolling=scrolling, kind=kind, readonly=readonly, **kwargs)
        
        
        # Allows for dragging using an ActionInterface
        self.p1 = Point(x,y) # Placement on the canvas, used by move()
        self.selectable = False # This is not a button
        self.bindingAllowed = canvas.bindingAllowed # Allow bindings if canvas allows them
        dragging = kwargs.get('dragging', False) # Allow dragging of the textbox
        dragDictionary = dict( widget=self.textBoxFrame.widget, dragging=dragging )
        ActionInterface.__init__(self, canvas, dragDictionary)
        
        if not copyPaste: # NOTE: Not working
            self.canvas.forEventAddFunction('<Key>', self.ctrlEvent)
            self.textBoxArea.widget.bind("<Key>", lambda e: self.ctrlEvent)

    def ctrlEvent(self, event):
        if event.state == 4:
            if event.keysym == 'c':
                return "break"
        
            elif event.keysym == 'v':
                return "break"
        
            elif event.keysym == 'x':
                return "break"
            
    def __str__(self):
        frame = self.textBoxFrame
        bbox = [frame.x, frame.y, frame.x + frame.width, frame.y + frame.height]
        return f"CanvasTextBox {self.name} at {bbox} with text: {self.get()}"
        
    def set(self, text):
        if text is not None and len(text) > 0: 
            self.textBoxArea.set(text)  
    def clear(self):
        self.textBoxArea.clear()
    def add(self, *args):
        if args is not None and len(args) > 0: 
            for text in args:
                self.textBoxArea.add(text)
    def beginning(self):
        self.textBoxArea.beginning()
    def ending(self):
         self.textBoxArea.ending()
    def addBoldText(self, boldText):
        if boldText is not None and len(boldText) > 0: 
            self.textBoxArea.addBold(boldText)
                
    def newSection(self, text):
        if text is not None and len(text) > 0: 
            self.textBoxArea.add(text)  

    def get(self):
        text = self.textBoxArea.get()
        return text

    def setBackground(self, color ):
        self.textBoxArea.color = color

    def undraw(self):
        self.textBoxFrame.widget.destroy()
    def delete(self):
        self.textBoxFrame.widget.destroy()

    def move(self, x, y, *args):
        self.p1 = Point(self.p1.x+x,self.p1.y+y)
        self.textBoxFrame.widget.place(x=self.p1.x, y=self.p1.y)

    def move_to(self, x, y, *args):
        self.p1 = Point(x,y)
        self.textBoxFrame.widget.place(x=self.p1.x, y=self.p1.y)

    def destroy(self):
        self.textBoxFrame.widget.destroy()

class PrettyTextBox(CanvasTextBox):
    def __init__(self, canvas, *args, **kwargs):

        # Get parameters that only the child class uses
        localText = kwargs.pop("text",None) # Don't pass on any provided text
        dividers = kwargs.pop("dividers","<>" )# Your special dividers, can be changed.
        self.uniqueNames = kwargs.pop("uniqueNames",True) # Use unique tag names to avoid global format changes in non-named tags

        # Initialize the parent
        super().__init__( canvas, *args, text=" ", **kwargs)
        
        # Tags can be unique, reusing tags will change previous text formats.
        # Adding text to existing text risks duplicating tags, so this number
        # is incremented for each added piece of unique formatted text.
        self.uniqueAdd = 0
        self.tagSet = set() # Set of unique tags (but not standard formatting like bold or italic)
        self.setDividers( dividers ) # Yes, dividers can be changed
        
        # Get the current font, keep an original value as the basicFont can be changed
        self.basicFont = kwargs.get('font', ["TkDefaultFont", 12, 'normal'])
        if isinstance(self.basicFont,tuple): self.basicFont = list(self.basicFont)
        if len(self.basicFont) == 1: self.basicFont.append(12)
        if len(self.basicFont) == 2: self.basicFont.append('normal')
        self.originalFont = [*self.basicFont]
        
        # Now format any provided text
        if localText is not None:
            self.set(localText)
    
    def formatText(self, value, uniqueNames):
        """Format the text in a text box using special commands. 
        Format commands or tags are surrouded by divider letters like <bob>. You can change divders.
        All text after that until the next divider letter like ">" have that format.
        The tag system in tkinter is dynamic so if you change a tag, all identical tags
        get the same format change, even previously printed text.
        Here, we make each tag unique (or not)by adding numbers to it.
        Format commands are:
        b:  bold the text
        i:  italic text
        upper: upper case the text
        size: change just the font size
        font: There are 3 variations:
              font=original~  set the font to the original font name, size, style.
              Notice the extra ending tiddle! The actual command is:  ~font=original~~
              font=name,size,style~ sets the current font to that font. Missing
                   size and/or style leaves those unchanged. Notice the extra ending tiddle!
              font=name,size,style sets the font to that font. Missing
                   size and/or style leaves those unchanged. Only changes the selected text.
        Two dividers together will print the divider (excluding used in font described above)
        Unidentified format commands are checked if they are a known color. If so the
              text color (foreground) is set to that color. Normal color is black.
        Args:
            value str: text to format
        """
        if len(value) == 0: return # No text means nothing to do
        
        # Split the text by the divider letter
        lastLetterIsDivider = value[-1] == self.textDivider
        textList = value.split(self.tagDivider)
        endOfTextList = len(textList) - 1
        self.textBoxArea.widget.location = tk.END 
        
        # Loop for each part of the text
        for number, line in enumerate(textList): # range(startAt,length):
            if number == 0 and len(line) == 0: continue # First item can be empty if starting with a divider

            # set up variables used for each pair of choice and text
            tag = None
            alternateTag = None
            tagHelper = None
            text = None
            extraNormalText = None
            formatting = None
            colorWasChosen = False
            matchValue = None

            # Get the tag, text, and extra text, if any
            phrase = line.split(self.textDivider)
            sizing = len(phrase)
            if sizing == 0:
                tag = self.tagDivider
            elif sizing == 1:
                text = phrase[0]
            elif sizing == 2:
                tag = phrase[0]
                text = phrase[1]
            else:
                tag = phrase[0]
                text = phrase[1]
                extraNormalText = phrase[2]

            # Quick check for the second divider showing twice
            count = line.find( self.doubleTextDivider )
            if count >= 0: tag = self.textDivider

            # Check if there is a named tag and it has included it formatting tag
            if tag is not None and tag.find(";") >= 0:
                alternateTag, tag = tag.split(";",1)

            # Set up for a match value. No choice means a divider was put in twice
            if tag is None:
                if lastLetterIsDivider:
                    if number == endOfTextList:
                        matchValue = self.tagDivider
            else:
                # Extract any extra tag helper (like a number with size) with the tag using the equals sign
                matchValue = tag.lower()
                findEquals = tag.find("=")
                if findEquals >= 0:
                    matchValue = matchValue[:findEquals].strip()
                    if findEquals < len(tag):
                        tagHelper = tag[findEquals+1:].strip()
            
            # Match a tag in lower case
            match matchValue:

                case None:
                    extraNormalText = text # Normal text
                    text = None

                case self.tagDivider: # Two dividers allow the divider to be shown before the text
                    extraNormalText = self.tagDivider

                case self.textDivider:
                    subtext = line
                    place = subtext.find(self.textDivider)
                    extraNormalText = subtext[:place]+subtext[place+1:]
                    tag = None
                    text = None

                case "b":
                    tag = "bold"
                    formatting = dict(font=(self.basicFont[0], self.basicFont[1], 'bold'))
            
                case "i":
                    tag = "italic"
                    formatting = dict(font=(self.basicFont[0], self.basicFont[1], 'italic'))
                    
                case "upper":
                    text = text.upper()
                case "lower":
                    text = text.lower()
                case "title":
                    text = text.title()
                    
                case "size": # Insure a valid integer between 1 and 500
                    tag = f"size_{number}_{self.uniqueAdd}" if uniqueNames else "size"
                    try:
                        size = int(tagHelper)
                    except:
                        tag = None
                    else:
                        size = max(1,min(500,size))
                        formatting = dict(font=(self.basicFont[0], size, self.basicFont[2]))
                        
                case "font":
                    if len(tagHelper) > 0: # There must be additional information for formatting
                        if len(text) > 0:
                            newFont = tagHelper.split(",")
                            useFont = self.basicFont.copy()
                            for i in range( len(newFont) ):
                                useFont[i] = newFont[i]
                            formatting = dict(font=(self.basicFont[0], self.basicFont[1], self.basicFont[2]))
                            tag = self.basicFont[0]+"_"+ str(self.basicFont[1])+"_"+self.basicFont[2]
                            if uniqueNames: tag += f"_{self.uniqueAdd}"
                # Anything else
                case _:
                    # Check for a color
                    if tag in self.canvas.colors.ColorDictionary:
                        colorChosen = self.canvas.colors.ColorDictionary[tag]
                        formatting = dict(foreground=colorChosen)
                        colorWasChosen = True
            
            # Anything not tagged is normal text, but we may have to give it a unique tag name
            # as if we change the basic font later in the text, all previous normal font
            # text will also change.
            if alternateTag is not None: tag = alternateTag
            if tag is None:  
                if text is not None: self.textBoxArea.widget.insert(tk.END, text)
            else:
                if formatting is None:
                    if text is not None: self.textBoxArea.widget.insert(tk.END, text)
                else:
                    self.textBoxArea.widget.tag_configure(tag, **formatting)
                    if not colorWasChosen: self.tagSet.add(tag)
                    self.textBoxArea.widget.insert(tk.END, text, tag)
            if extraNormalText is not None:
                self.textBoxArea.widget.insert(tk.END, extraNormalText)
            self.textBoxArea.widget.location = tk.END # Set the cursor to the end of the text
    
    def add(self, *args):
        """Add the formatted text to existing text."""
        if args is not None and len(args) > 0:
            if self.textBoxArea.readonly: self.textBoxArea.widget.config(state=tk.NORMAL)
            for value in args:
                self.uniqueAdd += 1
                self.formatText(value, self.uniqueNames)
                self.textBoxArea.widget.location = tk.END # Set the cursor to the end of the text
            self.textBoxArea.widget.see(tk.END) # Scroll to the end of the text
            if self.textBoxArea.readonly: self.textBoxArea.widget.config(state=tk.DISABLED)
    
    def set(self,value):
        self.clear()
        self.add(value)
        
    def addBoldText(self, boldText):
        if boldText is not None and len(boldText) > 0: 
            text = f"{self.tagDivider}b{self.textDivider}{boldText}{self.textDivider}"
            self.textBoxArea.add(text)
                
    def newSection(self, text):
        if text is not None and len(text) > 0: 
            self.textBoxArea.add("\n")  
            self.textBoxArea.add(text)  

    def setDividers(self, value):
        if len(value) > 1:
            self.tagDivider = value[0]
            self.textDivider = value[1]
        else:
            self.tagDivider, self.textDivider = value, value
        self.doubleTextDivider = self.textDivider + self.textDivider

    def setTag( self, tag, **values):
        if tag in self.tagSet:
            self.textBoxArea.widget.tag_configure(tag, **values)

    def addTag(self, tag, *args ):
        """
        Adding a tag using addTag using letter positioning
        :param tag: Name of the tag
        :param args: Either two points in a string as "1.0, 1.30) of the 4 points (1,0,1,30)
        """       
        self.tagSet.add(tag )
        if len(args)==2:
            line1, line2 = args[0],args[1]
            self.textBoxArea.widget.tag_add( tag, f"{line1}", f"{line2}" )
        elif len(args)==4:
            line1,letter1,line2,letter2 = args[0],args[1],args[2],args[3]
            self.textBoxArea.widget.tag_add( tag, f"{line1}.{letter1}", f"{line2}.{letter2}" )

    def removeTag( self, tag, *args ):
        if tag in self.tagSet:
            if len(args)==2:
                line1, line2 = args[0],args[1]
                self.textBoxArea.widget.tag_remove( tag, f"{line1}", f"{line2}" )
            elif len(args)==4:
                line1,letter1,line2,letter2 = args[0],args[1],args[2],args[3]
                self.textBoxArea.widget.tag_remove( tag, f"{line1}.{letter1}", f"{line2}.{letter2}" )

    def getTagRanges( self, tag ):
        if tag in self.tagSet: 
            return self.textBoxArea.widget.tag_ranges( tag )

    def sanitizeTextForFile(self, text ):
        """ Remove all special formatting tags from the text for saving to a file."""
        cleanText = ""
        lastIndex = 0
        length = len(text)
        i = 0
        while i < length:
            if text[i] == self.tagDivider:
                # Find the next divider
                j = i + 1
                while j < length and text[j] != self.textDivider:
                    j += 1
                if j < length:
                    # Found a complete tag, skip it
                    i = j + 1
                else:
                    # No closing divider found, treat as normal text
                    cleanText += text[i]
                    i += 1
            elif  text[i] != self.textDivider:
                cleanText += text[i]
            i += 1
        return cleanText

class CanvasComboBox(_ComboBox, ActionInterface):
    def __init__(self, localComboFrame, comboList, *args, **kwargs):
        self.outerFrame = localComboFrame.parent
        self.canvas = self.outerFrame.parent
        self.localComboFrame = localComboFrame
        self.comboSelectionList = comboList
        self.extraCode = ""
        dragging = kwargs.pop('dragging', False) # Allow dragging of the textbox
        self.name = kwargs.pop('name', "Combo Box")
        
        self.comboBox = _ComboBox(self.localComboFrame, self.comboSelectionList, *args, **kwargs) 
        
        # Allows for dragging using an ActionInterface
        self.p1 = Point(self.outerFrame.x, self.outerFrame.y) # Placement on the canvas, used by move()
        self.selectable = False # This is not a button
        self.bindingAllowed = self.canvas.bindingAllowed # Allow bindings if canvas allows them
        dragDictionary = dict( widget=self.localComboFrame.widget, dragging=dragging )
        ActionInterface.__init__(self, self.canvas, dragDictionary)

    def __str__(self):
        frame = self.outerFrame
        bbox = [frame.x, frame.y, frame.x + frame.width, frame.y + frame.height]
        return f"CanvasComboBox {self.name} at {bbox}"

    def undraw(self):
        self.outerFrame.widget.destroy()

    def move(self, x, y, *args):
        self.p1 = Point(self.p1.x+x,self.p1.y+y)
        self.outerFrame.widget.place(x=self.p1.x, y=self.p1.y)

    def move_to(self, x, y, *args):
        self.p1 = Point(x,y)
        self.outerFrame.widget.place(x=self.p1.x, y=self.p1.y)
    
    def get(self):
       return self.comboBox.get()
    
    def set(self, value):
        self.comboBox.set(value)

class ProgressBar():
    """Basic ttk progress bar helper for use on a Canvas instance.
       PARAMETERS:
           No parameters defaults to all defaults
           Text only centers text box in canvas 
           x,y - optional upper left cornet of the bar, default to bar centered in the canvas 
           width,height - optional dimensions of the bar, default to default dimensions
       
       KWARGS:
           anchor defaults to tk.NW
           coord defaults to None # Alternative coordinates
           increment defaults to DEFAULT_INCREMENT
           orient defaults to tk.HORIZONTAL)
           mode defaults to 'determinate', the other choice is intererminate
           length defaults to self.width
           maximum defaults to DEFAULT_MAXIMUM
           update has three possible values:
               'step' means use a step value to increment the bar
               'variable' means use a local self.variable whose value change, changes the bar
               variable passed in by user whose value change, changes the bar
           text defaults to None. If there is text then the following occurs:
               A box surrounds the text and bar with the box width extended to hold all the text
               The x,y is the upper left corner of the box with the width & height for the bar's shape
    """
    def __init__(self, canvas, *args, **kwargs):
        self.canvas = canvas
        self.windowID = None
        self.widget = None # Main ttk Widget used
        self.variable = None
        self.box = None
        self.textTitle = None
        self.counter = 0
        DEFAULT_INCREMENT = 10000
        DEFAULT_MAXIMUM = 100
        DEFAULT_BUFFER = 20
        DEFAULT_FONT_SIZE = 16
        DEFAULT_FONT = "TKDefaultFont"

        # Keep placement & design options out of ttk.Progressbar kwargs.
        self.anchor = kwargs.pop('anchor', tk.NW)
        text = kwargs.pop('text', None)
        coord = kwargs.pop('coord',None) # Alternative coordinates
        self.increment = kwargs.pop('increment',DEFAULT_INCREMENT)
        
        #  Determine location and shape. Center is the canvas center. Choose:
        #     no args means 'center', 180, 16
        #     width, height means 'center' used
        #     'center', width, height
        #     x,y, width, height
        self.determineDimensions(args, coord=coord)
        
        # Determine how to update the bar; step is default, variable or provided variable
        updateChoice = kwargs.pop('update', 'step')
        if updateChoice == 'step':
            pass
        elif updateChoice == 'variable':
            self.variable = kwargs.get('variable', tk.DoubleVar(value=kwargs.get('value', 0)))
            kwargs.setdefault('variable', self.variable)
        else:
            self.variable = updateChoice
            kwargs.setdefault('variable', self.variable)
            
        # Progress bar charcteristics
        kwargs.setdefault('orient', tk.HORIZONTAL)
        kwargs.setdefault('mode', 'determinate')
        kwargs.setdefault('length', self.width)
        kwargs.setdefault('maximum', DEFAULT_MAXIMUM)
        self.increment /= kwargs['maximum']
        
        # If there is any text then a background needs to be provided and dimensions change
        if text != None:
            # Assume text will fit
            buffer, textSize = DEFAULT_BUFFER,DEFAULT_FONT_SIZE
            
            # Determine box position
            box_x = self.x - buffer
            box_y = self.y - buffer - textSize
            box_width = self.width + 2*buffer
            box_height = self.height + buffer + textSize
            box_x2 = box_x + box_width
            box_y2 = box_y + box_height + buffer
            
            # Determine text position (may extend the box)
            text_x = box_x + box_width/2
            text_y = box_y + textSize
            font = (DEFAULT_FONT, textSize)
            fontStats = self.fontStats(text, font)
            minimumLength = fontStats[2]
            if minimumLength > box_width:
                fontBonus = minimumLength - box_width
                box_width += fontBonus
                box_x -= fontBonus/2
                box_x2 += fontBonus/2
            
            self.box = Rectangle( canvas, Point(box_x, box_y), Point(box_x2, box_y2),
                                 fill='white', outline='black', width=1)
            self.textTitle = Text( canvas, Point(text_x,text_y), text=text, 
                                  font=font)

        self.widget = ttk.Progressbar(self.canvas.widget, **kwargs)
        self.windowID = self.canvas.widget.create_window(
            self.x,
            self.y,
            width=self.width,
            height=self.height,
            anchor=self.anchor,
            window=self.widget,
        )
        self.startTime = datetime.datetime.now()
        
    def determineDimensions(self, args, coord=None):
        """ There are a variety of argument options"""
        x = None
        width = 180
        height = 16
        length = len(args)
        if length == 2:
            width = args[0]
            height = args[1]
        elif length == 3:
            width = args[1]
            height = args[2]
        elif length == 4:
            x = args[0]
            y = args[1]
            width = args[2]
            height = args[3]
            
        if coord is not None:
            try:
                if len(coord) == 2:
                    x = coord[0]    
                    y = coord[1]
            except:
                pass
            
        if x == None:
            (x1, y1, width1, height1) = self.canvas.getCanvasCoodinates()
            if x1 is None:
                x1 = 0
            if y1 is None: 
                y1 = 0
            x = x1 + (width1 - x1)/2 - width/2
            y = y1 + (height1 - y1)/2 - height/2
            
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
    def fontStats(self, text, font):
        """Return details about the font. Font is a tuple or string"""
        DEFAULT_FONT = "TKDefaultFont"
        DEFAULT_FONT_SIZE = '12'
        DEFAULT_FONT_STYLE = 'normal'
        if type(font) == tuple:
            partsOfTheFont = [*font] 
        else:
            partsOfTheFont = font.split(" ")
        if len(partsOfTheFont) == 1 and len(partsOfTheFont[0])==0: partsOfTheFont[0] = DEFAULT_FONT
        if len(partsOfTheFont) < 2: partsOfTheFont.append(DEFAULT_FONT_SIZE)
        if len(partsOfTheFont) < 3: partsOfTheFont.append(DEFAULT_FONT_STYLE)
        quickFont = Font(family=partsOfTheFont[0], size=int(partsOfTheFont[1]), weight=partsOfTheFont[2])
        letterWidth = quickFont.measure("W")
        letterHeight = quickFont.metrics("linespace")
        length = quickFont.measure(text)
        return( letterWidth, letterHeight, length)
    
    #-------------------------------------------
    def get(self):
        return float(self.widget['value'])

    def set(self, value=None):  
        self.widget.configure(value=value)
        self.canvas.update()

    value = property(get, set)
    #-------------------------------------------
    def step(self, amount=1.0):
        """ When called, only ipdate the bar at the proper time based on the increment / bar length"""
        self.counter += 1
        if self.counter > self.increment:
            self.counter = 0
            self.widget.step(amount)
            self.canvas.update()

    def stop(self):
        self.widget.stop()
        self.canvas.update()

    def configure(self, **kwargs):
        self.widget.configure(**kwargs)

    def place(self, x=None, y=None, width=None, height=None):
        if x is not None:
            self.x = x
        if y is not None:
            self.y = y
        if width is not None:
            self.wdth = width
        if height is not None:
            self.height = height

        self.canvas.widget.coords(self.windowID, self.x, self.y)
        self.canvas.widget.itemconfigure(self.windowID, width=self.wdth, height=self.height)

    def close(self):  
        """ Close the bar. To avoid a flash, there is a minimum visible time."""
        DEFAULT_MILLISECONDS_TO_BE_SHOWN = 2000
        rightNow = datetime.datetime.now()
        difference = rightNow - self.startTime
        if difference.seconds >= 1:
            self.finalClose()
        else:
            sleepingTime = DEFAULT_MILLISECONDS_TO_BE_SHOWN - difference.microseconds
            self.canvas.update()
            self.canvas.root.after(sleepingTime, self.finalClose)

    def finalClose(self, *args):
        """ Final close either immediately or after a delay"""
        if self.windowID is not None:
            self.canvas.widget.delete(self.windowID)
            self.windowID = None
        self.widget.destroy()
        if self.box != None:
            self.textTitle.delete()
            self.box.delete()
        self.canvas.update()


class changeWidgetClass():
    def __init__(self, *args, **kwargs):
        """Create a fixed frame to hold buttons to change
        widget values on-the-fly. Pass in the object being formatted."""
        self.returnFunction = kwargs.get("return",None)
        self.object = args[0] if len(args)> 0 else None
        self.frame = None
        
        self.dictionaryOfChanges = {}
    
    def getPopulateCheckbox(self):
        pass
        
    def populatePopupMinimal(self):
        pass
    
    def populatePopupFull(self):
        pass
    
    def getValueCheckbox(self):
        self
        
    def readValueAndModify(self):
        pass
    
    def displayChanges(self):
        params = ""
        for key, value in self.dictionaryOfChanges.items():
            params += f"{key}={value}, "
        print(self.object.description(), f"\nChanges were: {params[:-1]}")
    
    def quit(self):
        self.frame.delete()
        if self.returnFunction is not None:
            self.returnFunction(self)
        