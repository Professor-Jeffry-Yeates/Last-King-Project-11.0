__version__ = '8.0'
from CoffeeCanvas import *
from CoffeeBean import *

class StatusClass():
    """ This class displays short sentences of status for the player.
    PARAMETERS:
         canvas:     where to draw graphics
         data:       all game data
         arguments:  x,y, width, height of status holder
         dictionary: 'tags' with default value
                    'ObjectPath' for source of graphics
                    """
                    
    def __init__(self, canvas, data, x, y, width, height, **kwargs):
        self.canvas = canvas
        self.data = data.setResource('statusBar', self) # Registers itself in data for access and returns the data object
        title = "Status"
        providedText = kwargs.get('text', "Status: Ready")
        self.replacementDictionary = {}
        self.tags = kwargs.get('tags',"status")

        # Standard formatting dictionaries
        standardFont = ("TKDefaultFont", 12)
        standardFormat = dict( sticky="ew", padx=5, pady=5, font=standardFont)
        frameFormat = dict( sticky="full", relief=tk.SOLID, borderwidth=1, font=(standardFont[0], standardFont[1], 
                            'bold italic'), pady=5)
        
        self.statusFrame = LabelFrame( canvas, frameFormat, text=title, x=x, y=y, width=width, height=height, 
                                      rowweights=1, columnweights=1, padx=10, pady=5) 
        self.statusBar = TextBox(self.statusFrame, standardFormat, textFont=("TKDefaultFont", 12),  
                                 relief="flat", wrap="word", padx=10, pady=5, height=height, scrolling=True, 
                                 kind="vertical", readOnly=True)
        self.statusBar.setReadOnly(True)
        self.statusBar.set( providedText )

    def set(self, *args):
        """Clear, then display the status bar text.  If args is a single string, set it as the text. If more than one argument,
        then args[0] is a format string and each additional arg is a file from which to randomly get a substitute string.
        If the file is not found, it will be set to "file missing". If args is empty, do nothing. Once read-in,
        for faster access, file content are stored in arrays in a dictionary and access by the filename as a key.
        """
        length = len(args)
        if length == 0: return
        text = args[0]
        if text is not None and len(text) > 0:             
            if self.data is not None:
                
                # Everything OK, replace, then display the text using a lock for thread protection
                text = self.data.vocab(text)
                with self.data.graphicLock: 
                    self.statusBar.set(text) 

    def add(self, *args):
        """ Add text to any existing text in the status box"""
        if len(args) == 0: return
        text = args[0]
        if text is None or len(text) == 0: return
        if self.data is not None: 
            
            text = self.data.vocab(text)
            with self.data.graphicLock: 
                self.statusBar.add(text)
                self.statusBar.widget.see(tk.END)

    def get(self):
        """ Return any text in the status box"""
        with self.data.graphicLock: 
            return self.statusBar.get()
        
    def setBackground(self, color ):
        with self.data.graphicLock: 
            self.statusBar.setBackground(color)

    def undraw(self):
        self.statusFrame.destroy()