__version__ = '8.0'
from CoffeeCanvas  import *
from CoffeeColors import *
import socket

class StudentInfoClass():
    """ 
        Set up student entry entry area with background rectangle, student name, student nickname, Cancel and OK
        Cancel exits, OK saves student login, name and nickname (defaults to local server name) into data class. 
        Example position: [300, 300, 400, 200]. Results stored in the data class.
            
    Holds all code needed to initialize, run, and close out asking for student information.
    PARAMETERS:
         canvas:     where to draw graphics
         data:       all game data
         arguments:  x,y, width, height of the class on the canvas
         dictionary: Any needed kwargs
         
    Step 1: Place everything needed into this class
    Step 2: Place the retrieval of sizes and instantiation of this class into its own scene class. EX:
        class sceneFour():
           def __init__(self, canvas, data, returnFunction):
               size = data.getResource("size")
               scene = EndingSceneClass(canvas, data, *size("scenarioMap"), 
                       finalMessage=size["enterStudent"],
                       senarioInstructions=size("scenarioInstructions"), 
                       returnFunction=returnFunction, showPath=gameSetup.showPath )
    Step 3: Instantiate a scenario class with the scene and the scene to call next. Ex:
        senarioOne = ScenarioClass(sceneOne, nextScenario=senarioTwo)
    Step 4: You may need to do this in reverse order to previous scenes are created before access
    Step 5: Call the first scenario, which then instantiates and runs the scene. Ex:
        senarioOne.startScene(canvas, data)
        canvas.mainloop() 
    """
    def __init__(self, canvas, data, x, y, width, height, **kwargs):
        self.canvas = canvas
        self.data = data.setResource('studentInfo', self)
        self.nextFunction = kwargs.get("returnFunction", self.defaultReturn) 
        
        self.entryCanvas = Canvas(self.canvas, x=x, y=y, width=width, height=height, background="LightBrown")
        self.entryTitle = Text(self.entryCanvas, Point(200,30), text="Enter your name and a game name", 
                               font=("TKDefaultFont", 16))
        self.nameLabel = Text(self.entryCanvas, Point(10,70), text="Student name:", anchor='w', 
                              font=("TKDefaultFont", 16))
        self.nameEntry = CanvasEntry(self.entryCanvas, Point(320,120) ,50, fill="White")
        self.nickNameLabel = Text(self.entryCanvas, Point(10,120), text="Game Name:", anchor='w', 
                                  font=("TKDefaultFont", 16))
        text=socket.gethostname()
        self.nickNameEntry = CanvasEntry(self.entryCanvas, Point(320,170), 50, text=text, fill="White")
        self.cancel = CancelButton(self.entryCanvas, Point(100,160), Point(180,190), text="Exit",
                                    action=self.processQuit, squaricle=True)
        self.OKbutton = OKButton(self.entryCanvas, Point(260,160), Point(330,190), OkText="Play", 
                                 action=self.processEntry, squaricle=True)
        self.entryCanvas.update()
        self.canvas.update()

    def processEntry(self, *args):
        studentName = self.nameEntry.getText()
        if studentName.endswith('****'):
            studentName = studentName[:-4]
            self.data.provideMoreTorches(2)
        elif studentName.endswith('**'):
            studentName = studentName[:-2]
            self.data.provideMoreTorches(1.5)

        nickname = self.nickNameEntry.getText()
        if len(studentName) > 0 and len(nickname) > 0:
            self.data.userName = os.getlogin()
            self.data.studentName = studentName
            self.data.nickname = nickname
            self.processClosing()
            
    def processClosing(self):
        self.entryCanvas.undraw()
        self.canvas.update()
        self.entryCanvas = None
        self.data.removeResource("studentInfo")
        self.nextFunction()
                
    def processQuit(self, *args):
        self.canvas.root.quit()
        
    def defaultReturn(self, *args):
        return