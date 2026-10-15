__version__ = "11.0"
import sys, socket
if sys.platform.lower() != "darwin":
    import pyodbc
else:
    import random as pyodbc # Stop the error but may crash - DB not implemented for MacOS
#################################################################################################
# Classes to hold communications and the response from a database query
class DatabaseInfo:
    """ This class only initializes this information for the other classes"""
    def __init__(self):

        # Get host/server name information to identify this computer and server
        self.ServerName = socket.gethostname()    
        self.EnforceLogins = False # Set to True to force logins to be used for most queries
        self.UserName = "" # These two are needed if logins are enforced
        self.UserPassword = "" # These two are needed if logins are enforced
        self.DatabaseName = "Sample" # Default name

class SqlDatabaseProcessing():
    """ Query a database found in the DatabaseInfo class. Enforcement not implemented."""
    def __init__(self, enforceLogin = None):
        self.databaseInfo = DatabaseInfo() 
        self.useServer =  self.databaseInfo.ServerName 
        self.useDatabase =  self.databaseInfo.DatabaseName 
        self.userName =  self.databaseInfo.UserName
        self.userPassword =  self.databaseInfo.UserPassword
        self.forceDatabaseLogin =  self.databaseInfo.EnforceLogins

    def queryDatabase(self, query): 
        """
        Query the database using global server and database
        Also check if login values are enforced or if the Windows User credentials are used"""
        
        # Query connection string
        response = None
        conx_string = None
        if self.forceDatabaseLogin:
            conx_string = 'DRIVER={SQL SERVER};' + f'SERVER={self.useServer};Database={self.useDatabase};UID={self.username};PWD={self.userPassword};'
        else:
            conx_string = 'DRIVER={SQL SERVER};' +  f'SERVER={self.useServer};Database={self.useDatabase};Trusted_Connection=Yes' #True;Encrypt=False;TrustServerCertificate=True;MultipleActiveResultSets=true'

        # Ensure there is a query to send
        response = None
        if len(conx_string) == 0 :
            response =  DBresponse( None, [], "No connection string provided", error=True )
        elif query == None :
            response =  DBresponse(  None, [], "No query provided", error=True )   
        elif len(query) == 0 :
            response =  DBresponse(  None, [], "No query provided", error=True )   

        # Try the query and return the results in a DBresponse clsss
        # MacOS uses Darwin and daabasea ccess is not defined yet
        elif sys.platform.lower() == "darwin":
            response =  DBresponse(  None, [], "No server response or bad SQL query", error=True ) 
        else:
            try:
                with pyodbc.connect(conx_string) as conx:
                    cursor = conx.cursor()
                    cursor.execute(query)
                    data = cursor.fetchall()
            except:
                response =  DBresponse(  None, [], "No server response or bad SQL query", error=True ) 
                
            else:
                if len(data) == 0: 
                    response = DBresponse(  None, [], "No server response") 
                    response.empty = True
                else:
                    message = data[0]
                    if len(message) > 0:
                       message = message[0]
                    response = DBresponse( cursor, data, message ) 

        return response
        
class DBresponse:
    """ CLass used to hold the response from a database request"""
    def __init__(self, cursor, data, message="", error=False):
        """The parameters are:
        1. cursor : non-data response from the sql server
        2. data: the data from the server as an array of tuples
        3. message: any provided message
        4. error: boolean of an recognised error, see the message
        
        Below are the contents of this class:"""
        self.data = data # Copy of the provided data
        self.answer = "" # a single JSON-like string for checking as an answer
        self.error = error # Boolean provided as an error
        self.message = message if error else "" # Any provided message
        self.lines = [] # Data divided into a list of lists
        self.header = [] # The headers with extra spacing removed
        self.empty = False
        self.query = ""
        
        if cursor is not None:
            
        # Extract the headers from the cursor data
            theHeaders = []
            description = cursor.description
            for eachHeader in description:
                eachHeading = eachHeader[0]
                theHeaders.append(eachHeading)    
            self.header = theHeaders    
            
            # Extract the data into a list of lists (data has whitespace removed)
            if len(self.data) > 0:
                theContents = []
                for line in self.data:
                    piecesOfData = []
                    for item in line:
                        if type(item) is str:
                            dataPoint = item.strip()
                        else:
                            dataPoint = str(item)
                        piecesOfData.append(dataPoint)
                    theContents.append(piecesOfData)
                self.lines = theContents

            # Response of headers and data are placed into a csv format for checking if the answer is correct
            answer = ""
            length = len(self.header) - 1
            for count,item in enumerate( self.header):
                answer += item
                if length > count: answer += ','
            answer += "\n"
                
            for line in self.lines:
                length = len(line) - 1
                for count,item in enumerate( line):
                    answer += item
                    if length > count: answer += ','
                answer += "\n"
            self.answer = answer
