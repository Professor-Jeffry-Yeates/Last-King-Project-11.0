__version__ = '11.0'
from ItemClass import ItemClass

class SpiderClass(ItemClass):
    """ Spider Class for the Spider in the game. Based off of the Item Class"""

    def __init__(self, data, dictionary, *args, **kwargs):
        super().__init__(data, dictionary, *args, **kwargs, gender="she")
        
        self.SpiderBooty = None
        self.SpiderThieving = 0
        self.SpiderThievingMax = 1

        # Spider specific messages for common actions
        self.ItemDictionary["damaging weapon"] = '  {0} says "{1} is not impressed with your {2} but has a shell polishing appointment and nails to paint"'
        self.ItemDictionary["attacking retort"] = '{0} waves four claws \"Bye Bye, Bye Bye\" as she crawls through a Rous tunnel and disappears into the ceiling'
        self.ItemDictionary["wakingup"] = "  {0} groggily wakes up then gives you a hard stare with most of her eyes!"   
        self.ItemDictionary["wakingup weapon"] = '  {0} says "{1} are not impressed with your {2} but has a shell polishing appointment and nails to paint!"'
        self.ItemDictionary["wakingup retort"] = '  {0} looks a bit irritated since they need so much beauty sleep (between you and me it doesn\'t help) and {1} do not seem to move!'  
        self.ItemDictionary["defending"] = '  {0} says "{1} are not impressed with your {2} but has a shell polishing appointment and nails to paint!"'
        self.ItemDictionary["defending weapon"] = '  {0} does point out you may have damaged your {0} when you missed and hit the floor!'
        self.ItemDictionary["ignoring"] = "  The arrogant spider named {0} is ignoring you as unimportant. Perhaps you should leave it alone! You can't hurt {1} anyways!"
        self.ItemDictionary["sleeping"] = "  {0} the very tired spider is asleep. Perhaps you should leave now before {[1}]} gets hungry!"

        # Additional spider actions that an Item Class does not have. Add them to possible actions.
        self.GoingToSleep = self.addAction(self.goingToSleep)
        self.Screaming = self.addAction(self.screams)
        self.WakingupScreaming = self.addAction(self.wakingUpScreaming) 
        self.AttemptingToSteal = self.addAction(self.attemptingToSteal)  

    # Variuos spider actions
    def goingToSleep(self, *args):
        self.instructionsToPlayer = '  "Welcome back thief.  Try not to steal anything while I am asleep." Said the Spider, then with a great yawn it settled down to long nap.'
        self.ItemMatch = self.Sleeping                            

    def wakingUpScreaming(self, *args):
        self.instructionsToPlayer = "  The Spider must have woken up with a start!  You are not sure if she is angry or just startled, but she quickly runs into the shadows! What would you do if you woke up and found some stranger poking you?"
        self.status = "The Spider is gone, maybe to return with revenge in her eyes... or not."
        self.sound = "Scream"
        self.ItemMatch = self.Leaving
        if self.player is None: self.player = self.data.getResource('player')
        playerCenter = self.player.playerCoordinates
        myCenter = self.mapObject.getCenter()
        x =  myCenter.x - playerCenter.x
        y =  myCenter.y - playerCenter.y
        self.flee_x = myCenter - x
        self.flee_y = myCenter - y
        self.ItemMatch = self.Leaving
        self.fleeing()   

    def screams(self, *args):
        if self.ItemMatch == self.NotActivated: self.activation()
        sound = "Scream"
        self.ItemMatch = self.Ignoring   

    def attemptingToSteal(self, *args):
        """Called by Defending"""
        rewardBox = self.data.getResource('rewardBox')
        currentStatus = rewardBox.currentStatus()
        
        # There must be something to steal
        if currentStatus["total"] == 0:
            instructionsToPlayer = f'  {self.ItemName} the spider catches you and shouts "Tag, ' + "you're it! Too bad you are so poor I can't steal anything!  "
            status = "Good thing you don't have any coins! Is that a good thing?"
        
        # The spider has stolen enough
        elif self.SpiderThieving > self.SpiderThievingMax:
            instructionsToPlayer = f"  The gentle and caring spider {self.ItemName} has stolen enough from you!  "
            status = "Look out, she's got 8 hands!"
            
        else: # Attempt to steal, note how to explain if you stole before
            preposition = "a" if self.SpiderBooty is None else "another"
            player = self.data.getResource('player')
            self.SpiderBooty = player.stealFromPlayer("Random Coin")
            if self.SpiderBooty is None:
                instructionsToPlayer = f"  The sad spider {self.ItemName} can't find any more coins to steal! She cries, "+'"Too bad you are so poor!"  '
                status = "Good thing you don't have any coins! Is that a good thing?"
            else:
                self.SpiderThieving += 1
                instructionsToPlayer = f"  The harmless and unaggressive spider named {self.ItemName} has stolen {preposition} {self.SpiderBooty} coin from you because you are a big meanie!"
                instructionsToPlayer += f"  She works on her eye shadow - which is quite the task with six eyes!"
                status = f"  {self.ItemName} the spider teases you for lack of preparedness and urges you to leave!"
                soundMixer = self.data.getResource('soundMixer')
                soundMixer.playSound("Scream")
                
        self.ItemMatch = self.Defending    
        return instructionsToPlayer, status
    
# Alternative spider classes
class SleepingSpiderClass(SpiderClass):
    def __init__(self, data, dictionary, *args, **kwargs):
        super().__init__(data, dictionary, *args, **kwargs)

class ScreamingSpiderClass(SpiderClass):
    def __init__(self, data, dictionary, *args, **kwargs):
        super().__init__(data, dictionary, *args, **kwargs)

class DefendingSpiderClass(SpiderClass):
    def __init__(self, data, dictionary, *args, **kwargs):
        super().__init__(data, dictionary, *args, **kwargs)
        self.ItemMatch = self.Defending
        self.DefaultAction = self.Defending

class AttackingSpiderClass(SpiderClass):
    def __init__(self, data, dictionary, *args, **kwargs):
        super().__init__(data, dictionary, *args, **kwargs)
        self.ItemMatch = self.AttemptingToSteal 
        self.DefaultAction = self.AttemptingToSteal

class IgnoringSpiderClass(SpiderClass):
    def __init__(self, data, dictionary, *args, **kwargs):
        super().__init__(data, dictionary, *args, **kwargs)
        self.ItemMatch = self.Ignoring
        self.DefaultAction = self.Ignoring