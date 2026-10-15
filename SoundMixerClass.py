# Game support classes
__version__ = '8.0'
import os, random
from MultitaskingClasses import ThreadClass
import pygame

#Music and sound effects
class SoundMixerClass:
    """Class to handle music and sound effects based on pygame.mixer,  Major function calls are:
        chooseTheme() - Choose a theme, by default the first theme is loaded and ready, but music and sounds must be specifically started
        playContinuousMusic(self, name=None, volume=None) - Repeat music, commonly used for background music
        playMusic(self, name=None, volume=None, loops=1) - Specific music generally played once, not repeated unless loops is set to -1
        playSound(self, name, *args, volume=None, loops=0, **kwargs) - Play a specific sound, generally once but can be looped
        scheduleRandomSound(self, sound) - Schedule with timing control. The sound must have been defined as a random sound
        quit() - End using sound.
    
    There are many specific pygame commands that can be used to control the music and sound effects.
    Thses calls should be replaced with calls to a more simple sound/music library.
    """
    
    def _extractParameter( text ):
        """ Extract the parameter from a string like "gold(100)" or message(Hello there) and 
        return the tuple parameter as the lower case text and either an integer or text.   
        If no text return no and if no parameter is found, return None for it."""
        if text is None: return None,None
        leftParen = text.find("(")
        if leftParen < 0: return text,None
        rightParen = text.find(")")
        if rightParen < 0: return text,None
        parameter = text[leftParen+1:rightParen]
        usefulText = text[:leftParen]
        if len(parameter) == 0: return usefulText,None
        if not parameter.isdigit(): return usefulText,parameter
        try:
            number = int(parameter)
            return usefulText, number
        except ValueError:
            return usefulText,parameter
    _extractParameter = staticmethod(_extractParameter)

    def __init__(self, data, **kwargs):
        pygame.mixer.pre_init()
        pygame.mixer.init(channels=20)
        
        self.data = data.setResource('soundMixer', self)
        quiz = data.getResource('quiz') # If None, we have bigger problems!

        self.soundChannels = dict() # Dictionary of currently playing (name:channel)
        self.standardVolume = 5
        self.themes = {}
        self.music = {}
        self.sounds = {}
        self.currentMusicName = kwargs.get("music", None)
        self.currentThemeName = kwargs.get("theme", quiz["Theme"])
        self.lastThemeName = None
        self.continuousMusicThread = None
        self.continuousSoundThread = None
        self.playingSoundThread = None

        self.musicSource = quiz.get("Music Path", None)
        self.soundSource = quiz.get("Sounds Path", None)

        self.musicFiles = []
        self.soundFiles = []
        self.musicChannels = []
        
        
        if self.musicSource is not None and self.soundSource is not None:
            if data.music is not None and len(data.music) > 0: self.initializeMusic(data.music, self.musicSource)
            if data.sounds is not None and len(data.sounds) > 0: self.initializeSounds(data.sounds, self.soundSource)
            if data.soundtracks is not None and len(data.soundtracks) > 0: self.initializeSoundtracks(data.soundtracks)
            self.setupPygame()
        else:
            pass # Error, source folder not found
        self.chooseTheme(self.currentThemeName) # Choose the first theme, usually only one
        self.playContinuousMusic(self.currentMusicName) # Start the music playing   

    ###############  Soundracks containing Themes  ####################
    def initializeSoundtracks(self, soundtrackList):
        """The Sountrack list contains multiple themes in dictionary form, each with its own music and sounds
        Save a copy of each theme and then seup to load up all sounds and music for the theme in use."""
        for theme in soundtrackList:
            themeName = theme["Theme"]
            self.themes[themeName] = theme # Save the whole theme (for now)

            musicCSV = theme.get("Music", None) # csv of fileName(name)
            if musicCSV is not None:
                musicList = musicCSV.split(",")
                for musicPair in musicList:
                    name,musicName = self._extractParameter(musicPair)
                    existingResource = self.music.get(musicName, None)
                    if existingResource is None:
                        self.addMusic(self.musicSource, name, musicName)
                    else:
                        self.music[name] = existingResource

            soundCSV = theme.get("Sounds", None)
            if soundCSV is not None:
                soundList = soundCSV.split(",")
                for soundPair in soundList:
                    soundName,name = self._extractParameter(soundPair)
                    existingResource = self.sounds.get(soundName, None)
                    if existingResource is None:
                        self.addSound(self.soundSource, name=name, filename=soundName)
                    else:
                        self.sounds[name] = existingResource

            soundCSV = theme.get("Random", None) # Optional
            if soundCSV is not None:
                soundList = soundCSV.split(",")
                for soundPair in soundList:
                    soundName,randomList = self._extractParameter(soundPair)
                    try:
                        first, last = map(int, randomList.split("-"))
                    except:
                        self.data.logError(f"SoundMixerClass.initializeSoundtracks: Invalid random range for sound >>{soundName}<<.")
                    else:
                        randomList = [first, last] # File name is also the name for random sounds
                        self.addSound(self.soundSource, name=soundName, filename=soundName, randomList=randomList)

    ###############  Themes  ####################
    def chooseTheme(self, themeName='Default'):
        """Choose a specific theme for the sound mixer."""
        if themeName is None:
            self.currentThemeName = None
            self.removeAllSounds()
            self.removeAllMusic()

        elif themeName == 'Default': # This is the first theme, everything is already loaded
            themeName = None
            for firstName in self.themes:
                themeName = firstName
                break

        elif themeName in self.themes and themeName != self.currentThemeName:
            self.removeAllSounds()
            self.removeAllMusic()
            self.currentThemeName = themeName
            newTheme = self.themes[themeName]
            self.loadMusicFiles( **newTheme.music)
            self.loadSounds( **newTheme.sounds )

    ###############  Sounds  ####################
    def initializeSounds(self, soundList, sourceFolder):
        for sound in soundList:
            randomList = sound.get("Random", [])
            name = sound.get('Name', None)
            filename = sound.get('Resource', None)
            if name is not None and filename is not None:
                self.addSound(sourceFolder, name=name, filename=filename, randomList=randomList)

    def addSound(self, sourceFolder, name=None, filename=None, randomList=[]):
        """Add a sound to the sound mixer."""
        extensions = ['mp3', 'ogg', 'wav', 'aiff', 'mp4']
        if name is not None and filename is not None:
            extensionFound = filename.find(".") >= 0
            if not extensionFound:
                for extension in extensions:
                    filename += "." + extension
                    filepath = os.path.join(sourceFolder, filename)
                    extensionFound = os.path.exists(filepath)
                    if extensionFound: break
            if extensionFound:
                self.sounds[name] = {'path':filepath, 'randomList':randomList}
            else:
                pass
                #raise Exception(f"Sound file not found: {filepath}")

    def scheduleRandomSound(self, sound):
        randomly = sound.get("Random", None)
        if randomly is not None and len(randomly) == 2:
            number = random.randint(randomly[0], randomly[1])
            name = sound["Name"]
            function = [self.playSound,self.data.control.reschedule]
            self.data.control.add(name, number, -1, function, name, randomly[0], randomly[1])

    ###############  Music  ####################
    def initializeMusic(self, musicList, sourceFolder):
        for music in musicList:
            name = music.get('Name', None)
            filename = music.get('Resource', None)
            if name is not None and filename is not None:
                self.addMusic(sourceFolder, name=name, filename=filename)

    def addMusic(self, sourceFolder, name=None, filename=None):
        extensions = ['mp3', 'ogg', 'wav', 'aiff', 'mp4']
        filepath = ""
        if name is not None and filename is not None:
            extensionFound = filename.find(".") >= 0
            if not extensionFound:
                for extension in extensions:
                    tryFileName = filename + "." + extension
                    filepath = os.path.join(sourceFolder, tryFileName)
                    extensionFound = os.path.exists(filepath)
                    if extensionFound: break
            if extensionFound:
                self.music[name] = {'path':filepath}
            else:
                pass
                #raise Exception(f"Sound file not found: {filepath}")

    ###############  pygame controls  ####################
    def setupPygame(self):
        """Setup pygame for sound and music."""
        self.loadSounds(**self.sounds)
        self.loadMusicFiles(**self.music)

    def quit(self, *args, **kwargs):
        self.stopMusic()
        self.stopSound()
        pygame.quit()

    def checkIfMixerIsReady(self):
        result =  pygame.mixer.get_init() 
        return result is not None 
    
    def isMixerBusyMixing(self):
        return pygame.mixer.get_busy()
    
    def stopAllSounds(self, *args, **kwargs):
        pygame.mixer.stop()

    def pauseAllSounds(self, *args, **kwargs):
        pygame.mixer.pause()
    def mute(self, *args, **kwargs):
        pygame.mixer.pause()

    def unmute(self, *args, **kwargs):
        pygame.mixer.pause()
    def unpauseAllSounds(self, *args, **kwargs):
        pygame.mixer.pause()

    def fadeAllSounds(self, *args, time=1000, **kwargs):
        pygame.mixer.fadeout(time)

    def setStandardVolume(self, volume):
        if volume in [0,1,2,3,4,5,6,7,8,9,10]:
            number = volume / 10
            self.standardVolume = number
            pygame.mixer.music.set_volume(number)
        else:
            raise Exception("Volume must be between 0 and 10")
    
    ###############  pygame Music  ####################
    def stopMusic(self, *args, **kwargs):
        if self.continuousMusicThread is not None:
            if self.continuousMusicThread.is_alive():
                self.continuousMusicThread.stop()
            self.continuousMusicThread = None
        pygame.mixer.music.stop()

    # Needs to be in a thread
    def playMusic(self, *args, name=None, volume=None, loops=1, **kwargs):
        if name is None:
            if self.currentMusic is None:
                if len(self.music) > 0:
                    name = list(self.music.keys())[0]
                    pygame.mixer.music.load(self.music[name])
                    self.currentMusic = name
                else:
                    raise Exception("No music file loaded")
        else:
            musicFileDictionary = self.music[name]
            path = musicFileDictionary["path"]
            pygame.mixer.music.load(path)
            self.currentMusic = name
        if volume in [0,1,2,3,4,5,6,7,8,9,10]:
            number = volume / 10
            pygame.mixer.music.set_volume(number)
        elif self.standardVolume is not None:
            pygame.mixer.music.set_volume(self.standardVolume)
        pygame.mixer.music.play(loops)

    def playContinuousMusic(self, newMusic, *args, volume=3, loops=0, **kwargs):
        if newMusic is not None and newMusic != self.currentMusicName:
            if newMusic in self.music:
                self.fadeOutMusic(500)
                self.stopMusic()
                self.currentMusicName = newMusic
                pygame.mixer.music.load(self.music[newMusic])
                self.continuousMusicThread = ThreadClass(self.playContinuousThreadedMusic, newMusic, volume)
       
    def playContinuousThreadedMusic(self, name, volume):
        pygame.mixer.music.load(self.music[name])
        if volume in [0,1,2,3,4,5,6,7,8,9,10]:
            number = volume / 10
            pygame.mixer.music.set_volume(number)        
        elif self.standardVolume is not None:
            pygame.mixer.music.set_volume(self.standardVolume)
        pygame.mixer.music.play(-1)

    def pauseMusic(self, *args, **kwargs):
        pygame.mixer.music.pause()

    def unpauseMusic(self, *args, **kwargs):
        pygame.mixer.music.unpause()

    def setMusicVolume_0to10(self, volume):
        if volume in[0,1,2,3,4,5,6,7,8,9,10]:
            number = volume / 10
            pygame.mixer.music.set_volume(number)
        else:
            raise Exception("Volume must be between 0 and 10")

    def getMusicVolume(self):
        number = pygame.mixer.music.get_volume()
        return int(number * 10)
    
    def fadeOutMusic(self, *args, time=500, **kwargs):
        pygame.mixer.music.fadeout(time)

    def fadeInMusic(self, *args, time=500, **kwargs):
        pygame.mixer.music.fadein(time)

    #################### pygame Channels ####################
    def getUnusedChannel(self): # After 8, recycle least used channel
        channel = pygame.mixer.find_channel()
        for key,value in self.soundChannels.items():
            if value == channel:
                sound = self.sounds[key]
                sound.stop()
                sound = None
                self.sounds.delete(key)
                self.soundChannels.delete(key)
        return channel

    def isChannelBusy(self, channel):
        return channel.get_busy()
    
    def playChannel(self, channel=None, name=None, volume=None, loops=0, maxtime=0, fade_ms=0):
        useChannel = self.soundChannels[name] if channel is None else channel
        if name is not None or useChannel is None:
            sound = self.sounds[name]
            if useChannel is None:
                useChannel = self.getUnusedChannel()
                self.soundChannels[name] = useChannel
                sound = self.sounds[name]
        if volume in[0,1,2,3,4,5,6,7,8,9,10]:
            number = volume / 10
            useChannel.set_volume(number)
        elif self.standardVolume is not None:
            pygame.mixer.music.set_volume(self.standardVolume)
        useChannel.play(sound, loops=loops, maxtime=maxtime, fade_ms=fade_ms)

    def stopChannel(self, channel):
        channel.stop()

    def pauseChannel(self, channel):
        channel.pause()

    def unpauseChannel(self, channel):
        channel.unpause()

    def fadeOutChannel(self, channel, time=500):
        channel.fadeout(time)

    def fadeInChannel(self, channel, time=500):
        channel.fadein(time)

    def getChannelVolume_0to10(self, channel):
        number = channel.get_volume()
        return int(number * 10)

    def setChannelVolume_0to10(self, channel, volume):
        if volume in [0,1,2,3,4,5,6,7,8,9,10]:
            number = volume / 10
            channel.set_volume(number)
        else:
            raise Exception("Volume must be between 0 and 10")

    def getSoundAtChannel(self, channel):
        return channel.get_sound()

    def queueSoundAtChannel(self, channel, sound):
        channel.queue(sound)

    def getQueuedSoundsAtChannel(self, channel):
        return channel.get_queue()

    #################### pygame Sounds ####################
    def loadSound(self, name, file):
        try:
            sound = pygame.mixer.Sound(file)
            self.sounds[name] = sound

        except:
            self.data.logError("SoundMixerClass.loadSound: Sound file not found >>" + file + "<<.")


    # def removeSound(self, name):
    #     if name in self.sounds:
    #         sound = self.sounds[name]
    #         sound.stop()
    #         sound = None

    def removeAllSounds(self):
        # for name in self.sounds:
        #     self.removeSound(name)
        self.sounds.clear()
        self.soundChannels.clear()
        
    def playSound(self, name, *args, volume=3, loops=0, **kwargs):

        # make a thread and run the playThreadSound method
        nameCheck = self.sounds.get(name, None)
        if nameCheck is None:
            print(f"playSound() error: Sound not found >>{name}<<")
            pass
        else: # self.playingSoundThread is None:
            if type(nameCheck) == dict: # Convert file name in dictionary to a new channel
                self.loadSound(name, nameCheck['path'])
            self.playingSoundThread = ThreadClass(self.playThreadSound, name, volume, loops)

    def playThreadSound(self, name, volume, loops):
        if name in self.soundChannels:
            channel = self.soundChannels[name]
            if volume in [0,1,2,3,4,5,6,7,8,9,10]:
                number = volume / 10
                channel.set_volume(number)
            elif self.standardVolume is not None:
                pygame.mixer.music.set_volume(self.standardVolume)
            channel.play(self.sounds[name], loops)
        elif name in self.sounds:
            channel = self.getUnusedChannel()
            self.soundChannels[name] = channel
            if volume in [0,1,2,3,4,5,6,7,8,9,10]:
                number = volume / 10
                channel.set_volume(number)
            elif self.standardVolume is not None:
                pygame.mixer.music.set_volume(self.standardVolume)
            channel.play(self.sounds[name], loops)
            pass
        else:
            raise Exception("Sound file not found: " + name)
  
    def stopSound(self, name, *args, **kwargs):
        if name in self.soundChannels:
            if self.playingSoundThread is not None:
                self.playingSoundThread.stop() # Only works on the last sound
                self.playingSoundThread = None
            channel = self.soundChannels[name]
            channel.stop()

    def pauseSound(self, name, *args, **kwargs):
        if name in self.soundChannels:
            channel = self.soundChannels[name]
            channel.pause()

    def unpauseSound(self, name, *args, **kwargs):
        if name in self.soundChannels:
            channel = self.soundChannels[name]
            channel.unpause()

    def fadeOutSound(self, name, *args, time=500, **kwargs):
        if name in self.soundChannels:
            channel = self.soundChannels[name]
            channel.fadeout(time)

    def fadeInSound(self, name, *args, time=500, **kwargs):
        if name in self.soundChannels:
            channel = self.soundChannels[name]
            channel.fadein(time)

    def setSoundVolume_0to10(self, name, volume, *args, **kwargs):
        if name in self.soundChannels:
            channel = self.soundChannels[name]
            if volume in [0,1,2,3,4,5,6,7,8,9,10]:
                number = volume / 10
                channel.set_volume(number)
        else:
            raise Exception("Sound not found: " + name)        

    def getSoundVolume_0to10(self, name):
        if name in self.soundChannels:
            channel = self.soundChannels[name]
            number = channel.get_volume()
            return int(number * 10)
        
    # save a dictionary of up to 8 sounds
    def loadSounds(self, **wargs):
        count = 0
        for key,nameDictionary in wargs.items():
            self.loadSound(key, nameDictionary['path'])
            channel = self.getUnusedChannel()
            self.soundChannels[key] = channel
            count += 1
            if count >= 8: break

    def saveMusicFile(self, name, file):
        self.musicFiles[name] = file

    def removeMusicFile(self, name):
        if name in self.musicFiles:
            del self.musicFiles.delete[name]
        if self.currentMusicName == name:
            self.stopMusic()
            self.currentMusicName = None

    def removeAllMusic(self):
        for name in self.musicFiles:
            self.removeMusicFile(name)
        self.musicFiles.clear()
        self.musicChannels.clear()

    def loadMusic(self, name, file):
        self.music[name] = file
        if self.currentMusicName is None:
            pygame.mixer.music.load(self.music[name])

    def loadMusicFiles(self, **wargs):
        for key,nameDictionary in wargs.items():
            self.loadMusic(key, nameDictionary['path'])