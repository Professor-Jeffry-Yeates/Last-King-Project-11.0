# Setup GUI and imports
__version__ = "8.0"
from CoffeeCanvas import *
from CoffeeBean import *
from QuizClass import *
from DataClass import *
from GameTimerClass import *
from SoundMixerClass import *
from ScenarioMapClass import *
from LayoutSizingClass import LayoutSizingClass
from DebuggingClass import DebuggingClass
from VocabularyQuizGeneral import * # This is specific to a map

class SetupGameClass():
    """ Initial setup for a dungeon game. Additional connections needed within various scenarios/scenes."""
    def __init__(self, quizContentName, specificVocabulary=None, debugging=False, shortcut=False, showPath=False):

        self.debuggingOn = debugging # Set to True to disable some error catching and enable testing controls
        self.showPath = showPath # Set to True to overlay the path in white, over the map

        self.quiz = QuizClass(quizContentName) 
        self.window = Window(self.quiz["Quiz Name"], coord=(10,10), width=1350, height=850, resizable=True, 
                        EventDriven=True, checkBoxFont=("TKDefaultFont", 14))

        self.canvas = Canvas(self.window, background="LightBrown", width=1360, height=750, 
                        scrolling=True, WASD=True, tags="mainCanvas", development=self.debuggingOn)
        self.size = LayoutSizingClass(self.canvas.width,self.canvas.height)
        self.text = Text(self.canvas, *self.size("title"), text=f"{self.quiz['Title']} - Adventures in Coding", 
                        font=("Papyrus", 24 ), background="LightBrown")

        vocabulary = VocabularyQuizGeneral(specificVocabulary)
        self.data = DataClass(self.canvas, vocabulary, size=self.size, debugging=self.debuggingOn, quiz=self.quiz)
        self.soundMixer = SoundMixerClass(self.data) 
        self.debugging = DebuggingClass(self.canvas, self.data, debuggingOn=debugging, shortcut=shortcut) 
        self.timers = GameTimerClass(self.data)
        
    def primaryValues(self):
        return (self.canvas, self.data )
    
        """
        Note that these code files are specific to a game:
             VocabularyQuizSpecific
        
        
        """