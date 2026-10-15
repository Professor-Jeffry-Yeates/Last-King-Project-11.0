# Color
from random import *
__version__ = "8.0"   
"""Color library has premade colors using color commom names.
self.From_rgb() returns a color in RGB format.
Get_rgb() returns a tuple of (r,g,b) from a color.
Blend() blends a list of colors and returns the resulting color.
Standard color names are defined individually in a dictionary."""
class ColorClass:
    def __init__(self):
        """Initialize the Color class with a dictionary of colors."""
        self.ColorDictionary = dict(
            White = self.From_rgb(255,255,255),
            Mist = self.From_rgb(239,239,239),
            Haze = self.From_rgb(223,223,223),
            LightGray = self.From_rgb(190,190,190),
            Gray = self.From_rgb(127,127,127),
            DarkGray = self.From_rgb(64,64,64),
            Black = self.From_rgb(0,0,0),
            Lime = self.From_rgb(164, 196, 0),
            Green = self.From_rgb(96, 169, 23),
            DarkGreen = self.From_rgb(0, 64, 0),
            DeepGreen = self.From_rgb(0, 127, 0),
            MediumGreen = self.From_rgb(0, 190, 0),
            LightGreen = self.From_rgb(200, 255, 200),
            FullGreen = self.From_rgb(0, 255, 0),
            Emerald = self.From_rgb(0, 138, 0),
            Teal = self.From_rgb(0, 171, 169),
            Cyan = self.From_rgb(27, 161, 226),
            Blue = self.From_rgb(0, 0, 127),
            DarkBlue = self.From_rgb(0, 0, 64),
            DeepBlue = self.From_rgb(0, 0, 127),
            MediumBlue = self.From_rgb(0, 0, 190),
            FullBlue = self.From_rgb(0, 0, 255),
            LightBlue = self.From_rgb(200, 200, 255),
            Cobalt = self.From_rgb (0, 80, 239),
            Indigo = self.From_rgb(106, 0, 255),
            Violet = self.From_rgb(170, 0, 255),
            Purple = self.From_rgb(127,127,0),
            DarkPurple = self.From_rgb(64,64,0),
            DeepPurple = self.From_rgb(127,127,0),
            MediumPurple = self.From_rgb(190,190,0),
            FullPurple = self.From_rgb(255,255,0),
            LightPurple = self.From_rgb(255,255,200),
            Pink = self.From_rgb(244, 114, 208),
            Magenta = self.From_rgb(216, 0, 115),
            Crimson = self.From_rgb(162, 0, 37),
            Red = self.From_rgb(229, 20, 0),
            FiveGuysRed = self.From_rgb(193, 48, 57),
            DarkRed = self.From_rgb(64, 0, 0),
            DeepRed = self.From_rgb(127, 0, 0),
            MediumRed = self.From_rgb(190, 0, 0),
            FullRed = self.From_rgb(255, 0, 0),
            LightRed = self.From_rgb(255, 200, 200),
            Orange = self.From_rgb(250, 104, 0),
            Amber = self.From_rgb(240, 163, 10),
            Yellow = self.From_rgb(227, 200, 0),
            DarkYellow = self.From_rgb(64, 64, 0),
            DeepYellow = self.From_rgb(127, 127, 0),
            MediumYellow = self.From_rgb(190, 190, 0),
            FullYellow = self.From_rgb(255, 255, 0),
            LightYellow = self.From_rgb(255, 255, 200),
            Brown = self.From_rgb(130, 90, 44),
            DarkBrown = self.From_rgb(65, 45, 22),
            MediumBrown = self.From_rgb(195, 135, 66),
            LightBrown = self.From_rgb(255, 180, 90),
            Olive = self.From_rgb(109, 135, 100),
            Steel = self.From_rgb(100, 118, 135),
            Mauve = self.From_rgb(118, 96, 138),
            Taupe = self.From_rgb(135, 121, 78),
            Gold = self.From_rgb(255, 215, 0),
            Silver = self.From_rgb(192, 192, 192),
            Copper = self.From_rgb(184, 115, 51),
            Bronze = self.From_rgb(205, 127, 50) )

    def __call__(self, key, value=None):
        if value is None:
            if key in self.ColorDictionary:
                return self.ColorDictionary[key]
        else:
            self.ColorDictionary[key] = value
        return None

    def __len__(self):
        return len(self.ColorDictionary)

    def __getitem__(self, key):
        if key in self.ColorDictionary:
            return self.ColorDictionary[key]
        else:
            return None

    def __setitem__(self, key, value):
        self.ColorDictionary[key] = value
        return None

    def __delitem__(self, key):
        if key in self.ColorDictionary:
            del self.ColorDictionary[key]
        return None

    def get(self, key, defaultValue):
        if key is None: return ""
        if key == "": return "" # Will remove color
        if key[0] == "#": return key
        if key in self.ColorDictionary:
            return self.ColorDictionary[key]
        else:
            return defaultValue    
        
    def From_rgb(self,  *args):
        """r,g,b are intensities of red, green, and blue in range(256)
        Returns Tkinter color specifier string for the resulting color"""
        r = args[0]
        g = args[1]
        b = args[2]
        if len(args) == 4:
            o = args[3]
            return "#%02x%02x%02x%02x" % (r,g,b,o)
        else:
            return "#%02x%02x%02x" % (r,g,b)

    def Get_rgb(self, color):
        """color is a Tkinter color specifier string, returns a tuple of (r,g,b)"""
        r,g,b = 0,0,0
        if isinstance(color, str):
            try:
                r = int(color[1:3],16)
                g = int(color[3:5],16)
                b = int(color[5:7],16)
            except:
                pass
            if len(color) == 9:
                o = int(color[7:9],16)
                return (r,g,b,o)
        return (r,g,b)
    
    def Blend(self, *list, opacity=False):
        """Blend a list of colors.  Returns the resulting color.
        The list is either colors #xxxxxxxxx or a color name -or-
        a list of colors (as above) followed by a percentage (1-100 or .01-1.0) of the color to use.
        The final color's percentage is optional (to be computed if missing).
        If opacity is True, the color will be returned with an opacity value."""
        length = len(list)
        if length == 0:
            color = None
        elif length == 1:
            color = list[0]

        # if only color names are used to blend together
        elif type(list[1]) == str:
            count = 0
            total_r = 0
            total_g = 0
            total_b = 0
            total_o = 0
            for color in list:
                if color is not None:
                    if color[0] != "#":
                        color = self.ColorDictionary[color]
                    colors = self.Get_rgb(color)
                    r = colors[0]
                    g = colors[1]
                    b = colors[2]
                    if len(colors) == 4:
                        o = colors[3]
                        total_o += o
                    total_r += r
                    total_g += g
                    total_b += b
                    count += 1
            if count == 0:
                color = self.From_rgb(0,0,0)
            else:
                total_r //= count
                total_g //= count
                total_b //= count
                total_o //= count
                if opacity:
                    color = self.From_rgb(int(total_r),int(total_g),int(total_b),int(total_o))
                else:
                    color = self.From_rgb(int(total_r),int(total_g),int(total_b))

        # Otherwise each color is followed by a percentage with the final color's percentage 
        # being optional (to be computed if missing). The percentage is (1-100 or .01-1.0) but
        # converted to (.01 - 1.0) for the calculation.
        else:
            count = 0
            percentSumation = 0.0
            total_r = 0
            total_g = 0
            total_b = 0
            total_o = 0
            while count < length:
                color = list[count]
                count += 1
                if count >= length:
                    percent = 1.0 - percentSumation if percentSumation < 1.0 else 0
                else:
                    percent = list[count]
                    if percent >= 1: percent /= 100.0
                    percentSumation += percent
                count += 1

                if color is not None:
                    if color[0] != "#":
                        color = self.ColorDictionary[color]
                    colors = self.Get_rgb(color)
                    r = colors[0]
                    g = colors[1]
                    b = colors[2]
                    if len(colors) == 4:
                        o = colors[3]
                        total_o += o * percent
                    total_r += r * percent
                    total_g += g * percent
                    total_b += b * percent
            if opacity:
                color = self.From_rgb(int(total_r),int(total_g),int(total_b),int(total_o))
            else:
                color = self.From_rgb(int(total_r),int(total_g),int(total_b))

        return color

    def ComplementColor(self, color, default):
        if color is None or color == '':
            hexColor = self.get(default,'Black')
            return hexColor
        else:
            hexColor = self.get(color,'Black')
            rgb = self.Get_rgb(hexColor)
            color = self.From_rgb(255 - rgb[0], 255 - rgb[1], 255 - rgb[2])
            if len(rgb) == 4:
                o = rgb[3]
                return self.From_rgb(255 - rgb[0], 255 - rgb[1], 255 - rgb[2], o)
            else:
                return self.From_rgb(255 - rgb[0], 255 - rgb[1], 255 - rgb[2])
            
    def RandomColor(self):
        """Return a random color from the ColorDictionary."""
        keys = list(self.ColorDictionary.keys())
        length = len(keys) - 1
        number =randint(0,length)
        key = keys[number]
        value = self.ColorDictionary[key]
        return value