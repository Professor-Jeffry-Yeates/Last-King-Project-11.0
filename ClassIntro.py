__version__="11.0.0"
"""

Install these libraries:
For windows install:
    pip install pywin32

For both MacOS and Windows:
    pip install pillow
    pip install pygame-ce       or use below if implemented
    ##pip install pyaudio
    pip install pyodbc
    
For MacOS:# 
    pip install appscript

Executing pip may require this instead:
    python3 -m pip install --upgrade pip
    python3 -m pip install pillow
    python3 -m pip install pygame-ce       or use below if implemented
    ##python3 -m pip install pyaudio
    python3 -m pip install pywin32
    python3 -m pip install appscript
    python3 -m pip install pyodbc
    
If there are C++ build errors, you need C++ v14.0 or higher. Find it at:
https://visualstudio.microsoft.com/visual-cpp-build-tools/
"""
# Setup GUI and imports
from ScenarioMapClass import *
from ScenarioClass import ScenarioClass
from EndingSceneClass import EndingSceneClass
from StudentInfoClass import StudentInfoClass
from DungeonMapClass import DungeonMapClass
from SetupGameClass import SetupGameClass

gameSetup = SetupGameClass("Quiz_Content", debugging=True, shortcut=True, showPath=False)
(canvas, data) = gameSetup.primaryValues()

# Scene 1 is player name input
class sceneOne():
    def __init__(self, canvas, data, returnFunction):
        size = data.getResource("size")
        scene = StudentInfoClass(canvas, data, *size["enterStudent"], 
                                 returnFunction=returnFunction )

# Scene 2 is the scenario map and instructions
class sceneTwo():
    def __init__(self, canvas, data, returnFunction):
        size = data.getResource("size")
        scene = ScenarioMapClass(canvas, data, *size("scenarioMap"),
                senarioInstructions=size("scenarioInstructions"),
                miniCompassCoordinates=size("miniCompass"), 
                returnFunction=returnFunction )

# Part 3 is the dungeon map
class sceneThree():
    def __init__(self, canvas, data, returnFunction):
        size = data.getResource("size")
        scene = DungeonMapClass(canvas, data, *size("scenarioMap"),
                senarioInstructions=size("scenarioInstructions"), 
                returnFunction=returnFunction, showPath=True )


# Part 4 is the ending scene back at home
class sceneFour():
    def __init__(self, canvas, data, returnFunction):
        size = data.getResource("size")
        scene = EndingSceneClass(canvas, data, *size("scenarioMap"), 
                finalMessage=size["enterStudent"],
                senarioInstructions=size("scenarioInstructions"), 
                returnFunction=returnFunction, showPath=gameSetup.showPath )
        
# Define & start the scenarios
senarioFour = ScenarioClass(sceneFour)
senarioThree = ScenarioClass(sceneThree, nextScenario=senarioFour)
senarioTwo = ScenarioClass(sceneTwo, nextScenario=senarioThree)
senarioOne = ScenarioClass(sceneOne, nextScenario=senarioTwo)

senarioOne.startScene(canvas, data)
canvas.mainloop() 
