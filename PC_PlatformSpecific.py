# PC Mailing Helper
__version__ = "11.0"
# PC Mailing Helper
import platform

# Used for email
class PlatformSpecific:
    """Helper class to send emails"""
    def __init__(self):
        self.MacOS = (platform.system().lower() == 'darwin')
        self.PC = not self.MacOS
        if self.PC:
            try:
                import win32com.client # may need: "pip install pywin32"  (may need to update pip)
            except:
                pass

    def sendEmail(self, **dictionary):
        if self.PC:
            outlook = win32com.client.Dispatch('outlook.application')
            mail = outlook.CreateItem(0) # 0 is a mail item
            mail.To = dictionary["mailReciepient"]
            mail.subject = dictionary["title"]
            mail.BodyFormat = 1 # Plain text
            mail.Body = dictionary["contents"]
            mail.Send()