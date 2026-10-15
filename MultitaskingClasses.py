__version__ = '8.0'
import queue
import threading
import io, os, random, datetime, time
import multiprocessing as mp
from tkinter import *
import queue
import threading
from tkinter.ttk import *

# Time constants
Second = 1000  # milliseconds
One_second = Second
Seconds = Second
Minute = 60 * Second
Minutes = Minute
Hour = 60 * Minute
Hours = Hour
Day = 24 * Hour
Days = Day
Week = 7 * Day
Weeks = Week
_idIndex = 0
_counterIndex = 1
_repeatIndex = 2
_functionIndex = 3 # Beyond this are parameters with last 2 being randon int range when repeat < 0
_parmenterStart = 4
_minimumRepeatParameters = 6 
_repeatRandom = -1
_secondsFunctionIndex = 2
_secondsParameterStart = 3

class ControlledListClass():
    """ A class to hold a list of controlled items using a single lock (both read and write).
    It has all the standard list methods but is thread-safe. For anything else, I suggest
    either using a more complex Python class or copying values out an then manipulating them.
    This class is not meant to be a full replacement for a list, but rather a controlled
    collection that can be accessed by multiple threads. 
    IMPORTANT: Manually get and set the lock for loops.
    """
    def __init__(self):
        self.controlledList = []
        self.lock_queue = mp.Lock()
        
    def __len__(self):
        """ Get the length of the controlled list. """
        with self.lock_queue:
            return len(self.controlledList)
 
    def getLock(self):
        return self.lock_queue
    def setLock(self,lock):
        if not isinstance(lock, mp.Lock):
            self.lock_queue = lock
    def release(self):
        self.lock_queue.release()
            
###################################
    def __getitem__(self, index):
        """ Get an item from the controlled list. """
        with self.lock_queue:
            if index < len(self.controlledList):
                return self.controlledList[index]
            return None
                
    def extend(self, item):
        """ Add item(s) to extend the controlled list. """
        collection = isinstance(item, list) or isinstance(item, tuple)
        with self.lock_queue:
            if collection:
                self.controlledList.extend(item)
            else:
                self.controlledList.extend(item)
        
    def append(self, item):
        """ Add item(s) to the controlled list. """
        collection = isinstance(item, list) or isinstance(item, tuple)
        with self.lock_queue:
            if collection:
                self.controlledList.append(item)
            else:
                self.controlledList.append(item)

    def getList(self):
        """ Get the whole controlled list. Then its not controlled anymore. """
        with self.lock_queue:
            return self.controlledList

    def extract(self):
        """ Get the controlled list and then clear it. """
        with self.lock_queue:
            newList = self.controlledList.copy()
            self.controlledList.clear()
            return newList

    def copy(self):
        """ Copy the controlled list only. """
        with self.lock_queue:
            newList = self.controlledList.copy()
            return newList
        
    def pop(self, number=-1):
        """ pop the controlled list. Return None when empty"""
        with self.lock_queue:
            try:
                item = self.controlledList.pop(number)
            except:
                item = None
            return item
                
    def clear(self):
        """ Clear the controlled list. """
        with self.lock_queue:
            self.controlledList.clear()
                
    def lengthNoLock(self): # Does not lock, used when already locked
        """ Get the length of the controlled list. """
        return len(self.controlledList)            
    def getNoLock(self, number): # Does not lock, used when already locked
        """ Get the length of the controlled list. """
        listing = self.controlledList[number] if number < len(self.controlledList) else None
        return listing        
    def getNoLockCopy(self, number): # Does not lock, used when already locked
        """ Get the length of the controlled list. """
        listing = self.controlledList[number].copy() if number < len(self.controlledList) else None
        return listing
                
    def count(self):
        """ Get the count of the controlled list. """
        with self.lock_queue:
            return self.controlledList.count()
                
    def sort(self):
        """ Sort the controlled list but don't return it. """
        with self.lock_queue:
            self.controlledList.sort()
                
    def reverse(self):
        """ Reverse the controlled list but don't return it. """
        with self.lock_queue:
            self.controlledList.reverse()
                
    def index(self, *args, **wargs):
        """ Return an index in the controlled list. """
        with self.lock_queue:
            result = self.controlledList.index(*args, **wargs)
            return result
                
    def insert(self, *args, **wargs):
        """ Insert within the controlled list. """
        with self.lock_queue:
            self.controlledList.insert(*args, **wargs)
                
    def remove(self, *args, **wargs):
        """ Remove within the controlled list. """
        with self.lock_queue:
            self.controlledList.remove( *args, **wargs)

class QueueClass():
    """Set up a single queue for transmissions, Includes locking for reading and writing.
    The default is to use locking, but this can be turned off for speed."""
    def __init__(self):
        self.queue = queue.Queue()
        self.write_lock_queue = mp.Lock()
        self.read_lock_queue = mp.Lock()
        
    def check(self, withLock=True):
        """ Get an item from the queue with or without locks """
        result = False
        
        if withLock:
            with self.read_lock_queue:
                try:
                    result = self.queue.get_nowait()
                    pass
                except queue.Empty:
                    pass
        else:
            try:
                result = self.queue.get_nowait()
            except queue.Empty:
                pass 
        return result

      
    def get(self, withLock=True):
        """ Get an item from the queue with or without locks """
        result = None
        shuttingDown = False
        
        if withLock:
            with self.read_lock_queue:
                try:
                    result = self.queue.get()
                    shuttingDown = ( result is None) 
                except queue.Empty:
                    pass
        else:
            try:
                result = self.queue.get()
                shuttingDown = ( result is None) 
            except queue.Empty:
                pass 
       
        if shuttingDown:  
            self.ShutDownQueue()
        return result
    
    def put(self, item, withLock=True):
        """ Put an item into the queue with or without locks """
        if withLock:
            with self.write_lock_queue:
                self.queue.put(item)
        else:
            self.queue.put(item)
            
    def stop(self, withLock=True):
        """ Stop the queue by putting None into it with or without locks. """
        if withLock:
            with self.write_lock_queue:
                self.queue.put(None)
        else:
            self.queue.put(None)
            
    def ShutDownQueue(self):
        self.read_lock_queue.release()
        self.write_lock_queue.release()
        self.read_lock_queue = None
        self.write_lock_queue = None
        self.queue.close()

class PipeClass():
    """Pipes send short messages between threads. When defined as duplex, they can be used for both reading and writing.
    The default is to use locking, but this can be turned off for speed. Once ceate, give each thrread the pipe."""
    def __init__(self, duplex=False):
        self.duplex = duplex
        if duplex:
            self.pipe_out, self.pipe_in = mp.Pipe(duplex=duplex)
            self.pipe_in = self.pipe_out
        else:
            self.pipe_out, self.pipe_in = mp.Pipe(duplex=duplex)
        self.write_lock_pipe = mp.Lock()
        self.read_lock_pipe = mp.Lock()

    def check(self, withLock=True):
        if withLock:
            with self.read_lock_pipe:
                anythingThere = self.pipe_out.poll()
                if anythingThere:
                    return self.pipe_out.recv()
                return None
        else:
            anythingThere = self.pipe_out.poll()
            if anythingThere:
                return self.pipe_out.recv()
            return None

    def get(self, withLock=True):
        if withLock:
            with self.read_lock_pipe:
                return self.pipe_out.recv()
        else:
            return self.pipe_out.recv()

    def put(self, val, withLock=True):
        if withLock:
            with self.write_lock_pipe:
                self.pipe_in.send(val)
        else:
            self.pipe_in.send(val)

    def pipes(self):
        return (self.pipe_out, self.pipe_in, self.duplex)

class ThreadClass():
    """ Creates an independent thread for processing (in the background).
    The thread is started with a target function and optional arguments.
    The thread can be stopped and checked for activity. The important part is
    what the task being threaded does.  You need to add in any communications
    with other threads and the main thread. In tkinter only the main thread does graphics.
    """
    def __init__(self, *args):
        self.thread = None
        if len(args) > 0:
            self.start(*args)

    def start(self, target, *args):
        self.thread = threading.Thread(target=target, args=args)
        self.thread.start()
        
    def stop(self):
        if self.thread is not None:
            self.thread.join()
            self.thread = None        
            
    def is_alive(self):
        return self.thread.is_alive() if self.thread else False
    
    
class BasicQueueClass():
    """  A queue used to schedule threaded tasks to be run after a delay. The queue is used until closed
    by receiving a None response. Functions are called as provided. Each queue element is a list or tuple
    containing a function followed by an optional series of parameters or just the function without parameters.
    There is a default delay of 1 second (1000 milliseconds) between checks. 
    The queue will continue to process elements as long as elements are in the queue, then wait using root.after() 
    """
    def __init__(self, *args, **wargs): #root, parent=None, repeat=True, delay=1000):
        self.root = args[0] 
        if len(args) > 1:
            self.parent = args[1]  
        else: 
            self.parent = wargs.get('parent',self.root)  # Parent is optional
        self.repeat = wargs.get('repeat', True)  # If True, keep repeating the queue
        self.repeatDelay = wargs.get('delay', 1000)  # Delay in milliseconds between checks
        self.functionDelay = 1 # millisecond.  An alternative is 0
        
        self.repeatQueue = QueueClass()
        # --> Must be called by child class:  
        # self.process()  # Start the queue processing immediately
        
    def getQueue(self):
        return self.repeatQueue
    
    def stop(self):
        self.repeatQueue.put(None)  # Signal to stop the threads
        
    def put(self, function, *args): # Here, args are added to each function
        """ Add a function to the queue with optional arguments. """
        if isinstance(function, list) or isinstance(function, tuple):
            eachFunction = (*function, *args)
            self.repeatQueue.put(eachFunction)
        else:
            eachFunction = (function, *args)
            self.repeatQueue.put(eachFunction)

    def process(self):
        """ Start the queue and keep repeating using after the delay.
        This is overloaded by different versions of this class."""
        resultReceived = True        
        while resultReceived is not None:
            resultReceived = self.repeatQueue.check()
            if resultReceived is None: # Exit loop
                self.repeat = False 
            elif resultReceived is False:
                break
            
            else:
                if isinstance(resultReceived, tuple):
                    resultReceived = list(resultReceived)  # Convert to list for easier manipulation
                if isinstance(resultReceived, list):
                    if len(resultReceived) > 0:
                        function = resultReceived.pop(0)
                        if isinstance(function, tuple): # Transfered from another queue imbedded in atuple
                            function, *resultReceived = function
                        if callable(function):
                            self.root.after(self.functionDelay, function, *resultReceived)
                elif callable(resultReceived):
                    self.root.after(self.functionDelay, resultReceived)
        if self.repeat: 
            self.root.after(self.repeatDelay, self.process)
    
    
class QueueThreadClass(BasicQueueClass):
    """  A queue used to schedule threaded tasks to be run after a delay. The queue is used until closed
    by receiving a None response. Functions are called as provided. Each queue element is a list or tuple
    containing a function followed by an optional series of parameters or just the function without parameters.
    There is a default delay of 1 second (1000 milliseconds) between checks. 
    The queue will continue to process elements as long as elements are in the queue, then wait using root.after() 
    """
    """ See parent class for details. Parent or rootis required. No use of root.after() function. """
    def __init__(self, *args, **wargs):
        super().__init__(*args, **wargs)
        self.process()  # Start the queue processing immediately

class TransferQueueClass(BasicQueueClass):
    """  See parent class for details. This class is used to transfer data from one queue to another.
    """
    def __init__(self, *args, **wargs):
        super().__init__(*args, **wargs)
        self.receivingQueue = wargs.get('receivingQueue', None)    
        if self.receivingQueue is None:
            self.receivingQueue = QueueClass()
        self.process()  # Start the queue processing immediately 
        
    def getReceivingQueue(self):
        return self.receivingQueue

    def process(self):
        """ OVERLOAD: Collect what was sent into the main queue and pass it on to the receiving queue."""
        resultReceived = True
        queueList = []
        while resultReceived is not None:
            resultReceived = self.repeatQueue.check()
            if resultReceived is None: # Loop exit
                self.repeat = False
            elif resultReceived is False:
                break
            else:
                queueList.append(resultReceived)
        
        if len(queueList) > 0:
            if self.receivingQueue is None: 
                self.repeat = False # No queue means no point in the function
            else:      
                for item in queueList:
                    if item is not None:
                        self.receivingQueue.put(item)

        if self.repeat: 
            self.root.after(self.repeatDelay, self.process)

class GetQueueThreadClass(BasicQueueClass):
    """  See parent class for details. Because get() is used this should only be used by thread.
    """
    def __init__(self, *args, **wargs):
        super().__init__(*args, **wargs)
        self.process()  # Start the queue processing immediately

    def process(self):
        """ OVERLOAD: Start the queue and keep repeating with the get function not the checking function.
        this should only be used by thread and not the mai thread.
        """
        resultReceived = True        
        while resultReceived is not None:
            resultReceived = self.repeatQueue.get() # Wait here until something is received
            if resultReceived is None: # Exit loop
                self.repeat = False 
            elif resultReceived is False:
                break
            
            else:
                if isinstance(resultReceived, tuple):
                    resultReceived = list(resultReceived)  # Convert to list for easier manipulation
                if isinstance(resultReceived, list):
                    if len(resultReceived) > 0:
                        function = resultReceived.pop(0)
                        if callable(function):
                            self.root.after(self.functionDelay, function, *resultReceived)
                elif callable(resultReceived):
                    self.root.after(self.functionDelay, resultReceived)
        if self.repeat: 
            self.root.after(self.repeatDelay, self.process)

class ThreadingQueueClass(BasicQueueClass):   
    """  A queue used to schedule tasks to be run in separate threads. Schedule to check after a delay. 
    The queue is used until closed. Functions are called as provided and not from a parent class.
    Each queue element is a list containing a function followed by an optional series of parameters
    or just the function without parameters. 
    There is a delay to check the queue defaulted to 1 second (1000 milliseconds). The queue
    will continue to process elements as long as they are in the queue, then delays.
    """
    def __init__(self, *args, **wargs):
        super().__init__(*args, **wargs)
        self.join = wargs.get('join', True)  # If True, wait for threads to finish then stop
        self.process()  # Start the queue processing immediately

    def process(self):
        resultReceived = True      
        threads = []  
        while resultReceived is not None:
            resultReceived = self.repeatQueue.check()
            if resultReceived is None: # Exit loop
                self.repeat = False
            elif resultReceived is False:
                break
            
            else:
                if isinstance(resultReceived, tuple):
                    resultReceived = list(resultReceived)  # Convert to list for easier manipulation
                if isinstance(resultReceived, list):
                    for element in resultReceived:
                        thread = ThreadClass()
                        if callable(element):
                            threads.append(thread)
                            thread.start(element)
                        elif isinstance(element, list):
                            function = element.pop(0)
                            if callable(function):
                                threads.append(thread)
                                thread.start(function, *element)
                elif callable(resultReceived):
                    thread = ThreadClass(resultReceived)
                    threads.append(thread)
        if self.join:
            self.queue.put(None)  # Signal to stop the threads
            for thread in threads:
                thread.stop()
        
        if self.repeat: 
            self.root.after(self.functionDelay, self.process)

class ReportingQueueClass(BasicQueueClass):
    """  A queue used to schedule tasks to be run after a delay. The queue is used until closed.
    Each queue element is a list containing a function followed by an optional series of parameters
    or just the function without parameters. Functions are called as provided (no parent class).
    There is a delay to check the queue defaulted to 1 second (1000 milliseconds). The queue
    will continue to process elements as long as they are in the queue, then delays. The functions
    collected are passed on to a provided function for processing. The reporting queue is pcreated
    if not provided
    """    
    def __init__(self, *args, **wargs):
        super().__init__(*args, **wargs)
        self.reportFunction = wargs.get('reportFunction', None)     
        self.reportingQueue = wargs.get('reportingQueue', None)     
        self.reportingQueue = QueueClass() if self.reportingQueue is None else self.reportingQueue
        self.process()
        
    def getComponents(self):
        return self.repeatQueue, self.reportingQueue
    
    def process(self):     
        count = 0 
        
        # Get each resultReceived from the queue and add to the list: self.reportingQueue
        resultReceived = True 
        while resultReceived is not None:
            resultReceived = self.repeatQueue.check()
            if resultReceived is None:
                self.repeat = False
            elif resultReceived is False:
                break
            else:
                self.reportingQueue.put(resultReceived)
                count += 1
                
        # If there are results, call the reportFunction to process them
        if count > 0:
            self.root.after(self.functionDelay, self.reportFunction, self.reportingQueue)
        
        # Repeat the queue process
        if self.repeat: 
            self.root.after(self.functionDelay, self.process)

class TimingThreadClass():
    """Create a thread that repeats the following every delay in milliseconds:
        1.  Manually block and read from a controlled list formatted:
            [countdown, countdown value, function, any arguments passed to the function]
            a countdown value of zero means it runs once then is removed from the list.
        2.  Decrements each countdown in the list until it reaches zero
        3.  Upon reaching zero, the countdown is reset or if 0, marked for removal.
        4. Once complete. obsolete timers are removed and the list is unblocked.
        5. The activated functions are saved in a queue for later processing.
        6. The reportFunction is called to process the queue in the main (graphics) thread.
    """
    def __init__(self, root, reportFunction, controlledList=None, reportingQueue=None, repeat=False):

        self.root = root
        self.reportFunction = reportFunction
        self.reportingQueue = ReportingQueueClass() if reportingQueue is None else reportingQueue 
        self.controlledList = ControlledListClass() if controlledList is None else controlledList
        self.listLock = controlledList.getLock()
        self.repeat = repeat
        self.delay = One_second
        self.thread = None 
        self.processCount = 0
        
    def getComponents(self):
        return self.repeatQueue, self.reportingQueue, self.controlledList
    
    def stop(self):
        self.repeat = False # Stop the thread and the repeat of the thread
        self.controlledList.clear()
        self.reportingQueue.put(None) # Signal to stop the queue
        self.thread.stop()
            
    def start(self):
        if self.thread is None or not self.thread.is_alive():
            self.thread = ThreadClass(self.timingProcess)
        
    def timingProcess(self): 
        """ Process looking for timed items every second"""
        # Manual locking for speed and safety
        activatedTimers = []
        
        # For each item, element[0] is the countdown and [1] is the countdown value
        self.processCount = 0
        whenDoneDeleteIndex = None
        with self.listLock: 
            maximum = self.controlledList.lengthNoLock() # Does not need locking
            for index in range(maximum):
                timingItem = self.controlledList.getNoLock(index) # Does not need locking
                if timingItem is not None:
                    if len(timingItem) <= 2: 
                        print("TimingThreadClass: Invalid timing item, length is less than 3:", timingItem)
                        timingItem[0] = 0 # Set to zero to mark to remove it
                        continue
                    elif timingItem[0] == 0: 
                        continue # Obsolete timer
                    timingItem[0] -= 1
                    if timingItem[0] <= 0:
                        timingItem[0] = timingItem[1] # Negative here means it is a random choice - random selection done in main loop
                        activatedTimers.append(index) # Timers to activate in the reportFunction
                        self.processCount += 1
            
            # Check if there is an item to remove
            if whenDoneDeleteIndex is not None:
                self.controlledList.pop(whenDoneDeleteIndex)
                
        if len(activatedTimers) > 0: self.reportingQueue.put(activatedTimers) # List of timers to activate in the main thread as they are probably graphics
        if self.repeat: self.root.after(One_second, self.timingProcess) 

class TimerControlClass():
    def __init__(self, data, timerQueue=None, repeat=False):
        self.data = data
        self.root = data.root
        self.everySecondList = ControlledListClass()
        self.timedList = ControlledListClass()
        self.timerQueue = QueueClass() if timerQueue is None else timerQueue
        self.timer = None
        self.repeat = repeat
        self.purgeCounter = (4 * Minutes); self.purgeTrigger = (5 * Minutes)  # Purge obsolete timers when trigger is exceeded
        self.lastTimerList = []
        self.nextTimeChecked = 0
        self.controlProcess()
        
    def getQueue(self):
        return self.timerQueue
    
    def getTimedList(self):
        return self.timedList
    
    def stop(self):
        self.repeat = False # Stop the thread and the repeat of the threadself.timer 
        if ( timer := self.timer ): timer.stop()
        self.timerQueue.put(None) # Signal to stop the queue
        try:
            self.everySecondList.release()
            self.timedList.release()
        except:
            pass
                
    def add(self, id, countdown, repeat, function, *args):
        #self.data.logError(f"Adding timer: {countdown=}, {repeat=}, {name=}, args:", *args)
        if repeat == 1:
            timingItem = [countdown, repeat, id, function, *args]
            self.everySecondList.append(timingItem)
        else:
            timingItem = [countdown, repeat, id, function, *args]
            self.timedList.append(timingItem)
        if self.timer is not None:
            self.timer.start() # Allows a restart, ignored if already running
                
    def addTimer(self, id, countdown, repeat, function, *args):
        if repeat == 1:
            timingItem = [countdown, repeat, id, function, *args]
            self.everySecondList.append(timingItem)
        else:
            timingItem = [countdown, repeat, id, function, *args]
            self.timedList.append(timingItem)

    def remove( self, id):
        listLock = self.timedList.getLock()
        with listLock:
            maximum = len(self.timedList) - 1
            for index in range(maximum, -1, -1):
                timingItem = self.timedList[index]
                if timingItem[_idIndex] == id: timingItem.remove(index)
        
        listLock = self.everySecondList.getLock()
        with listLock:
            maximum = len(self.everySecondList) - 1
            for index in range(maximum, -1, -1):
                timingItem = self.everySecondList[index]
                if self.everySecondList[_idIndex] == id: self.everySecondList.remove(index)
        
    def purgeUnusedItems(self):
        listLock = self.timedList.getLock()
        with listLock:
            maximum = len(self.timedList) - 1
            for index in range(maximum, -1, -1):
                timingItem = self.timedList[index]
                if timingItem[_counterIndex] == 0: timingItem.remove(index)
        
        listLock = self.everySecondList.getLock()
        with listLock:
            maximum = len(self.everySecondList) - 1
            for index in range(maximum, -1, -1):
                timingItem = self.everySecondList[index]
                if timingItem[_counterIndex] == 0: self.everySecondList.remove(index)
        
    def controlProcess(self):
        self.purgeCounter += 1
        if self.purgeCounter > self.purgeTrigger:
            self.purgeCounter = 0
            self.purgeUnusedItems()
        
        # The every-second list is protected, unlock for the entire checking
        listLock = self.everySecondList.getLock()
        with listLock:
            length = self.everySecondList.lengthNoLock()
            if length > 0:
                for index in range(length):
                    
                    # Process each timer list NOTE: Why duplicate this and next code?
                    timerList =  self.everySecondList.getNoLockCopy(index)
                    if len(timerList) > _secondsFunctionIndex:
                        function = timerList[_secondsFunctionIndex] 
                        if len(timerList) > _secondsParameterStart:
                            function(*timerList[_secondsParameterStart:])
                        else:
                            function()
        
        # Check the timed list for indexes to timers that are ready to activate
        activeList = self.timerQueue.check()
        while activeList is not None and activeList is not False:
            length = len(activeList)
            for index in range(length):
                try:
                    timerIndex = activeList[index]
                    if timerIndex < 0 or timerIndex >= len(self.timedList):
                        continue
                    timerList = self.timedList[timerIndex]
                    newTimerList = []
                    for item in timerList:
                        newTimerList.append(item)
                    self.lastTimerList = newTimerList  # Copy the list to avoid locking issues
                except:
                    self.lastTimerList = None
                    
                if self.lastTimerList is None or len(self.lastTimerList) < 4: continue
                
                # Process each timer list
                function = self.lastTimerList[_functionIndex]
                if function is not None:
                    if len(self.lastTimerList) > _parmenterStart:
                        function(*self.lastTimerList[_parmenterStart:])
                    else:
                        function()
            activeList = self.timerQueue.check()
        if self.repeat: self.root.after(One_second, self.controlProcess) 
            
    def connectToTimer(self):
        self.timer = TimingThreadClass(self.root, self.controlProcess, 
                             controlledList=self.timedList, reportingQueue=self.timerQueue)
        self.timer.start()

    def reschedule(self):
        """ Reschedule the last timer (if the ids match) based on its last two arguments """
        if self.lastTimerList[_repeatIndex] <= _repeatRandom:
            length = len(self.lastTimerList)
            if length >= _minimumRepeatParameters:
                listLock = self.timedList.getLock()
                with listLock:
                    for item in self.timedList:
                        if item[_idIndex] == self.lastTimerList[_idIndex]:
                            if item[_counterIndex] <= 0:
                                b = length - 1
                                a = b - 1
                                first = self.lastTimerList[a]
                                last = self.lastTimerList[b]
                                try:
                                    number = random.randint(first, last)
                                except:
                                    pass # Invalid range
                                else:
                                    item[_counterIndex] = number
                                break

    def oneSecondCheck(self):
        # Only check the timers after a second has passed without queues
        newTime = time.time()
        if newTime > self.nextTimeChecked:
            self.nextTimeChecked = newTime + 1

            # Check to purge timers periodically
            self.purgeCounter += 1
            if self.purgeCounter > self.purgeTrigger:
                self.purgeCounter = 0
                self.purgeUnusedItems()

            # The every-second list 
            listLock = self.everySecondList.getLock()
            with listLock:
                length = self.everySecondList.lengthNoLock()
                if length > 0:
                    for index in range(length):

                        # Process each timer list in the every second list
                        timerList =  self.everySecondList.getNoLockCopy(index)
                        if len(timerList) > _secondsFunctionIndex:
                            function = timerList[_secondsFunctionIndex] 
                            if len(timerList) > _secondsParameterStart:
                                function(*timerList[_secondsParameterStart:])
                            else:
                                function()

            # Check the timed list for indexes to non-every-second timers that are ready to activate
            activeList = self.timedList.getList()
            length = len(activeList)
            if length > 0:
                self.lastTimerList.clear()
                for index in range(length):
                    # Decrement each counter and select ones that have reached zero (reset if they are resettable)
                    # [countdown, repeat, id, function, *args]
                    timerIndex = activeList[index]
                    timerIndex[0] -= 1
                    if timerIndex[0] != 0: continue
                    timerIndex[0] = timerIndex[1]  # Reset the countdown

                    # Process each timer list
                    function = timerIndex[3]
                    if function is not None:
                        self.lastTimerList.append(timerIndex)
                        if len(timerIndex) > _parmenterStart:
                            function(*timerIndex[_parmenterStart:])
                        else:
                            function()
                    self.purgeCounter += 1

        # Purge after checking the lists
        if self.purgeCounter > self.purgeTrigger:
            self.purgeCounter = 0
            self.purgeUnusedItems()
        
class ProgressBarClass():
    """Provide a progress bar as a thread and queue.
    Initialize the progress bar and include the maximum steps. These will be divided into the space
    provided by your grid system. Set up the grid system next with the .grid() function. Then,
    start the progress bar with .start() and call .step() for each step in the progress bar.
    The bar terminates when the maximum steps are reached or stop() is called.
    """
    def __init__(self, parent, **kwargs):
        self.parent = parent
        self.gridUsed = False
        self.placeUsed = False
        self.packUsed = False
        self.location = {}
        self.counter = 0
        self.endDelay = kwargs.pop('endDelay',True)
        
        # If everything is sent in, start here.  Manually call step()
        if len(kwargs)>0:
            self.gridUsed = kwargs.pop('grid',False)
            self.placeUsed = kwargs.pop('place',False)
            self.packUsed = kwargs.pop('pack',False)
            progressDictionary = {}
            for item in ['cursor','maximum','mode','name','orient','phase','style','takefocus','value','variable']:
                if item in kwargs: progressDictionary[item] = kwargs.pop(item)
            self.location = dict(**kwargs)
            self.details(**progressDictionary)
        
    def grid(self, **kwargs):
        self.gridUsed = True
        self.location = dict(**kwargs)
        
    def place(self, **kwargs):
        self.placeUsed = True
        self.location = dict(**kwargs)
        
    def pack(self, **kwargs):
        self.packUsed = True
        self.location = dict(**kwargs)
        
    def details(self, **kwargs):        
        self.progressDictionary = dict(**kwargs)
        self.progress = Progressbar(self.parent, **self.progressDictionary)
        if self.gridUsed:
            self.progress.grid(**self.location)
        elif self.packUsed:
            self.progress.pack(**self.location)
        else:
            self.progress.place(**self.location)
        self.maximum = self.progress['maximum'] - 1
        
    def start(self):       
        self.spawnThread = ThreadClass(self.spawn_progressBar_thread)
        
    def spawn_progressBar_thread(self):
        """ Spawn a thread to update the progress bar. """
        for i in range(self.maximum):
            self.counter = i
            self.progress.step() 
        # Stop 1 step short, then finish    
        if self.endDelay:
            self.progress.master.after(150,self.progress.step)
        else:
            self.progress.step()
            
    def finish(self):
        for i in range(self.counter+1,self.maximum):
            self.progress.step()
