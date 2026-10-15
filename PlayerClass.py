__version__ = "8.0"
from CoffeeCanvas import *
import random, datetime

class PlayerClass(Circle):
    """A class to create a player object for placement on a map"""
    TYPE_SWORD = 1 # NOTE: Replace using enum
    TYPE_AXE = 2
    TYPE_POTION = 3
    TYPE_KEY = 4
    TYPE_TREASURE = 5
    TYPE_POSITIONING = 6
    TYPE_TORCH = 7

    # The inventory is limited to these items:
    InventoryItems = {"Sword":TYPE_SWORD, "Damaged Sword":TYPE_SWORD, "Broken Sword":TYPE_SWORD,
                      "Axe":TYPE_AXE, "Potion":TYPE_POTION, "Key":TYPE_KEY, "Treasure":TYPE_TREASURE,
                      "Positioning":TYPE_POSITIONING,"Torch":TYPE_TORCH}
    
    def __init__(self, data, playersMap, **kwargs):
        self.data = data.setResource('player', self)
        self.playersMap = playersMap
        self.map = self.playersMap.map
        self.badges = self.data.getResource('badges') # These are all needed upfront
        self.quiz = data.getResource('quiz')
        self.rewardBox = data.getResource('rewardBox')
        self.statusBar = data.getResource('statusBar')
        self.questionArea = data.getResource('questionArea')
        self.lastQuestionObject = None

        # This is the player object, which is a solid circle on the map. 
        # For a different object change the parent class to that object type (such as picture).
        spotSizeRadius = 10
        playerColor = 'Lime'
        super().__init__(self.map.canvas, -spotSizeRadius, -spotSizeRadius, spotSizeRadius, spotSizeRadius, fill=playerColor)
        
        # Topics recorded for the history of this adventure. Summerized at conclusion and can be saved for grading
        self.history = {'Completed':False, 'Torches_Left':0, 'Winning_Coins':0, 'Questions_Left':0,
                        'Last_Monster':None, 'Last_Touch':None, 'Last_Reward':None,
                        'Last_Theft':None, 'Weapon':False, 'Sword':False, 'Axe':False, 'Met_Boss':False, 
                        'Thief':False, 'Potion':0, 'Found_Potion':False} # History of significant player activity
        
        # Initial items and message
        self.inventory =  [] # Items collected by the player
        coins = kwargs.get('coins', "")
        if len(coins) > 0: self.addReward(coins)     

        # Set the player location on the map - later it will be placed between pre and post player objects
        playerLocation = self.quiz.get("Player Location", "Center" )
        if type(playerLocation) == str: # Right now "Center" is the only selection
            coord = self.map.middleTuple
        else:
            coord = playerLocation
        self.playerCoordinates = coord

    def positionPlayerOnTheMap(self):
        x=self.playerCoordinates[0]
        y=self.playerCoordinates[1]
        self.map.setCenterObject(self, x=x, y=y)
        self.objectPosition = (x, y)

    def recordHistory(self, **dictionary):
        """These are actions the player can perform.  These can be called using the "Action" key in the object dictionary."""
        for key,value in dictionary.items():
            if key in self.history:
                if key == "Potion":
                    self.history[key] += value
                    self.history['Found_Potion'] = True
                elif key == "Torches_Left":
                    self.history[key] += value
                else:
                    self.history[key] = value
                    
    def getHistory(self, key, default=False):
        """Get a specific historical event based on a key word"""
        result = self.history.get(key,default)
        return result
            
    def canYouPickUpSword(self, item):
        """Check if player can pick up a particular sword. Only better swords are picked up"""
        if "Axe" in self.inventory:
            response = False
        elif "Sword" in self.inventory:
            response = False  # Nothing better than a sword
        elif "Damaged Sword" in self.inventory and item == "Broken Sword":
            response = False
        elif "Broken Sword" in self.inventory and item == "Broken Sword":
             response = False
        else:
            response = True
        return response

    def addItem(self, item, value):
        """Add an item to the inventory"""
        kind = value
        if item in self.inventory: return
        if value == PlayerClass.TYPE_AXE:
            self.removeItem("Sword")
            self.removeItem("Damaged Sword")
            self.removeItem("Broken Sword")
            self.history['weapon'] = True
            
        elif value == PlayerClass.TYPE_SWORD:
            if "Sword" in self.inventory:
                pass # Nothing better than a sword
            elif "Damaged Sword" in self.inventory and item != "Broken Sword":
                index = self.inventory.index("Damaged Sword")
                del self.inventory[index]
                self.badges.removeIcon("Damaged Sword")
                self.history['Sword'] = True
                self.history['Weapon'] = True
            elif "Broken Sword" in self.inventory and item != "Broken Sword":
                index = self.inventory.index("Broken Sword")
                del self.inventory[index]
                self.badges.removeIcon("Broken Sword")
                
        elif value == PlayerClass.TYPE_POSITIONING:
            self.positioning = True
            
        elif value == PlayerClass.TYPE_TORCH:
            self.history['Torches Left'] += 1
        self.inventory.append(item)
        amount = self.history.get('Torches Left',0)
        response = self.badges.addIcon(item, kind, amount=amount)
        return response

    def removeItem(self, item):
        """Remove an item from the inventory"""
        if item in self.inventory:
            self.inventory.remove(item)
            self.badges.removeIcon(item)
            self.history['Sword'] = False
            self.history['Weapon'] = False   
            self.history['Axe'] = False                     
    
    def attack(self, target=None):
        """Attack a target object"""
        success = True
        if "Sword" in self.inventory:
            self.history['Sword'] = "Sword"
            self.removeItem("Sword")
            self.addItem("Damaged Sword")
        elif "Damaged Sword" in self.inventory:
            self.history['Weapon'] = "Damaged Sword"
            self.removeItem("Damaged Sword")
            self.addItem("Broken Sword")
        elif "Broken Sword" in self.inventory:
            self.history['Weapon'] = "Broken Sword"
            self.removeItem("Broken Sword")
        elif "Axe" in self.inventory:
            self.history['Weapon'] = "Axe"
        else:
            success = False
            self.history['Weapon'] = None
        if target.lower() == 'dragon': success = False
        if target.lower() == 'troll': success = False
        return success, self.history['Weapon']
    
    def useItem(self, item, swordOK=False):
        """Use an item from the inventory"""
        success = False
        if item in self.inventory:
            if item == "Potion":
                self.inventory.remove(item)
                success =  True
            elif item == "Key":
                self.inventory.remove(item)
                success =  True
            elif item == "Treasure":
                self.inventory.remove(item)
                success =  True
            elif swordOK:
                success = self.attack()
        return success
    
    def addReward(self, coins):
        """Add a coin reward"""
        if len(coins) > 0:
            if isinstance(coins, str):
                self.rewardBox.addReward(coins)
                self.history['Last Reward'] = coins
            elif isinstance(coins, list):
                for coin in coins:
                    self.history['Last Reward'] = coin
                    self.rewardBox.addReward(coin)
                    
    def removeReward(self, coins):
        """Remove a coin reward"""
        if len(coins) > 0:
            if isinstance(coins, str):
                self.rewardBox.removeReward(coins)
                self.history['Last Theft'] = coins
            elif isinstance(coins, list):
                for coin in coins:
                    self.history['Last Theft'] = coin
                    self.rewardBox.removeReward(coin)
    def weaponIsDamaged(self):
        """Determine what damage happens to a weapon. Can change the type and picture"""
        response = True
        if "Axe" in self.inventory:
            response = False # The Axe is never damaged

        elif "Sword" in self.inventory:
            self.badges.removeIcon("Sword")
            index = self.inventory.index("Sword")
            del self.inventory[index]
            self.badges.addIcon("Damaged Sword", PlayerClass.TYPE_SWORD)
            self.inventory.append("Damaged Sword")
            
        elif "Damaged Sword" in self.inventory:
            self.badges.removeIcon("Damaged Sword")
            index = self.inventory.index("Damaged Sword")
            del self.inventory[index]
            self.badges.addIcon("Broken Sword", PlayerClass.TYPE_SWORD)
            self.inventory.append("Broken Sword")

        elif "Broken Sword" in self.inventory:
            self.badges.removeIcon("Broken Sword")
            index = self.inventory.index("Broken Sword")
            del self.inventory[index]
        else:
            response = False
        return response
    
    def nameOfWeapon(self):
        """Return the name of the weapon"""
        if "Sword" in self.inventory:
            return "Sword"
        elif "Damaged Sword" in self.inventory:
            return "Damaged Sword"
        elif "Broken Sword" in self.inventory:
            return "Broken Sword"
        elif "Axe" in self.inventory:
            return "Axe"
        else:
            return None
        
    def stealFromPlayer(self, item):
        """Steal an item from the player"""
        stolenItem = None
        if item in self.inventory:
            self.removeItem(item)
            self.history['Last Theft'] = item
            stolenItem = item
        elif item == "Random Coin":
            purse = self.rewardBox.currentStatus()
            if purse["total"] > 0:
                if purse["copper"] > 0:
                    stolenItem = "Copper"
                    self.rewardBox.removeReward("copper")
                elif purse["silver"] > 0:
                    stolenItem = "Silver"
                    self.rewardBox.removeReward("silver")
                elif purse["gold"] > 0:
                    stolenItem = "Gold"
                    self.rewardBox.removeReward("gold")
                self.history['Last Theft'] = stolenItem
        return stolenItem
    
    def flyToHere(self, coords, showMovement=False):
        """Movement that ignores the path"""
        bbox = self.canvas.widget.bbox(self.id)
        moves = self.determineMouseMoves( coords, bbox)
        self.setFlying(True)
        self.performAutomaticMovement(moves, showMovement=showMovement)
        self.setFlying(False)   
    
    def getPosition(self):
        bbox = self.map.canvas.widget.bbox(self.id)
        x = int((bbox[0] + bbox[2]) // 2)
        y = int((bbox[1] + bbox[3]) // 2)
        return (x,y)
    
    def message(self, *args):
        """Display a message in the status bar"""
        self.statusBar.set(*args)

    # Retrieve a function from a player action - those actions are listed above. 
    # Callable from the data class based on an "Action"
    def retrieveFunctionFromAction(self, classObject, functionName, *args):
        """Retrieve a function from the class based on the function name. classObject and args are not used
        here but this is a standard call and it expects them to be passed in."""
        matchName = functionName.lower()
        match matchName:
            case  "message":
                return self.message
            case "removeaward":
                return self.removeReward
            case "addreward":
                return self.addReward
            case "useitem":
                return self.useItem
            case "attack":
                return self.attack
            case "additem":
                return self.addItem
            case "removeitem":
                return self.removeItem
            case "gethistory":
                return self.getHistory
            case "recordhistory":
                return self.recordHistory
            case _:
                pass
            
        return None
        