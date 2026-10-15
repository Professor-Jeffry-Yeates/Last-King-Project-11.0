__version__ = "8.0"
class LayoutSizingClass():
    """This class defines the layout sizes and positions for the various components of the dungeon GUI.
    The sizes can be defined relative to the overall canvas size, allowing for easy adjustments.
    """
    
    def __init__(self, width, height):
        
        # Constants for relative adjustments
        CENTER_WIDTH=int(width/2);CENTER_HEIGHT=int(height/2)
        TOP_ROW=60;BOTTOM_ROW=615;BOTTOM_HEIGHT=max(height-640,150)
        BADGE_LEFT = max(width-470,420)
        QUESTION_WIDTH = max(width-460,420)
        INSTRUCTION_WIDTH = max(width-270,420)
        
        self.size = {} # Stores x,y, and then width,height
        self.size["title"] = [CENTER_WIDTH,30]
        self.size["miniMap"] =      [10,  TOP_ROW, 100,100]
        self.size["rewardBox"] =    [120, TOP_ROW, 290, 130] # This should adjust based on the size of the minimap
        self.size["badges"] =       [BADGE_LEFT, TOP_ROW, 440, 100]
        self.size["playersMap"] =   [10, 200, 400, 400]
        self.size["questionArea"] = [420, 140, QUESTION_WIDTH, 450] # +1600 width, +800 height,  extras
        self.size["statusBar"] =    [10, BOTTOM_ROW, 225, BOTTOM_HEIGHT ]
        self.size["instructions"] = [245, BOTTOM_ROW, INSTRUCTION_WIDTH, BOTTOM_HEIGHT]
        
        self.size["scenarioMap"] =[10, 200, 1000, 640] #width-200, 640]
        self.size["scenarioInstructions"] =[415, 50, width-440, 150]
        self.size["scenarioBlank"] = [10, 200, width-10, height-200]
        self.size["miniCompass"] =[0,0,100,100]
        self.size['debugging'] = [10, 750, 500, 1240]
        
        self.size["enterStudent"] = [CENTER_WIDTH-200,CENTER_HEIGHT-100, 400, 200]
    
    # Access as a function call or dictionary reference
    def __getitem__(self, key ):
        return self.size.get(key, [0,0,0,0])
        
    def __call__(self, key ):
        return self.size.get(key, [0,0,0,0])