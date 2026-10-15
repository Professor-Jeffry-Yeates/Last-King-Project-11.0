__version__ = "11.0"
# Mac Mailing Helper
# Setup GUI and imports
#import smtplib
#from email.message import EmailMessage
import platform
import tkinter as tk
from tkinter import ttk
from CoffeeCanvas import *
from CoffeeBean import *
from CoffeeColors import *

# Shell commands
# python3 -m pip install --upgrade pip
# pip install appscript
# python3 -m pip install appscript
from appscript import app, k
from mactypes import Alias

class Outlook:
    def __init__(self):
        self.client = app('Microsoft Outlook')

class Message:
    def __init__(self, subject='', body='', to_recip=[], cc_recip=[]):
        self.client = Outlook().client
        self.msg = self.client.make(
            new=k.outgoing_message,
            with_properties={k.subject: subject, k.content: body}
        )
        self.add_recipients(to_recip, 'to')
        self.add_recipients(cc_recip, 'cc')

    def add_recipients(self, emails, type_):
        if not isinstance(emails, list):
            emails = [emails]
        for email in emails:
            self.msg.make(
                new=k.to_recipient if type_ == 'to' else k.cc_recipient,
                with_properties={k.email_address: {k.address: email}}
            )

    def add_attachment(self, file_path):
        self.msg.make(
            new=k.attachment,
            with_properties={k.file: Alias(file_path)}
        )

    def send(self):
        self.msg.send()

class PlatformSpecific:
    """Helper class to send emails"""
    def __init__(self):
        self.MacOS = (platform.system().lower() == 'darwin')
        self.PC = not self.MacOS

    def sendEmail(self, **dictionary):
        """Mailing on the Mac with data in a dictionary"""   

        email = Message(
            subject= dictionary["title"],
            body=dictionary["contents"],
            to_recip=[dictionary["mailReciepient"]]
        )
        email.send()