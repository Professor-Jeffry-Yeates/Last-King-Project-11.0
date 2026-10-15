__version__ = '8.0'
from CoffeeCanvas import *
import random

class RewardClass():
    """ Place coins and related text into a box so player can see the score.
        Three types of coins (gold, silver, copper)
    PARAMETERS:
         canvas:     where to draw graphics
         data:       all game data
         arguments:  x,y, width, height of reward holder
         dictionary:'tags' with default value
                    'background' Initial background
                    'text' Initial text describing score
                    'font' Initial font
                    'wins' single minimum score of each coin to win
    """
    def __init__(self, canvas, data, x, y, width, height, **kwargs):
        self.canvas = canvas
        dictionary = dict(**kwargs)
        self.data = data.setResource('rewardBox', self)
        self.tags = kwargs.get('tags',"reward")
        background = dictionary.get('background', canvas.colors["White"])
        text = dictionary.get('text', "Coins Collected")
        font = dictionary.get('font', ('TKDefaultFont', 16, 'bold italic'))
        self.wins = dictionary.get('wins', 10)

        # Individual coin graphics stores in lists
        self.goldCoins = []
        self.silverCoins = []
        self.copperCoins = []
        self.completed = False # Minimum reached for win, not reset if more coins lost
        
        # Coin descriptions for graphics
        self.maximumCoinsShowing = 10
        self.coinHeight = 25
        self.coinWidth = 80
        self.thickness = 10
        gap = max(15,int(width/30))
        self.silverCenter = x+width/2
        self.copperCenter = self.silverCenter - self.coinWidth - gap
        self.goldCenter = self.silverCenter + self.coinWidth + gap

        # Setup for coin placment
        self.heights = []
        self.heights.append(y+height-3-int(self.coinHeight/2))
        for i in range(1,self.maximumCoinsShowing):
            self.heights.append(self.heights[i-1]-self.thickness)

        # Draw the graphics
        self.textCenter = Point(x+width/2, int(y+height/2))
        self.coinBox = Rectangle(canvas, x, y, x+width, y+height, fill=background)
        if 0 < self.wins < self.maximumCoinsShowing:
            lineHeight = self.heights[self.wins]
            self.line = Line(canvas, (x+2, lineHeight), (x+width-2, lineHeight), width=2, fill="Red", dash=(4,2))
        self.title = Text(canvas, self.textCenter, text=text, font=font, color="Grey")

    def addReward(self, reward, amount=1):
        """ Determine what coin to add and the amount to add, then add coin(s) with sound effect."""
        
        # Determine what to show
        somethingToShow = False
        for _ in range(amount):
            checkReward = reward.lower()
            if checkReward == "copper":
                x = self.copperCenter
                array = self.copperCoins
            elif checkReward == "silver":
                x = self.silverCenter
                array = self.silverCoins
            elif checkReward == "gold":
                x = self.goldCenter
                array = self.goldCoins
            else:
                return False

            # Only show more stacked coins if the maximum has not been reached (but keep track of totals)
            count = len(array)
            somethingToShow = (count < self.maximumCoinsShowing)
            if somethingToShow:        
                
                # Wobble is a slight mismatch in stacking to randomly separate coins
                wobble = random.randrange(0,self.maximumCoinsShowing)-5 # The wobble factor on the x-axis when they stack
                x += wobble
                y = self.heights[count]
                coin = self.makeCoinShape(x, y, reward)
            else:
                coin = array[-1] # Duplicate last coin graphic
            with self.data.graphicLock:
                self.canvas.displayList(coin)
            array.append(coin)
        
        # One sound per coin group   
        #if somethingToShow: 
        soundMixer = self.data.getResource('soundMixer')
        soundMixer.playSound("Coin")
        return somethingToShow

    def removeReward(self, reward, amount=1):
        """ Determine what coin to remove and the amount to remove, then remove coin(s)."""
        
        # Determine what to remove
        checkAmount = abs(amount)
        checkReward = reward.lower()
        if checkReward == "copper":
            array = self.copperCoins
        elif checkReward == "silver":
            array = self.silverCoins
        elif checkReward == "gold":
            array = self.goldCoins
        else:
            return None
        
        # Removal of coin graphic
        length = len(array)
        if length > 0 and checkAmount > 0:
            soundMixer = self.data.getResource('soundMixer')
            soundMixer.playSound("Scream")
            for _ in range(checkAmount):
                if len(array) > 0:
                    coin = array.pop()
                    with self.data.graphicLock:
                        self.canvas.undisplayList(coin)
            return coin
        return None

    def changeReward( self, *args):
        """Change the amount of a reward coin - generally a degugging function so arguments are needed"""
        
        # Determine what to change
        if len(args) >= 2:
            coin = args[0].lower()
            number = args[1]
            if coin == "copper":
                array = self.copperCoins
            elif coin == "silver":
                array = self.silverCoins
            elif coin == "gold":
                array = self.goldCoins  
            else:
                return
            
            # Make the change to add or remove
            if number == 0:
                count = len(array)
                if count > 0:
                    for _ in range(count):
                        self.removeReward(coin)
            elif number > 0:
                for _ in range(number):
                    self.addReward(coin)
            
    def checkForGameOver(self):
        """ Quick check it coins have reached the minimum win"""
        status = self.currentStatus()
                
        # If there are still torches as time has not run out, run the exit game box code in a short while
        if status["torches"] and not self.completed:
            self.canvas.root.after(100, self.data.exitGameBox)
            self.completed = True
        
        # If completed, but only do once
        elif status["completed"] and not self.completed:
            self.completed = True
            if self.title.drawn:
                self.title.undraw()
                self.title = Text(self.canvas, self.textCenter, text="GAME COMPLETED!\nYOU SHOULD LEAVE\nBEFORE TORCHES RUN OUT", 
                                  font=('TKDefaultFont', 16, 'bold'), fill="DarkRed")
        return status
    
    def currentStatus(self):
        """Return the status of the awards and if completing the game in a dictionary"""
        copper = len(self.copperCoins)
        silver = len(self.silverCoins)
        gold = len(self.goldCoins)
        coinsCollected = (copper >= self.wins) and (silver >= self.wins) and (gold >= self.wins)
        total = copper + silver + gold
        torches = self.data.getHistory('Torches_Left', 0)
        torches = torches == 0
        noMoreQuestions = self.data.noMoreQuestions()
        completed = any([torches, coinsCollected, noMoreQuestions, self.completed])

        dictionary = dict(copper=copper, silver=silver, gold=gold, total=total, completed=completed,
                          torches=torches, coinsCollected=coinsCollected, noMoreQuestions=noMoreQuestions) 
        return dictionary

    def makeCoinShape(self, x, y, metal):
        """Create a coin shape at the given location"""
        coinList = []
        if metal.lower() == "copper":
            metalColor = self.canvas.colors.From_rgb(184,115,51)
        elif metal.lower() == "silver":
            metalColor = self.canvas.colors.From_rgb(192,192,192)
        else: # metal.lower() == "gold":
            metalColor = self.canvas.colors.From_rgb(255,215,0)
        darkerMetalColor = self.canvas.colors.Blend(metalColor, self.canvas.colors["Gray"])

        topOval_p1 = Point(x-self.coinWidth/2, y-self.coinHeight/2)
        topOval_p2 = Point(x+self.coinWidth/2, y+self.coinHeight/2)
        coinBottom = Oval(self.canvas, topOval_p1, topOval_p2, fill=darkerMetalColor, outline="Black", draw=False)
        coinList.append(coinBottom)

        p1 = Point(topOval_p1.x, topOval_p1.y)
        p2 = Point(topOval_p2.x, topOval_p2.y-self.thickness)
        middleOfCoin = Rectangle(self.canvas, p1, p2, fill=darkerMetalColor, width=0, draw=False)
        coinList.append(middleOfCoin)

        leftLine = Line(self.canvas, (p1.x, p1.y+self.thickness/2), (p1.x, p1.y+self.thickness*3/2), width=1, fill="Black", draw=False)
        coinList.append(leftLine)
        rightLine = Line(self.canvas, p2, (p2.x, p2.y-self.thickness), width=1, fill="Black", draw=False)
        coinList.append(rightLine)

        shadeLine1 = Line(self.canvas, (p2.x-3, p2.y+3), (p2.x-3, p2.y-self.thickness+3), width=3, fill="DarkGray", draw=False)
        coinList.append(shadeLine1)
        shadeLine2 = Line(self.canvas, (p2.x-8, p2.y+6), (p2.x-8, p2.y-self.thickness+6), width=2, fill="DarkGray", draw=False)
        coinList.append(shadeLine2)
        shadeLine3 = Line(self.canvas, (p2.x-16, p2.y+7), (p2.x-16, p2.y-self.thickness+7), width=1, fill="DarkGray", draw=False)
        coinList.append(shadeLine3)
        shadeLine4 = Line(self.canvas, (p2.x-30, p2.y+9), (p2.x-30, p2.y-self.thickness+9), width=1, fill="DarkGray", draw=False)
        coinList.append(shadeLine4)

        topOval_p1 = Point(topOval_p1.x, topOval_p1.y-self.thickness)
        topOval_p2 = Point(topOval_p2.x, topOval_p2.y-self.thickness)
        coinTop = Oval(self.canvas, topOval_p1, topOval_p2, fill=metalColor, outline="Black", draw=False)
        coinList.append(coinTop)

        return coinList  
  
    def undraw(self):
        self.coinBox.undraw()
        self.title.undraw()
        self.line.undraw()
  
    def undrawTitle(self):
        self.title.undraw()