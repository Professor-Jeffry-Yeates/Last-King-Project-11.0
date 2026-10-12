__version__ = "8.0"
from CoffeeBean import *
from CoffeeCanvas import *
from MapClass import *
from PlayerClass  import *
from datetime import *
__version__ = "7.1.1"

class BadgesClass():
    """ This class holds 'badges' or graphical representations of game or player attributes. They are specifically 
    placed in tkinter slots. Their contant positions are listed below.
    PARAMETERS:
         canvas:     where to draw graphics
         data:       all game data
         arguments:  x,y, width, height of badges holder
         dictionary: 'tags' with default value
                    'ObjectPath' for source of graphics
    """
    POTION_SLOT = 0    # Glass bottle of a potion
    TORCH_SLOT = 1     # Torch (optoional GIF)
    POSITION_SLOT = 2  # Degug (x,y) location of center object's center
    WEAPON_SLOT = 3    # Optional weapon
        
    def __init__(self, canvas, data, *args, **kwargs):
        self.canvas = canvas
        self.data = data.setResource('badges', self) # Registers itself in data for access and returns the data object
        self.map = data.getResource('map') # Assumes map existence or error
        self.dictionary = dict(**kwargs)
        self.tags = self.dictionary.pop('tags',"badges")

        # Gather icon graphics into a list
        quiz = data.getResource('quiz')  # Assumes quiz existence or error
        self.icons = dict(folder=quiz.dictionary["Objects Path"])
        self.icons['Sword'] = os.path.join(self.icons['folder'], "Sword.png")
        self.icons['Broken Sword'] = os.path.join(self.icons['folder'], "Broken Sword.png")
        self.icons['Damaged Sword'] = os.path.join(self.icons['folder'], "Damaged Sword.png")
        self.icons['Torch'] = os.path.join(self.icons['folder'], "Torch.png")
        self.icons['Axe'] = os.path.join(self.icons['folder'], "Axe.png" )
        self.iconsInUse = dict()
        
        self.potionIcon = None
        self.swordIcon = None
        self.torchIcon = None
        self.positioningObject = None
        self.positioningAvailable = False

        title = "Badges"
        standardFont = ("TKDefaultFont", 14)

        # Get the positioning of the question area
        (self.x,self.y,self.width,self.height) = self.coordinatesFromArguments(args)

        # Frame contents
        frameHeight = 70
        badgesFormat = dict( sticky="full", relief=tk.SOLID, borderwidth=2, 
                                  font=(standardFont[0], standardFont[1], 'bold italic'), columnweights=1 )
        self.badgesFrame = LabelFrame( self.canvas, badgesFormat, text=title, x=self.x, y=self.y, 
                                        width=self.width, height=frameHeight) 

        frameFormat = dict( sticky="full", borderwidth=0 )#, relief=tk.SOLID)
        self.iconFrame = Frame( self.badgesFrame, frameFormat, columnweights=4, rowweights=1)
        
    def coordinatesFromArguments(self, args):
        """ Return separate x,y, width, height from arguments of different kinds and populations"""
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

    def addIcon(self, icon, kind, amount=0):
        """Add an icon to the question area
           PARAMETERS
           icon:  Required string matching icon name (see above) for graphic file
           kind:  PlayerClass.TYPE_SWORD etc... (see PlayerClass)
           amount: Optional number with icon, not used by all icons
        """
        
        # Get the path to the icon graphic
        if icon is None: return
        iconPathToUse = self.icons.get(icon,None)
        if iconPathToUse is None:
            self.icons[icon] = os.path.join(self.icons['folder'],icon + ".png")
            iconPathToUse = self.icons[icon]
            
        # For swords, lock graphics (tkinter may be thread safe now) and place graphic in a label
        if kind == PlayerClass.TYPE_SWORD:
            with self.data.graphicLock:   
                if self.swordIcon is not None: self.swordIcon.widget.destroy()
                self.swordIcon = Label( self.badgesFrame, image=iconPathToUse, coord=(0,BadgesClass.WEAPON_SLOT), sticky=tk.RIGHT)
            self.iconsInUse['Sword'] = icon   
            return self.swordIcon
        
        # (x,y) position used in debugging with a colored background
        elif kind == PlayerClass.TYPE_POSITIONING:
            color = self.canvas.background
            if ( controls := self.data.getResource('debugging') ): 
                if controls.active: color = "Lime"
            with self.data.graphicLock:   
                self.positioningObject = Label( self.badgesFrame, text="", coord=(0,BadgesClass.POSITION_SLOT), 
                                               font=standardFont, background=color, sticky=tk.NSEW)
            return self.positioningObject
        
        elif kind == PlayerClass.TYPE_TORCH:
            with self.data.graphicLock: 
                
                # No more torches
                if amount <=0:  
                    if self.torchIcon is not None:
                        self.torchIcon.widget.destroy()
                        self.torchIcon = None
                        self.iconsInUse['Torch'] = False
                else:
                    # Torch may include the optinal amount
                    oldicon = self.torchIcon
                    if os.path.exists(iconPathToUse):
                        self.torchIcon = Label( self.badgesFrame, text=f"{amount} X ", image=iconPathToUse, 
                                               coord=(0,BadgesClass.TORCH_SLOT), font=standardFont, 
                                              compound=tk.RIGHT, sticky=tk.NSEW)
                        if oldicon is not None: oldicon.widget.destroy()
                        self.iconsInUse['Torch'] = True
                    else:
                        self.data.logError(f"Torch icon not found in bat {iconPathToUse}")
            return self.torchIcon
        
        # Axe fits in sword slot replacecing any sword
        elif kind == PlayerClass.TYPE_AXE:
            if self.swordIcon is not None: self.swordIcon.widget.destroy()
            with self.data.graphicLock: 
                self.swordIcon = Label( self.badgesFrame, image=iconPathToUse, coord=(0,BadgesClass.WEAPON_SLOT), 
                                       sticky=tk.RIGHT)
            self.iconsInUse['Axe'] = True
            self.iconsInUse['Sword'] = None   
            return self.swordIcon
        
        # Potions are selectable so a button is used with a call function
        elif kind == PlayerClass.TYPE_POTION:
            if self.potionIcon is not None: self.potionIcon.widget.destroy()
            with self.data.graphicLock: 
                self.potionIcon = Button( self.badgesFrame, image=iconPathToUse, coord=(0,BadgesClass.POTION_SLOT), 
                                         sticky=tk.RIGHT, command=self.data.usePotion)
            self.iconsInUse['Potion'] = True  
            self.activePotion = icon
            return self.potionIcon
        self.parentCanvas.update()
        return None

    def returnIcon(self, kind):
        """Return the icon to the question area
           PARAMETERS
           kind:  PlayerClass.TYPE_SWORD etc... (see PlayerClass)
        """
        response = None
        if kind == PlayerClass.TYPE_SWORD:
           usingSword = self.iconsInUse.get('Sword', None)
           return usingSword is not None
        elif kind == PlayerClass.TYPE_POSITIONING:
            return self.positioning is not None
        elif kind == PlayerClass.TYPE_TORCH:
            return self.iconsInUse.get('Torch', 0)
        elif kind == PlayerClass.TYPE_AXE:
            return self.iconsInUse.get('Axe', False)
        elif kind == PlayerClass.TYPE_POTION:
            return self.iconsInUse.get('Potion', False)
        return None

    def removePotion(self, *args):
        """ Specifically remove a potion. Arguments not used but may exist"""
        if self.potionIcon is not None: 
            with self.data.graphicLock: 
                self.potionIcon.widget.destroy()
            self.potionIcon.image = None
            self.potionIcon = None
            self.activePotion = None
            self.iconsInUse['Potion'] = False 

    def removeIcon(self, icon, amount=0):
        """Remove the icon from the question area or change its amount
           PARAMETERS
           icon:  Required string matching icon name (see above) for graphic file
           amount: Optional number with icon, not used by all icons"""
        if icon is None: return
        kind = PlayerClass.InventoryItems.get(icon, None)

        # It could be a version of an icon, so check the last 3 letters
        if kind is None:
            tryingIcon = icon[-3]
            for key, value in PlayerClass.InventoryItems.items():
                tryKey = key[-3]
                if tryingIcon == tryKey:
                    kind = value
                    break
                
        if kind is not None:
            match kind:
                case PlayerClass.TYPE_SWORD:
                    if self.swordIcon is not None:
                        with self.data.graphicLock: 
                            self.swordIcon.widget.destroy()
                        self.swordIcon = None
                        self.iconsInUse['Sword'] = None  
                        
                case PlayerClass.TYPE_POSITIONING:
                    map = self.data.getResource('map')
                    if map is not None and map.positioning is not None:
                        with self.data.graphicLock: 
                            map.positioning.widget.destroy()
                        map.positioning = None
                        self.iconsInUse['Positioing'] = False  
                        
                case PlayerClass.TYPE_TORCH:
                    with self.data.graphicLock: 
                        if amount <1:
                            if self.torchIcon is not None:
                                self.torchIcon.widget.destroy()
                                self.torchIcon = None
                        elif self.torchIcon is not None:
                            self.torchIcon.setText(f"{amount} X ")
                    self.iconsInUse['Torch'] = max(0,amount)
                    
                case PlayerClass.TYPE_AXE:
                    if self.swordIcon is not None:
                        with self.data.graphicLock: 
                            self.swordIcon.widget.destroy()
                        self.swordIcon = None
                        self.iconsInUse['Axe'] = False  
                        
                case PlayerClass.TYPE_POTION:
                    if self.potionIcon is not None:
                        with self.data.graphicLock: 
                            self.potionIcon.widget.destroy()
                        self.potionIcon = None
                        self.iconsInUse['Potion'] = False 
                case _:
                    pass

    def updatePositioning(self, *args):
        """ Update the current position on the center object"""
        if self.positioningAvailable:
            if self.positioningObject is not None:
                if self.map is not None and self.map.positioning is not None:
                    result = self.map.objectPosition
                    if result is not None:
                        try:
                            a = int(result[0])
                            b = int(result[1])
                            x,y =  self.map.convertMapCoordinatesToStandard(a,b)
                        except:
                            self.data.logError("BadgesClass.updatePositioning: Unable to convert positioning to integers")
                        else:
                            self.positioningObject.set(f"{x},{y}")

    def stop(self, *args):
        """ Remove the class, common function in classes. Arguments not used but may exist"""
        self.positioningObject = None
        with self.data.graphicLock: 
            if self.badgesFrame is not None:
                self.badgesFrame.destroy()
            if self.iconFrame is not None:
                self.iconFrame.destroy()