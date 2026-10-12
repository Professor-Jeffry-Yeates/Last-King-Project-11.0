__version__ = "8.0"
class GenericGroup(): 
    """A GenericGroup is an organizational collection of buttons that appear 
    together and are coordinated together, such as radio buttons and check boxes.  
    Except for selecting, there is no direct graphical representation of a ButtonGroup, that is all handeled
    by the elements individually.  For graphical coordination, use a group and a panel.
    Elements can be untraditional such as buttons, pictures, or picture buttons.
    Element values can be returned as a dictionary using .currentValues(). Elements
    can also handle this on their own. All groups allow preselection from a list.
    Radio groups allow only one button to be selected at a time.  Check groups allow
    multiple buttons to be selected at a time.  The group can be used to collect and
    coordinate the buttons.  The group can be used to select and deselect buttons.
    Return values are in a dictionary with the button name as the key and the value.
    All groups report any button missing a value or if nothing sis selected.
    Checks return all values while radios only report the selected value.
    To use, include the "group" setting for a button and pass in the group object.
    Example: radioGroupOne = Group()
             group=radioGroupOne,
    """
    def __init__(self):
        """ Collects a list of graphic items """ 
        self.groupList = [] 
        self.name = "Group"

    def draw(self):
        for item in self.groupList:
            item.draw()

    def undraw(self):
        for item in self.groupList:
            item.undraw()
        self.groupList.clear()

    def addItem( self, item):
        if isinstance(item,list) or isinstance(item,tuple):
            for eachItem in item:
                self.addItem( eachItem )
        else:
            self.groupList.append(item)

    def removeItem( self, item):
        if isinstance(item,list) or isinstance(item,tuple):
            for eachItem in item:
                self.removeItem(eachItem)
        else:
            for i in range(len(self.groupList)):
                if self.groupList[i] == item:
                    self.groupList.pop(i)
                    break

    def currentValues( self ):
        """Return the current return-values of the list buttons."""
        dataDictionary = dict()
        for item in self.groupList:
            try:
                currentValue = item.returnValue
                dataDictionary[item.name] = currentValue if item.selected else ""
            except:
                dataDictionary[item.name] = "Missing"
        
        if len(dataDictionary) == 0:
            dataDictionary['Selection'] = 'No Selection'
        return dataDictionary
        
    def preselectButtons(self, *listOfTuples):
        for item in self.groupList:
            item.forceButtonOff()

        for i in range(len(listOfTuples)):
            (button,status) = self.listOfTuples[i]
            for item in self.groupList:
                if item == button:
                    item.setButtonState(status)
          
    def selectButton(self, button):
        for i in range(len(self.groupList)):
            eachItem = self.groupList[i]
            if eachItem == button:
                eachItem.turnButtonOn()
                
    def deselectButton(self, button): 
        for i in range(len(self.groupList)):
            eachItem = self.groupList[i]
            if eachItem.button == button:
                eachItem.turnButtonOff()

    def deselectEverything(self): 
        for i in range(len(self.groupList)):
            eachItem = self.groupList[i]
            eachItem.turnButtonOff()

class RadioButtonGroup(GenericGroup): 
    """A RadioButtonGroup is an organizational collection of buttons that appear 
    together and are coordinated together, such as radio buttons and check boxes.  
    Except for selecting, there is no direct graphical representation of a ButtonGroup, that is all handeled
    by the elements individually.  For graphical coordination, use a group and a panel.
    Elements can be untraditional such as buttons, pictures, or picture buttons.
    Element values can be returned as a dictionary using .currentValues(). Elements
    can also handle this on their own. All groups allow preselection from a list.
    Radio groups allow only one button to be selected at a time.  Check groups allow
    multiple buttons to be selected at a time.  The group can be used to collect and
    coordinate the buttons.  The group can be used to select and deselect buttons.
    Return values are in a dictionary with the button name as the key and the value.
    All groups report any button missing a value or if nothing sis selected.
    Checks return all values while radios only report the selected value.
    To use, include the "group" setting for a button and pass in the group object.
    Example: radioGroupOne = Group()
             group=radioGroupOne,
    """
    def __init__(self):
        super().__init__()
        self.radio = True 
        self.name = "RadioGroup"
        
    def selectButton(self, button):
        for i in range(len(self.groupList)):
            eachItem = self.groupList[i]
            if eachItem == button:
                eachItem.turnButtonOn()
            else:
                eachItem.forceButtonOff()
                
    def currentValues( self ):
        """Return the current return-values of the list buttons."""
        dataDictionary = dict()
        for item in self.groupList:
            try:
                if item.selected:
                    currentValue = item.returnValue
                    dataDictionary[item.name] = currentValue
                    break
            except:
                pass

        if len(dataDictionary) == 0:
            dataDictionary['Selection'] = 'No Selection'
        return dataDictionary
    
    def preselectButtons(self, selectionTuple):
        (button,status) = selectionTuple
        for item in self.groupList:
            if item == button:
                item.setButtonState(status)
                            
class CheckBoxGroup(GenericGroup): 
    """A CheckBoxGroup is an organizational collection of buttons that appear 
    together and are coordinated together, such as radio buttons and check boxes.  
    Except for selecting, there is no direct graphical representation of a ButtonGroup, that is all handeled
    by the elements individually.  For graphical coordination, use a group and a panel.
    Elements can be untraditional such as buttons, pictures, or picture buttons.
    Element values can be returned as a dictionary using .currentValues(). Elements
    can also handle this on their own. All groups allow preselection from a list.
    Radio groups allow only one button to be selected at a time.  Check groups allow
    multiple buttons to be selected at a time.  The group can be used to collect and
    coordinate the buttons.  The group can be used to select and deselect buttons.
    Return values are in a dictionary with the button name as the key and the value.
    All groups report any button missing a value or if nothing sis selected.
    Checks return all values while radios only report the selected value.
    To use, include the "group" setting for a button and pass in the group object.
    Example: radioGroupOne = Group()
             group=radioGroupOne,
    """
    def __init__(self):
        super().__init__()
        self.check = True
        self.name = "CheckBoxGroup"
        
class GenericTargetGroup(GenericGroup): 
    """A GenericTargetGroup is an organizational collection of buttons that appear 
    together and are coordinated together, such as radio buttons and check boxes.  
    Except for selecting, there is no direct graphical representation of a ButtonGroup, that is all handeled
    by the elements individually.  For graphical coordination, use a group and a panel.
    Elements can be untraditional such as buttons, pictures, or picture buttons.
    Element values can be returned as a dictionary using .currentValues(). Elements
    can also handle this on their own. All groups allow preselection from a list.
    Radio groups allow only one button to be selected at a time.  Check groups allow
    multiple buttons to be selected at a time.  The group can be used to collect and
    coordinate the buttons.  The group can be used to select and deselect buttons.
    Return values are in a dictionary with the button name as the key and the value.
    All groups report any button missing a value or if nothing sis selected.
    Checks return all values while radios only report the selected value.
    To use, include the "group" setting for a button and pass in the group object.
    Example: radioGroupOne = Group()
             group=radioGroupOne,
    """
    def __init__(self, activate=None):
        super().__init__(self )
        self.target = True
        self.name = "TargetGroup"
        self.connect = False
        self.launch = False
        self.latch = False
        self.activateFunction = activate # (self,object=None)
        
    def addItem( self, item):
        self.groupList.append(item)
        
class LaunchTargetGroup(GenericTargetGroup):
    def __init__(self, activate=None):
        super().__init__(activate=activate)
        self.launch = True

class LatchTargetGroup(GenericTargetGroup):
    def __init__(self, activate=None):
        super().__init__(activate=activate)
        self.latch = True

        
class ConnectTargetGroup(GenericTargetGroup):
    def __init__(self, activate=None, travel=None, deactivate=None):
        super().__init__(activate=activate)
        self.connect = True
        self.travelFunction = travel # (self,object=None)
        self.deactivateFunction = deactivate #(self,object=None)
        