# Game support classes
__version__ = '11.0'
#import os, random, threading, time
#import numpy as np
#import miniaudio            # pip install miniaudio numpy
#
#
##################### Decoded audio held in memory ####################
#class _Source:
#    """A fully decoded file: int16 frames shaped (numFrames, 2) at the mixer's sample rate."""
#    def __init__(self, path, frames, sampleRate):
#        self.path = path
#        self.frames = frames
#        self.duration = len(frames) / sampleRate
#
#
##################### Internal channel (replaces pygame.mixer.Channel) ####################
#class _Channel:
#    """One voice in the software mixer. All timing (loops, fades, maxtime, queue) is counted
#    in audio frames inside the audio callback, so no timer thread is needed.
#    Every method is called with the mixer lock held."""
#
#    def __init__(self, mixer, index):
#        self.mixer = mixer
#        self.index = index
#        self.loaded = None        # last _Source loaded (kept after stop for fadein/replay)
#        self.source = None        # _Source currently playing, None when idle
#        self.name = None
#        self.pos = 0
#        self.paused = False
#        self.volume = 1.0         # 0.0 - 1.0
#        self.loops = 0
#        self.loopsRemaining = 0
#        self.framesLeft = None    # maxtime countdown in frames
#        self.queue = []
#        self.lastStarted = 0.0
#        self._resetFade()
#
#    def _resetFade(self):
#        self.fadeGain = 1.0
#        self.fadeTarget = 1.0
#        self.fadeStep = 0.0
#        self.fadeFramesLeft = 0
#        self.stopWhenFaded = False
#
#    def _startFade(self, target, ms, stopWhenDone):
#        frames = max(1, int(ms * self.mixer.sampleRate / 1000))
#        self.fadeTarget = target
#        self.fadeStep = (target - self.fadeGain) / frames
#        self.fadeFramesLeft = frames
#        self.stopWhenFaded = stopWhenDone
#
#    # ---- pygame.mixer.Channel-like API ----
#    def load(self, source, name=None):
#        self.loaded = source
#        self.name = name
#
#    def play(self, source=None, name=None, loops=0, maxtime=0, fade_ms=0, keepQueue=False):
#        """loops follows pygame: 0 = play once, N = play N extra times, -1 = forever."""
#        if source is not None:
#            self.load(source, name)
#        if self.loaded is None:
#            return
#        self.source = self.loaded
#        self.pos = 0
#        self.paused = False
#        self.loops = loops
#        self.loopsRemaining = loops if loops > 0 else 0
#        self.framesLeft = int(maxtime * self.mixer.sampleRate / 1000) if maxtime and maxtime > 0 else None
#        if not keepQueue:
#            self.queue.clear()
#        self._resetFade()
#        if fade_ms and fade_ms > 0:
#            self.fadeGain = 0.0
#            self._startFade(1.0, fade_ms, False)
#        self.lastStarted = time.monotonic()
#
#    def stop(self):
#        self.source = None
#        self.pos = 0
#        self.paused = False
#        self.loopsRemaining = 0
#        self.framesLeft = None
#        self.queue.clear()
#        self._resetFade()
#
#    def pause(self):
#        if self.source is not None:
#            self.paused = True
#
#    def unpause(self):
#        self.paused = False
#
#    def fadeout(self, ms=500):
#        if self.source is None or self.paused:
#            self.stop()
#        else:
#            self._startFade(0.0, ms, True)
#
#    def fadein(self, ms=500):
#        if self.source is None:
#            if self.loaded is not None:
#                self.play(loops=self.loops, fade_ms=ms)
#            return
#        if self.paused:
#            self.fadeGain = 0.0
#            self.paused = False
#        self._startFade(1.0, ms, False)
#
#    def get_busy(self):
#        return self.source is not None
#
#    def set_volume(self, value):
#        self.volume = max(0.0, min(1.0, float(value)))
#
#    def get_volume(self):
#        return self.volume
#
#    def get_sound(self):
#        return self.name
#
#    def queue_sound(self, source, name=None):
#        if self.source is None:
#            self.play(source, name)
#        else:
#            self.queue.append((source, name))
#
#    def get_queue(self):
#        return [name if name is not None else source.path for source, name in self.queue]
#
#    def release(self):
#        self.stop()
#        self.loaded = None
#        self.name = None
#
#    # ---- called from the audio callback ----
#    def mix(self, out, n):
#        """Add this channel's next n frames into out (float32, shape (n, 2))."""
#        if self.source is None or self.paused:
#            return
#        written = 0
#        while written < n and self.source is not None:
#            data = self.source.frames
#            total = len(data)
#            if total == 0:
#                self.stop()
#                break
#            take = min(n - written, total - self.pos)
#            if self.framesLeft is not None:
#                take = min(take, self.framesLeft)
#            if self.stopWhenFaded and self.fadeFramesLeft > 0:
#                take = min(take, self.fadeFramesLeft)
#            if take > 0:
#                chunk = data[self.pos:self.pos + take].astype(np.float32)
#                scale = self.volume / 32768.0
#                if self.fadeFramesLeft > 0:
#                    k = min(take, self.fadeFramesLeft)
#                    ramp = np.full(take, self.fadeTarget, dtype=np.float32)
#                    ramp[:k] = self.fadeGain + self.fadeStep * np.arange(1, k + 1, dtype=np.float32)
#                    np.clip(ramp, 0.0, 1.0, out=ramp)
#                    self.fadeFramesLeft -= k
#                    self.fadeGain = self.fadeTarget if self.fadeFramesLeft == 0 else float(ramp[k - 1])
#                    chunk *= (ramp * scale)[:, None]
#                else:
#                    chunk *= self.fadeGain * scale
#                out[written:written + take] += chunk
#                self.pos += take
#                written += take
#                if self.framesLeft is not None:
#                    self.framesLeft -= take
#            if self.stopWhenFaded and self.fadeFramesLeft == 0:
#                self.stop()
#                break
#            if self.framesLeft is not None and self.framesLeft <= 0:
#                self.stop()
#                break
#            if self.pos >= total:
#                if self.loops == -1 or self.loopsRemaining > 0:
#                    if self.loops != -1:
#                        self.loopsRemaining -= 1
#                    self.pos = 0
#                elif self.queue:
#                    source, name = self.queue.pop(0)
#                    self.play(source, name, keepQueue=True)
#                else:
#                    self.stop()
#                    break
#
#
##################### Music and sound effects ####################
#class SoundMixerClass:
#    """Class to handle music and sound effects based on miniaudio (pyminiaudio). Major function calls are:
#        chooseTheme() - Choose a theme, by default the first theme is loaded and ready, but music and sounds must be specifically started
#        playContinuousMusic(self, name=None, volume=None) - Repeat music, commonly used for background music
#        playMusic(self, name=None, volume=None, loops=0) - Specific music generally played once, not repeated unless loops is set to -1
#        playSound(self, name, *args, volume=None, loops=0, **kwargs) - Play a specific sound, generally once but can be looped
#        scheduleRandomSound(self, sound) - Schedule with timing control. The sound must have been defined as a random sound
#        quit() - End using sound.
#
#    One miniaudio PlaybackDevice is opened. Its callback mixes all channels with numpy.
#    Files are decoded fully into memory (int16 stereo). Music is decoded on a background
#    thread so the GUI is not blocked. Supported formats: WAV, MP3, FLAC, OGG Vorbis.
#    Volumes in the public API are integers 0-10.
#    """
#
#    EXTENSIONS = ['ogg', 'mp3', 'wav', 'flac']
#
#    def _extractParameter(text):
#        """ Extract the parameter from a string like "gold(100)" or message(Hello there) and
#        return the tuple parameter as the lower case text and either an integer or text.
#        If no text return no and if no parameter is found, return None for it."""
#        if text is None: return None, None
#        text = text.strip()
#        leftParen = text.find("(")
#        if leftParen < 0: return text, None
#        rightParen = text.find(")")
#        if rightParen < 0: return text, None
#        parameter = text[leftParen+1:rightParen].strip()
#        usefulText = text[:leftParen].strip()
#        if len(parameter) == 0: return usefulText, None
#        if not parameter.isdigit(): return usefulText, parameter
#        try:
#            return usefulText, int(parameter)
#        except ValueError:
#            return usefulText, parameter
#    _extractParameter = staticmethod(_extractParameter)
#
#    def __init__(self, data, **kwargs):
#        self._lock = threading.RLock()
#        self.sampleRate = kwargs.get("sampleRate", 44100)
#        self.maxChannels = kwargs.get("channels", 20)
#        self._channels = []                 # sound-effect channels (created on demand)
#        self.musicChannel = _Channel(self, -1)
#        self.masterGain = 1.0
#        self._savedMasterGain = 1.0
#        self._muted = False
#        self._soundCache = {}               # path -> _Source
#        self._musicCache = (None, None)     # (path, _Source) of the last music decoded
#        self._musicToken = 0
#        self._musicPending = False
#        self._callbackErrorLogged = False
#
#        self.data = data.setResource('soundMixer', self)
#        quiz = data.getResource('quiz')  # If None, we have bigger problems!
#
#        self.soundChannels = dict()  # Dictionary of sound name -> _Channel
#        self.standardVolume = 5      # 0-10
#        self.themes = {}
#        self.music = {}              # name -> {'path': ...}
#        self.sounds = {}             # name -> {'path': ..., 'randomList': [...]}
#        self.currentMusicName = None
#        self.currentThemeName = kwargs.get("theme", quiz.get("Theme", 'Default'))
#
#        self.musicSource = quiz.get("Music Path", None)
#        self.soundSource = quiz.get("Sounds Path", None)
#
#        self.device = None
#        self._openDevice(kwargs.get("bufferMsec", 60))
#
#        if self.musicSource is not None and self.soundSource is not None:
#            if data.music is not None and len(data.music) > 0: self.initializeMusic(data.music, self.musicSource)
#            if data.sounds is not None and len(data.sounds) > 0: self.initializeSounds(data.sounds, self.soundSource)
#            if data.soundtracks is not None and len(data.soundtracks) > 0: self.initializeSoundtracks(data.soundtracks)
#            self.setupMixer()
#        else:
#            self._log("SoundMixerClass.__init__: 'Music Path' or 'Sounds Path' not set in quiz.")
#        self.chooseTheme(self.currentThemeName)              # Choose the first theme, usually only one
#        self.playContinuousMusic(kwargs.get("music", None))  # Start the music playing (if requested)
#
#    ###############  Audio device and mixing  ####################
#    def _openDevice(self, bufferMsec):
#        try:
#            self.device = miniaudio.PlaybackDevice(output_format=miniaudio.SampleFormat.FLOAT32,
#                                                   nchannels=2, sample_rate=self.sampleRate,
#                                                   buffersize_msec=bufferMsec, app_name="SoundMixer")
#            generator = self._generator()
#            next(generator)              # prime the generator, as miniaudio requires
#            self.device.start(generator)
#        except Exception as error:
#            self.device = None
#            self._log(f"SoundMixerClass: cannot open audio device, running silent: {error}")
#
#    def _generator(self):
#        frames = yield b""
#        while True:
#            frames = yield self._mix(frames)
#
#    def _mix(self, n):
#        out = np.zeros((n, 2), dtype=np.float32)
#        try:
#            with self._lock:
#                for channel in self._channels:
#                    if channel.source is not None:
#                        channel.mix(out, n)
#                self.musicChannel.mix(out, n)
#                gain = self.masterGain
#            if gain != 1.0:
#                out *= gain
#            np.clip(out, -1.0, 1.0, out=out)
#        except Exception as error:   # never let an exception kill the audio device
#            if not self._callbackErrorLogged:
#                self._callbackErrorLogged = True
#                self._log(f"SoundMixerClass audio callback error: {error}")
#            out[:] = 0
#        return out
#
#    def _decode(self, path):
#        decoded = miniaudio.decode_file(path, output_format=miniaudio.SampleFormat.SIGNED16,
#                                        nchannels=2, sample_rate=self.sampleRate)
#        frames = np.frombuffer(decoded.samples, dtype=np.int16).reshape(-1, 2)
#        return _Source(path, frames, self.sampleRate)
#
#    def _getSoundSource(self, path):
#        source = self._soundCache.get(path)
#        if source is None:
#            source = self._decode(path)
#            self._soundCache[path] = source
#        return source
#
#    ###############  internal helpers  ####################
#    def _log(self, message):
#        try:
#            self.data.logError(message)
#        except Exception:
#            print(message)
#
#    def _toUnit(self, volume):
#        """0-10 integer -> 0.0-1.0, or None if not a valid volume."""
#        if volume in [0,1,2,3,4,5,6,7,8,9,10]:
#            return volume / 10
#        return None
#
#    def _resolveVolume(self, volume):
#        unit = self._toUnit(volume)
#        return unit if unit is not None else self.standardVolume / 10
#
#    def _firstIntArg(self, args, default):
#        if args and isinstance(args[0], (int, float)):
#            return int(args[0])
#        return default
#
#    def _findFile(self, sourceFolder, filename):
#        """Return a full path to an existing file, trying known extensions when none is given."""
#        if os.path.splitext(filename)[1]:
#            filepath = os.path.join(sourceFolder, filename)
#            return filepath if os.path.exists(filepath) else None
#        for extension in self.EXTENSIONS:
#            filepath = os.path.join(sourceFolder, filename + "." + extension)
#            if os.path.exists(filepath):
#                return filepath
#        return None
#
#    ###############  Soundtracks containing Themes  ####################
#    def initializeSoundtracks(self, soundtrackList):
#        """The Soundtrack list contains multiple themes in dictionary form, each with its own music and sounds.
#        Save a copy of each theme and load the sounds and music it uses."""
#        for theme in soundtrackList:
#            self.themes[theme["Theme"]] = theme
#            self._loadThemeResources(theme)
#
#    def _loadThemeResources(self, theme):
#        # Music: csv of fileName(name)
#        musicCSV = theme.get("Music", None)
#        if musicCSV:
#            for musicPair in musicCSV.split(","):
#                fileName, name = self._extractParameter(musicPair)
#                if name is None: name = fileName
#                existing = self.music.get(fileName, None)
#                if existing is None:
#                    self.addMusic(self.musicSource, name=name, filename=fileName)
#                else:
#                    self.music[name] = existing
#
#        # Sounds: csv of fileName(name)
#        soundCSV = theme.get("Sounds", None)
#        if soundCSV:
#            for soundPair in soundCSV.split(","):
#                fileName, name = self._extractParameter(soundPair)
#                if name is None: name = fileName
#                existing = self.sounds.get(fileName, None)
#                if existing is None:
#                    self.addSound(self.soundSource, name=name, filename=fileName)
#                else:
#                    self.sounds[name] = existing
#
#        # Random: csv of fileName(first-last)   (optional)
#        soundCSV = theme.get("Random", None)
#        if soundCSV:
#            for soundPair in soundCSV.split(","):
#                soundName, randomRange = self._extractParameter(soundPair)
#                try:
#                    first, last = map(int, str(randomRange).split("-"))
#                except (ValueError, AttributeError):
#                    self._log(f"SoundMixerClass.initializeSoundtracks: Invalid random range for sound >>{soundName}<<.")
#                else:  # File name is also the name for random sounds
#                    self.addSound(self.soundSource, name=soundName, filename=soundName, randomList=[first, last])
#
#    ###############  Themes  ####################
#    def chooseTheme(self, themeName='Default'):
#        """Choose a specific theme for the sound mixer."""
#        if themeName is None:
#            self.currentThemeName = None
#            self.removeAllSounds()
#            self.removeAllMusic()
#
#        elif themeName == 'Default':  # The first theme; everything is already loaded
#            self.currentThemeName = next(iter(self.themes), None)
#
#        elif themeName in self.themes and themeName != self.currentThemeName:
#            self.removeAllSounds()
#            self.removeAllMusic()
#            self.currentThemeName = themeName
#            self._loadThemeResources(self.themes[themeName])
#            self.setupMixer()
#
#    ###############  Sounds  ####################
#    def initializeSounds(self, soundList, sourceFolder):
#        for sound in soundList:
#            randomList = sound.get("Random", [])
#            name = sound.get('Name', None)
#            filename = sound.get('Resource', None)
#            if name is not None and filename is not None:
#                self.addSound(sourceFolder, name=name, filename=filename, randomList=randomList)
#
#    def addSound(self, sourceFolder, name=None, filename=None, randomList=None):
#        """Add a sound to the sound mixer."""
#        if name is None or filename is None: return
#        filepath = self._findFile(sourceFolder, filename)
#        if filepath is not None:
#            self.sounds[name] = {'path': filepath, 'randomList': list(randomList or [])}
#        else:
#            self._log(f"SoundMixerClass.addSound: Sound file not found >>{filename}<< in {sourceFolder}.")
#
#    def scheduleRandomSound(self, sound):
#        randomly = sound.get("Random", None)
#        if randomly is not None and len(randomly) == 2:
#            number = random.randint(randomly[0], randomly[1])
#            name = sound["Name"]
#            function = [self.playSound, self.data.control.reschedule]
#            self.data.control.add(name, number, -1, function, name, randomly[0], randomly[1])
#
#    ###############  Music  ####################
#    def initializeMusic(self, musicList, sourceFolder):
#        for music in musicList:
#            name = music.get('Name', None)
#            filename = music.get('Resource', None)
#            if name is not None and filename is not None:
#                self.addMusic(sourceFolder, name=name, filename=filename)
#
#    def addMusic(self, sourceFolder, name=None, filename=None):
#        if name is None or filename is None: return
#        filepath = self._findFile(sourceFolder, filename)
#        if filepath is not None:
#            self.music[name] = {'path': filepath}
#        else:
#            self._log(f"SoundMixerClass.addMusic: Music file not found >>{filename}<< in {sourceFolder}.")
#
#    ###############  Mixer controls  ####################
#    def setupMixer(self):
#        """Preload sounds so the first play has no decode delay."""
#        self.loadSounds(**self.sounds)
#
#    setupPygame = setupMixer  # backward-compatible name
#
#    def quit(self, *args, **kwargs):
#        with self._lock:
#            self._musicToken += 1
#            self.musicChannel.release()
#            for channel in self._channels:
#                channel.release()
#            self._channels.clear()
#            self.soundChannels.clear()
#            self._soundCache.clear()
#            self._musicCache = (None, None)
#        if self.device is not None:
#            try:
#                self.device.close()
#            except Exception as error:
#                self._log(f"SoundMixerClass.quit: {error}")
#            self.device = None
#
#    def checkIfMixerIsReady(self):
#        return self.device is not None and self.device.running
#
#    def isMixerBusyMixing(self):
#        with self._lock:
#            return any(channel.get_busy() for channel in self._channels)
#
#    def stopAllSounds(self, *args, **kwargs):
#        with self._lock:
#            for channel in self._channels: channel.stop()
#
#    def pauseAllSounds(self, *args, **kwargs):
#        with self._lock:
#            for channel in self._channels: channel.pause()
#
#    def unpauseAllSounds(self, *args, **kwargs):
#        with self._lock:
#            for channel in self._channels: channel.unpause()
#
#    def mute(self, *args, **kwargs):
#        with self._lock:
#            if not self._muted:
#                self._savedMasterGain = self.masterGain
#                self.masterGain = 0.0
#                self._muted = True
#
#    def unmute(self, *args, **kwargs):
#        with self._lock:
#            if self._muted:
#                self.masterGain = self._savedMasterGain
#                self._muted = False
#
#    def fadeAllSounds(self, *args, time=1000, **kwargs):
#        time = self._firstIntArg(args, time)
#        with self._lock:
#            for channel in self._channels: channel.fadeout(time)
#
#    def setStandardVolume(self, volume):
#        if self._toUnit(volume) is None:
#            raise Exception("Volume must be between 0 and 10")
#        self.standardVolume = volume
#        with self._lock:
#            self.musicChannel.set_volume(volume / 10)
#
#    ###############  Music playback  ####################
#    def _startMusic(self, name, volume, loops, fade_ms):
#        """Decode music on a background thread, then start it (unless superseded)."""
#        path = self.music[name]['path']
#        with self._lock:
#            self._musicToken += 1
#            token = self._musicToken
#            self.musicChannel.stop()
#            self.musicChannel.set_volume(self._resolveVolume(volume))
#            self.currentMusicName = name
#            self._musicPending = True
#
#        def work():
#            try:
#                cachedPath, source = self._musicCache
#                if cachedPath != path:
#                    source = self._decode(path)
#            except Exception as error:
#                self._log(f"SoundMixerClass: cannot play music >>{name}<<: {error}")
#                with self._lock:
#                    if token == self._musicToken: self._musicPending = False
#                return
#            with self._lock:
#                if token != self._musicToken: return   # another request replaced this one
#                self._musicCache = (path, source)
#                self._musicPending = False
#                self.musicChannel.play(source, name, loops=loops, fade_ms=fade_ms)
#
#        threading.Thread(target=work, name="SoundMixerMusicDecode", daemon=True).start()
#
#    def isMusicPlaying(self):
#        with self._lock:
#            return self._musicPending or self.musicChannel.get_busy()
#
#    def stopMusic(self, *args, **kwargs):
#        with self._lock:
#            self._musicToken += 1
#            self._musicPending = False
#            self.musicChannel.stop()
#
#    def playMusic(self, *args, name=None, volume=None, loops=0, **kwargs):
#        """Play music once (loops=0), N extra times (loops=N) or forever (loops=-1)."""
#        if name is None:
#            name = self.currentMusicName or next(iter(self.music), None)
#            if name is None:
#                raise Exception("No music file loaded")
#        if name not in self.music:
#            raise Exception("Music not found: " + str(name))
#        self._startMusic(name, volume, loops, 0)
#
#    def playContinuousMusic(self, newMusic, *args, volume=3, fade_ms=500, **kwargs):
#        """Loop background music forever. Does nothing if that music is already playing."""
#        if newMusic is None or newMusic not in self.music: return
#        if newMusic == self.currentMusicName and self.isMusicPlaying(): return
#        self._startMusic(newMusic, volume, -1, fade_ms)
#
#    def pauseMusic(self, *args, **kwargs):
#        with self._lock: self.musicChannel.pause()
#
#    def unpauseMusic(self, *args, **kwargs):
#        with self._lock: self.musicChannel.unpause()
#
#    def setMusicVolume_0to10(self, volume):
#        if self._toUnit(volume) is None:
#            raise Exception("Volume must be between 0 and 10")
#        with self._lock: self.musicChannel.set_volume(volume / 10)
#
#    def getMusicVolume(self):
#        return int(round(self.musicChannel.get_volume() * 10))
#
#    def fadeOutMusic(self, *args, time=500, **kwargs):
#        time = self._firstIntArg(args, time)
#        with self._lock: self.musicChannel.fadeout(time)
#
#    def fadeInMusic(self, *args, time=500, **kwargs):
#        time = self._firstIntArg(args, time)
#        with self._lock: self.musicChannel.fadein(time)
#
#    #################### Channels ####################
#    def getUnusedChannel(self):
#        """Return a free channel: an idle unassigned one, a new one (up to maxChannels),
#        an idle assigned one, or finally the channel that started playing longest ago."""
#        with self._lock:
#            assigned = set(id(channel) for channel in self.soundChannels.values())
#            idle = [c for c in self._channels if not c.get_busy()]
#            channel = next((c for c in idle if id(c) not in assigned), None)
#            if channel is None and len(self._channels) < self.maxChannels:
#                channel = _Channel(self, len(self._channels))
#                self._channels.append(channel)
#            if channel is None and idle:
#                channel = min(idle, key=lambda c: c.lastStarted)
#            if channel is None:
#                channel = min(self._channels, key=lambda c: c.lastStarted)
#                channel.stop()
#            for key in [k for k, v in self.soundChannels.items() if v is channel]:
#                del self.soundChannels[key]
#            return channel
#
#    def isChannelBusy(self, channel):
#        with self._lock: return channel.get_busy()
#
#    def playChannel(self, channel=None, name=None, volume=None, loops=0, maxtime=0, fade_ms=0):
#        with self._lock:
#            useChannel = channel if channel is not None else self.soundChannels.get(name)
#            if useChannel is None:
#                useChannel = self.getUnusedChannel()
#                if name is not None: self.soundChannels[name] = useChannel
#            source = None
#            if name in self.sounds:
#                try:
#                    source = self._getSoundSource(self.sounds[name]['path'])
#                except Exception as error:
#                    self._log(f"SoundMixerClass.playChannel: cannot load >>{name}<<: {error}")
#                    return
#            useChannel.set_volume(self._resolveVolume(volume))
#            useChannel.play(source, name, loops=loops, maxtime=maxtime, fade_ms=fade_ms)
#
#    def stopChannel(self, channel):
#        with self._lock: channel.stop()
#
#    def pauseChannel(self, channel):
#        with self._lock: channel.pause()
#
#    def unpauseChannel(self, channel):
#        with self._lock: channel.unpause()
#
#    def fadeOutChannel(self, channel, time=500):
#        with self._lock: channel.fadeout(time)
#
#    def fadeInChannel(self, channel, time=500):
#        with self._lock: channel.fadein(time)
#
#    def getChannelVolume_0to10(self, channel):
#        return int(round(channel.get_volume() * 10))
#
#    def setChannelVolume_0to10(self, channel, volume):
#        if self._toUnit(volume) is None:
#            raise Exception("Volume must be between 0 and 10")
#        with self._lock: channel.set_volume(volume / 10)
#
#    def getSoundAtChannel(self, channel):
#        return channel.get_sound()
#
#    def queueSoundAtChannel(self, channel, sound):
#        """sound may be a sound name or a file path."""
#        path = self.sounds[sound]['path'] if sound in self.sounds else sound
#        name = sound if sound in self.sounds else None
#        try:
#            source = self._getSoundSource(path)
#        except Exception as error:
#            self._log(f"SoundMixerClass.queueSoundAtChannel: cannot load >>{sound}<<: {error}")
#            return
#        with self._lock: channel.queue_sound(source, name)
#
#    def getQueuedSoundsAtChannel(self, channel):
#        with self._lock: return channel.get_queue()
#
#    #################### Sounds ####################
#    def loadSound(self, name, file):
#        """Register a sound file, decode it, and preload it on its own channel."""
#        if not os.path.exists(file):
#            self._log("SoundMixerClass.loadSound: Sound file not found >>" + file + "<<.")
#            return
#        entry = self.sounds.get(name, {})
#        entry['path'] = file
#        entry.setdefault('randomList', [])
#        self.sounds[name] = entry
#        try:
#            source = self._getSoundSource(file)
#        except Exception as error:
#            self._log(f"SoundMixerClass.loadSound: cannot decode >>{file}<<: {error}")
#            return
#        with self._lock:
#            channel = self.soundChannels.get(name) or self.getUnusedChannel()
#            channel.load(source, name)
#            self.soundChannels[name] = channel
#
#    def removeSound(self, name):
#        with self._lock:
#            channel = self.soundChannels.pop(name, None)
#            if channel is not None: channel.release()
#            entry = self.sounds.pop(name, None)
#            if entry is not None: self._soundCache.pop(entry['path'], None)
#
#    def removeAllSounds(self):
#        with self._lock:
#            for channel in self._channels: channel.release()
#            self.sounds.clear()
#            self.soundChannels.clear()
#            self._soundCache.clear()
#
#    def playSound(self, name, *args, volume=3, loops=0, **kwargs):
#        entry = self.sounds.get(name, None)
#        if entry is None:
#            self._log(f"playSound() error: Sound not found >>{name}<<")
#            return
#        try:
#            source = self._getSoundSource(entry['path'])
#        except Exception as error:
#            self._log(f"playSound() error: cannot decode >>{name}<<: {error}")
#            return
#        with self._lock:
#            channel = self.soundChannels.get(name)
#            if channel is None:
#                channel = self.getUnusedChannel()
#                self.soundChannels[name] = channel
#            channel.set_volume(self._resolveVolume(volume))
#            channel.play(source, name, loops=loops)
#
#    def stopSound(self, name=None, *args, **kwargs):
#        """Stop one sound by name, or all sound effects if no name is given."""
#        with self._lock:
#            if name is None:
#                self.stopAllSounds()
#            elif name in self.soundChannels:
#                self.soundChannels[name].stop()
#
#    def pauseSound(self, name, *args, **kwargs):
#        with self._lock:
#            if name in self.soundChannels: self.soundChannels[name].pause()
#
#    def unpauseSound(self, name, *args, **kwargs):
#        with self._lock:
#            if name in self.soundChannels: self.soundChannels[name].unpause()
#
#    def fadeOutSound(self, name, *args, time=500, **kwargs):
#        with self._lock:
#            if name in self.soundChannels: self.soundChannels[name].fadeout(self._firstIntArg(args, time))
#
#    def fadeInSound(self, name, *args, time=500, **kwargs):
#        with self._lock:
#            if name in self.soundChannels: self.soundChannels[name].fadein(self._firstIntArg(args, time))
#
#    def setSoundVolume_0to10(self, name, volume, *args, **kwargs):
#        if name not in self.soundChannels:
#            raise Exception("Sound not found: " + name)
#        if self._toUnit(volume) is None:
#            raise Exception("Volume must be between 0 and 10")
#        with self._lock: self.soundChannels[name].set_volume(volume / 10)
#
#    def getSoundVolume_0to10(self, name):
#        if name in self.soundChannels:
#            return int(round(self.soundChannels[name].get_volume() * 10))
#        return None
#
#    def loadSounds(self, **kwargs):
#        """Preload up to 8 sounds onto their own channels; others decode on first play."""
#        for count, (key, entry) in enumerate(kwargs.items()):
#            if count >= 8: break
#            self.loadSound(key, entry['path'])
#
#    #################### Music file registry ####################
#    def saveMusicFile(self, name, file):
#        self.music[name] = {'path': file}
#
#    def removeMusicFile(self, name):
#        self.music.pop(name, None)
#        if self.currentMusicName == name:
#            self.stopMusic()
#            self.currentMusicName = None
#
#    def removeAllMusic(self):
#        self.stopMusic()
#        self.music.clear()
#        self.currentMusicName = None
#        self._musicCache = (None, None)
#
#    def loadMusic(self, name, file):
#        self.music[name] = {'path': file}
#
#    def loadMusicFiles(self, **kwargs):
#        for key, entry in kwargs.items():
#            self.loadMusic(key, entry['path'] if isinstance(entry, dict) else entry)
#