__version__ = '8.0'
from MapClass import PhantomMapClass
import enum

# Enum of dragon actions stored in self.dragonMatch
class DragonIs(enum.Enum):
        NotActivated = enum.auto() # First time in
        GoingToSleep = enum.auto() # In process of going to sleep permanently
        Greeting = enum.auto() # First greeting of player
        QuestioningGuest = enum.auto() # Continuous questioning of player until no more questions, then sleeping
        QuestioningThief = enum.auto() # One missed question then sleeping
        Sleeping = enum.auto() # Sleeping, continue to snore and ignore player
        Slumbering = enum.auto() # Activated but not awake yet
        Wakingup = enum.auto() # Awake and waiting for the player
        WaitingForAnswer = enum.auto() # Waiting for player to answer question

class DragonClass():
    """ Dragon Class for the Dragon Boss in the game. 
    Initialization is not instantiation, but sets up for it. """

    def __init__(self, data, dragonDictionary, *args, **kwargs):
        self.data = data
        self.arguments = args
        self.dragon = None
        self.dictionary = dict(**dragonDictionary)
        self.dragonColor = None
        self.name = ""
        self.dragonEyes = None
        self.dragonMatch = DragonIs.NotActivated
        self.lastDragonMatch = None
        self.phantomObject = None

    def activation(self):
        """ Activate the dragon for doing things but no initial action specified"""
        # Get the specific color for the dragon for its picture
        filename = self.dictionary.get('File', "")
        if len(filename) > 0:
            endingLetter = filename.find("SleepingDragon")
            self.color = filename[:endingLetter]
        self.name = 'dragon ' + self.dictionary.get('Special', '')
        self.dragonTreasure = self.dictionary.get('DragonTreasure', None)
        self.dragonColor = self.dictionary.get('Color', "")
        
        # Retrieve the map object for its characteristics along with any initial action
        dragonMapObject = self.dictionary.get("MapObject", None)
        if dragonMapObject is not None: dragonMapObject.addAction(self.activate)

        # Find its open eyes
        for objectDictionary in self.data.objects:
            if objectDictionary['Purpose'] == "Eyes of Dragon":
                self.dragonEyes = objectDictionary["MapObject"]
                break 

    def awakenByThief(self):
        """ Specific action if the player steals called by external class"""
        if self.dragonMatch == DragonIs.NotActivated:
            self.activate()
        if self.dragonMatch == DragonIs.Slumbering:
            self.dragonEyes.unhide()
            self.dragonEyes.levelUp() # Bring above the dragon
            self.dragonMatch = DragonIs.Greeting
        if self.dragonMatch != DragonIs.Sleeping:
            self.data.recordHistory(Last_Theft="Gold", Thief=True)
            soundMixer = self.data.getResource('soundMixer')
            if soundMixer is not None: soundMixer.playSound("Snore")
    
    def blinkEyes(self):
        """ Externally timed or called to blink the eyes"""
        map = self.data.getResource('map')
        self.dragonEyes.hide()
        map.canvas.update()
        map.canvas.sleepBriefly.start()
        self.dragonEyes.unhide()
        map.canvas.update()
    
    def activate(self, *args):
        """ Function to activate the boss/dragon. Matching can setup the next matching so loop until no more matching is needed. """
        looping = True
        self.data.stopMoving() # Stop player movement
        player = self.data.getResource('player')
        soundMixer = self.data.getResource('soundMixer')
        instructionsToPlayer = self.data.getResource('instructions')
        statusBar = self.data.getResource('statusBar')
        
        # Loop trhough possible actions. Actions may call other actions until loop is done.
        while looping:
            askingQuestion = False
            sound = ""
            specificStatus = ""
            specificInstructions = ""

            match self.dragonMatch:
                case DragonIs.NotActivated:
                    self.activation()
                    self.dragonMatch = DragonIs.Slumbering

                case DragonIs.Slumbering:
                    self.dragonEyes.hide()
                    self.dragonEyes.levelUp() # Bring above the dragon
                    # Get the dragons dictionary color and use in sentence
                    specificInstructions += f"Before you is an ancient and gigantic {self.dragonColor.lower()} dragon. If you don't see it's burning red eyes then it may be asleep. It's scales are dented and worn, and you notice one of it's front legs is curiously missing. It's fangs, however, are visibly sharp and dangerous!"
                    specificStatus += "Perhaps you should leave now as death awaits in slumber!"
                    sound = "Snore"
                    self.dragonMatch = DragonIs.Wakingup
                    looping = False

                case DragonIs.Wakingup:
                    specificStatus += "The dragon may be asleep or he is ignoring you! Oops, he woke up! Run!!"
                    with self.data.graphicLock:
                        self.dragonEyes.unhide()
                    sound = "Laugh"
                    self.dragonMatch = DragonIs.Greeting
                    looping = False

                case DragonIs.Greeting:
                    # Boss will decide what to do based on: prior meeting, thieving, no sword with player, or thief questioning
                    # Dictionary special should be its name
                    sound = "Laugh"
                    playerIsAThief = player.getHistory("Thief", False)
                    axe = player.getHistory("Axe", False)
                    weaponInHand = player.nameOfWeapon()
                    previouslyMetBoss = player.getHistory("Met_Boss", False)

                    if playerIsAThief:
                        if previouslyMetBoss:
                            specificInstructions += '"Welcome back thief.  Try not to steal anything while I am asleep." Said the dragon, then with a great yawn it settled down to long nap. '
                            specificStatus += "I don't think it is going to ask any more questions. "
                            self.dragonMatch = DragonIs.GoingToSleep
                        else:
                            specificInstructions += f'In a low voice the dragon says "Greetings lunch. You stole some of my gold. very brave, but foolish. I shall question you, and then I will let you go! Anyways, its almost time for my nap". '
                            specificStatus += "Answer the question ... choose carefully! "
                            player.recordHistory(Met_Boss=True,Last_Monster="Boss")
                            self.blinkEyes()
                    else:
                        missedQuestionExists = self.data.missedQuestionStatus()
                        if previouslyMetBoss:
                            if missedQuestionExists:
                                specificInstructions += f'"Not satisfied yet?" queries the dragon. "Here is another question." '
                                specificStatus += "The dragon has another question. "
                            else:
                                specificInstructions += f'"I have bad news." says the dragon. "There are no more missed question so keep looking for treasure in the dungeon." '
                                specificStatus += "The dragon will only ask questions you have missed. Keep up the good work! "
                        else:
                            specificInstructions += f'You have entered the lair of the {self.dragonColor.lower()} dragon. It is a fearsome sight, and you feel a chill run down your spine. '
                            if not axe and not weaponInHand:
                                specificInstructions += f'  The dragon eyes you warily, then says "You are quite brave to face me without a weapon. Here, take the Last King\'s axe. It\'s is useful against spideras and rous. He doesn\'t need it - he had an axe-cident!!" '
                                specificStatus += "You have received the Last King\'s battle axe! "
                                self.data.pickupAxe()
                            else:
                                if missedQuestionExists:
                                    specificStatus += "The dragon has a question for you to answer. "
                                else:
                                    specificStatus += "The dragon will only ask questions you have missed. Keep up the good work! "
                            
                            if missedQuestionExists:
                                specificInstructions += 'Slightly amused, the dragon said "To keep me entertained and not thinking of inviting you for dinner, here is a question for you that has been bothering me." '
                            else:
                                specificInstructions += 'Slightly irritated, the dragon sharply spoke "To keep me entertained and not thinking of inviting you for dinner, keep looking for treasure in the dungeon." '
                            self.blinkEyes()

                    player.recordHistory(Met_Boss=True, Last_Monster="Boss")
                    if self.dragonMatch != DragonIs.GoingToSleep:
                        askingQuestion = True
                        looping = False

                case DragonIs.GoingToSleep:
                    self.dragonMatch = DragonIs.Sleeping

                case DragonIs.Sleeping:
                    sound = "Snore"
                    specificStatus += "The dragon is asleep. Perhaps you should leave now before it gets hungry! "
                    looping = False

                case _: # Anything else just snore or blink
                    if self.lastDragonMatch != self.dragonMatch: 
                        if self.dragonMatch == DragonIs.Sleeping:
                            sound = "Snore"
                        else:
                            self.blinkEyes()
                    looping = False
        
            # Once the loop is complete, display any status, messages, or instructions
            if len(specificInstructions) > 0: 
                instructionsToPlayer = self.data.getResource('instructions')
                if instructionsToPlayer is not None: instructionsToPlayer.newSection(specificInstructions)
            if len(specificStatus) > 0: 
                statusBar = self.data.getResource('statusBar')
                if statusBar is not None: statusBar.set(specificStatus)
            if len(sound) > 0: 
                soundMixer = self.data.getResource('soundMixer')
                if soundMixer is not None: soundMixer.playSound(sound)

            # Note last action for later reference
            self.lastDragonMatch = self.dragonMatch
            
            # Any question asked uses the Phantom class as no treasure is involved in the question
            if askingQuestion:
                self.phantomObject = PhantomMapClass(self.data, self)
                self.data.questionFunction(self.phantomObject, useMissedQuestions=True)
