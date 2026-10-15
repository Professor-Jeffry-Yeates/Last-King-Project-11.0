__version__ = '8.0'
from CoffeeCanvas import *
from CoffeeBean import *

class InstructionClass():
    """ Place a continuous stream of instructions in a scrollable text box
    PARAMETERS:
         canvas:     where to draw graphics
         data:       all game data
         arguments:  x,y, width, height of instruction holder
         kwargs:    'tags' with default value
                    'text' Initial text
                    'label' Label for the box
                    'quest' description
    """
    def __init__(self, canvas, data, x, y, width, height, **kwargs):
        title = "This is your quest"
        self.canvas = canvas
        self.data = data.setResource('instructions', self)
        text = kwargs.get('text', "Missing text")
        label = kwargs.get('label', None)
        self.tags = kwargs.get('tags', "instructions")

        standardFont = ("TKDefaultFont", 12)
        instructionFormat = dict( sticky="ew", padx=10, pady=5, font=standardFont, relief="flat", wrap="word" )
        frameFormat = dict( sticky="full", relief=tk.SOLID, borderwidth=1, 
                            padx=10, pady=5, rowweights=1, columnweights=1, 
                           font=(standardFont[0], standardFont[1], 'bold italic'))
        
        # Get the specific quest text 
        quest = kwargs.get('quest', "This is your quest")
        
        self.instructionBar = PrettyTextBox( canvas, x, y, x+width, y+height,  **instructionFormat,
                         text=text, label=label, scrolling=True, kind="vertical", readonly=True )
        self.instructionBar.beginning()
#
    def set(self, text):
        """ Clear, then display text"""
        if text is not None and len(text) > 0: 
            with self.data.graphicLock:
                self.instructionBar.set(text)
            savedText = self.instructionBar.sanitizeTextForFile( text )
            self.data.writeGameResult(savedText)   

    def add(self, *args):
        """ Add to any existing text"""
        if args is not None and len(args) > 0: 
            with self.data.graphicLock:
                for text in args:
                    self.instructionBar.add(text)
            savedText = self.instructionBar.sanitizeTextForFile( text )
            self.data.writeGameResult(savedText) 

    def addBoldText(self, boldText):
        """ Add to any existing text but his text is bold"""
        if boldText is not None and len(boldText) > 0: 
            with self.data.graphicLock:
                self.instructionBar.add('<b>'+boldText+'>')
            savedText = self.instructionBar.sanitizeTextForFile( boldText )
            self.data.writeGameResult(savedText) 
                
    def newSection(self, text):
        """ Add to any existing text but place some space before it to separate it visually"""
        if text is not None and len(text) > 0: 
            with self.data.graphicLock:
                self.instructionBar.add(text)
            savedText = self.instructionBar.sanitizeTextForFile( text )
            self.data.writeGameResult(savedText) 

    def get(self):
        """ Return all the existing text"""
        text = self.instructionBar.get()
        return text

    def setBackground(self, color ):
        with self.data.graphicLock:
            self.instructionBar.setBackground(color)

    def undraw(self):
        self.instructionBar.destroy()


        