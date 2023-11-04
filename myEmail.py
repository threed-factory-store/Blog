import base64
from datetime import datetime
import email
from email.message import EmailMessage
from email.header import decode_header
from flask import request
from html import unescape
import imaplib
import mailparser
import re
import ssl
import threading
from os import getenv, remove, makedirs, path
import time


def newMailCount():
    imap, messageCount = connectToEmail()
    disconnectFromEmail(imap)
    return messageCount

def connectToEmail():
    ssl_context = ssl.create_default_context()
    imap = imaplib.IMAP4_SSL(getenv('EmailImapServer'), getenv('EmailImapPort'), ssl_context=ssl_context)
    imap.login(getenv('EmailUsername'), getenv('EmailPassword'))

    status, messages = imap.select("INBOX")
    messageCount = int(messages[0])

    return imap, messageCount


def disconnectFromEmail(imap):
    try:
        imap.close()
        imap.logout()
    except:
        pass


def clean(filename):
    return str(str(filename.split('/')).split('\0'))


def cleanFileName(filename):
    filename = filename.replace("[\"[\'", "")
    filename = filename.replace("\']\"]", "")
    filename = filename.replace("/", "-")
    filename = unescape(filename)

    return filename


def cleanFrom(From):
    result = From
    if "<" in result:
        match = re.search('<(.*)>', result)
        if match:
            result = match.group(1)
        
    return result


def getMessageYearAndSubject(subject):
    now = datetime.now()
    year = now.year
    guessedYear = True
    month = now.month
    day = now.day
    monthDay = "{:02d}-{:02d}".format(month, day)
    subject = subject.replace("Fwd: ", "")
    mySubject = subject

    yearMatch = re.search('^[0-9]+/', mySubject)
    if yearMatch:
        subjectParts = mySubject.split("/", 1)
        subjectYear = subjectParts[0]
        if len(subjectYear) <= 4:
            try:
                intYear = int(subjectYear)
                if intYear < 100:
                    intYear += year // 100 * 100
                if intYear <= year:
                    year = intYear
                    guessedYear = False
                    mySubject = subjectParts[1]
            except:
                pass
    
    sep = "-"
    monthDayMatch = re.search('^\d+'+sep+'\d+ ', mySubject)
    if not monthDayMatch:
        sep = "/"
        monthDayMatch = re.search('^\d+'+sep+'\d+ ', mySubject)

    if monthDayMatch:
        monthDayFound = monthDayMatch.group(0)
        monthDayParts = monthDayFound.split(sep)
        monthStr = monthDayParts[0]
        dayStr = monthDayParts[1]
        try:
            intMonth = int(monthStr)
            intDay = int(dayStr)
            monthDay = "{:02d}-{:02d}".format(intMonth, intDay)
            month = intMonth
            day = intDay

            monthDayPlusRest = mySubject.split(" ", 1)
            mySubject = monthDayPlusRest[1]
        except:
            pass

    if guessedYear:
        guessedDate = datetime(year, month, day)
        # Let date be tomorrow in case the email is coming from some weird timezone.
        maxLegitDate = now + datetime.timedelta(days=1)
        if guessedDate > maxLegitDate:
            year = now.year-1

    subject = monthDay+" "+mySubject
    subject = cleanFileName(subject)

    return "{:04d}".format(year), subject


def saveMessageText(staticFolder, msgYear, subject, text):
    folder = path.join(staticFolder,msgYear,subject)
    makedirs(folder, exist_ok=True)
    filename = folder+"/"+subject
    mode = "w"
    if path.exists(filename):
        mode = "a"

    with open(filename, mode) as myfile:
        if mode == "a":
            myfile.write("<br><br>")
        myfile.write(text)
        

def saveMessageAttachment(staticFolder, msgYear, subject, filename, img):
    if filename:
        filename = cleanFileName(filename)
        folder = path.join(staticFolder,msgYear,subject)
        makedirs(folder, exist_ok=True)
        fullFilename = folder+"/"+filename
        open(fullFilename, "wb").write(base64.b64decode(img))


def fixMailBody(mail, staticUrl, msgYear, subject):
    result = mail.body
    mail_boundary = "--- mail_boundary ---"
    if mail_boundary in result:
        idx = result.index(mail_boundary)
        result = result[idx+len(mail_boundary):]

    for a in mail.attachments:
        contentId = a['content-id']
        contentId = contentId[1:]
        contentId = contentId[:-1]
        cid = "cid:"+contentId
        url = staticUrl+"/"+msgYear+"/"+subject+"/"+a['filename']
        if cid in result:
            result = result.replace(cid, url)
        else:
            result +=   "<div>\n"+\
                        "<img src='"+url+"'>\n"+\
                        "</div>\n"

    return result


def doTheWorkEmail(staticUrl, staticFolder, response):
    imap, messageCount = connectToEmail()

    try:
        for i in range(messageCount, 0, -1):
            res, msgParts = imap.fetch(str(i), "(RFC822)")
            for response in msgParts:
                if isinstance(response, tuple):
                    mail = mailparser.parse_from_bytes(response[1])
                    msgYear, subject = getMessageYearAndSubject(mail.subject)
                    body = fixMailBody(mail, staticUrl, msgYear, subject)
                    From = cleanFrom(mail.from_[0][1])
                    if From != getenv("MyEmail"):
                        break

                    for a in mail.attachments:
                        img = a['payload']
                        saveMessageAttachment(staticFolder, msgYear, subject, a['filename'], img)

            if body:
                saveMessageText(staticFolder, msgYear, subject, body)
            
            msgId = bytes(str(i), 'utf-8')
            r = imap.copy(msgId, "INBOX.Trash")             # Copy the message to the Trash
            r = imap.store(msgId, "+FLAGS", "\\Deleted")    # Mark the original message as deleted
            r = imap.expunge()                              # Delete the original message

    finally:
        setBusy(response, False)
        disconnectFromEmail(imap)


# def doTheWork(staticUrl, staticFolder, response):
#     # TODO:  
#     #   Make blog post title be a valid filename.
#     #   Handle errors gracefully.  If we come across a folder or file that already exists, 
#     #   then we should look at the post's text file.  If our post starts with the same text as
#     #   the existing file, then leave it be.  Otherwise, add our text.
#     #   If an image file already exists, leave it.  Otherwise, add ours.

#     imap, messageCount = connectToEmail()

#     try:
#         for i in range(messageCount, 0, -1):
#             gotHtmlText = False
#             res, msgParts = imap.fetch(str(i), "(RFC822)")
#             for response in msgParts:
#                 if isinstance(response, tuple):
#                     msg = email.message_from_bytes(response[1])
                    
#                     subject, encoding = decode_header(msg["Subject"])[0]
#                     if isinstance(subject, bytes):
#                         subject = subject.decode(encoding)
#                     msgYear, subject = getMessageYearAndSubject(subject)

#                     From, encoding = decode_header(msg.get("From"))[0]
#                     if isinstance(From, bytes):
#                         From = From.decode(encoding)
#                     From = cleanFrom(From)
#                     if From != getenv("MyEmail"):
#                         break

#                     messageBody=""
#                     if msg.is_multipart():
#                         for part in msg.walk():
#                             content_type = part.get_content_type()
#                             content_disposition = str(part.get("Content-Disposition"))
#                             try:
#                                 if content_type == "text/plain": # and not gotHtmlText:
#                                     messageBody += "\n"+part.get_payload(decode=True).decode()
#                                 # if content_type == "text/html":
#                                 #     messageBody = part.get_payload(decode=True).decode()
#                                 #     gotHtmlText = True
#                             except:
#                                 pass
#                             if  ("attachment" in content_disposition or
#                                 "inline" in content_disposition):
#                                 filename = clean(part.get_filename())
#                                 if filename:
#                                     img = part.get_payload(decode=True)
#                                     saveMessageAttachment(staticFolder, msgYear, subject, filename, img)
#                                     messageBody += "\n("+filename+")"
#                     else:
#                         messageBody = msg.get_payload(decode=True).decode()

#                     if messageBody:
#                         saveMessageText(staticFolder, msgYear, subject, messageBody)

#                     msgId = bytes(str(i), 'utf-8')
#                     r = imap.copy(msgId, "INBOX.Trash")             # Copy the message to the Trash
#                     r = imap.store(msgId, "+FLAGS", "\\Deleted")    # Mark the original message as deleted
#                     r = imap.expunge()                              # Delete the original message
#     finally:
#         setBusy(response, False)
#         disconnectFromEmail(imap)


lastCheckedCookieName = "LastCheckedWhen"
lastCheckedFormat = "%m/%d/%Y %H:%M:%S"
def setLastCheckedWhen(response):
    now = datetime.now() 
    nowStr = now.strftime(lastCheckedFormat)
    response.set_cookie(lastCheckedCookieName, nowStr)


def itsBeenXMinutesSince(x, since: datetime):
    now = datetime.now()
    diff = now - since
    minutes = diff.total_seconds() / 60
    return minutes > x


def isItTimeToCheck():
    lastCheckedStr = request.cookies.get(lastCheckedCookieName)
    if not lastCheckedStr:
        return True
    
    lastChecked = datetime.strptime(lastCheckedStr, lastCheckedFormat)
    return itsBeenXMinutesSince(10, lastChecked)


busyFilename = "./storage/busyProcessingEmails"
def someoneIsProcessingEmails(response):
    if path.exists(busyFilename):
        modified = datetime.fromtimestamp(path.getmtime(busyFilename))
        if itsBeenXMinutesSince(10, modified):
            setBusy(response, False)
            return False
        else:
            return True
    else:
        return False

def setBusy(response, busy):
    if busy:
        with open(busyFilename, "w") as file:
            file.write("Z")
        setLastCheckedWhen(response)
    else:
        try:
            remove(busyFilename)
        except:
            pass


def processEmails(staticUrl, staticFolder, response):

    if not isItTimeToCheck():
        return

    if someoneIsProcessingEmails(response):
        return

    setBusy(response, True)
    x = threading.Thread(target=doTheWorkEmail, args=(staticUrl, staticFolder, response))
    x.start()
