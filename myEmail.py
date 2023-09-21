import email
from email.message import EmailMessage
from email.header import decode_header
from html import unescape
import imaplib
import ssl
import threading
from os import getenv

def emailExists():
    imap, messageCount = connectToEmail()
    disconnectFromEmail(imap)
    return messageCount > 0

def connectToEmail():
    # Load system's trusted SSL certificates
    ssl_context = ssl.create_default_context()
    # Connect
    imap = imaplib.IMAP4_SSL(getenv('EmailImapServer'), getenv('EmailImapPort'), ssl_context=ssl_context)
    # authenticate
    imap.login(getenv('EmailUsername'), getenv('EmailPassword'))

    status, messages = imap.select("INBOX")
    # total number of emails
    messageCount = int(messages[0])

    return imap, messageCount

def disconnectFromEmail(imap):
    imap.close()
    imap.logout()


def clean(filename):
    return str(str(filename.split('/')).split('\0'))


def cleanFileName(filename):
    filename = filename.replace("[\"[\'", "")
    filename = filename.replace("\']\"]", "")
    filename = filename.replace("/", "-")
    filename = unescape(filename)

    return filename


def JustTheBody(body):
    bodyStartString = "<body>"
    bodyStart = body.index(bodyStartString)
    bodyEnd   = body.index("</body>")
    if bodyStart and bodyEnd:
        bodyStart += len(bodyStartString)
        body = body[bodyStart:bodyEnd]
    result = (body
                    .replace("<br>", "\n\r")
                    .replace("<p>", "")
                    .replace("</p>", "")
                )
    return result


def doTheWork(postsFolder, staticFolder):
    # TODO:  
    #   Make blog post title be a valid filename.
    #   Handle errors gracefully.  If we come across a folder or file that already exists, 
    #   then we should look at the post's text file.  If our post starts with the same text as
    #   the existing file, then leave it be.  Otherwise, add our text.
    #   If an image file already exists, leave it.  Otherwise, add ours.

    imap, messageCount = connectToEmail()

    for i in range(messageCount, 0, -1):
        # fetch the email message by ID
        res, msgParts = imap.fetch(str(i), "(RFC822)")
        for response in msgParts:
            if isinstance(response, tuple):
                # parse a bytes email into a message object
                msg = email.message_from_bytes(response[1])
                
                # decode the email subject
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    # if it's a bytes, decode to str
                    subject = subject.decode(encoding)
                subject = cleanFileName(subject)

                # TODO:  If subject contains "Year/mm-dd Post Title", then add to that post.

                # decode email sender
                From, encoding = decode_header(msg.get("From"))[0]
                if isinstance(From, bytes):
                    From = From.decode(encoding)
                if From != getenv("MyEmail"):
                    break

                if msg.is_multipart():
                    # iterate over email parts
                    messageBody=""
                    fullFilename=""
                    for part in msg.walk():
                        # extract content type of email
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        try:
                            # get the email body
                            body = part.get_payload(decode=True).decode()
                        except:
                            pass
                        if content_type in ["text/plain", "text/html"] and "attachment" not in content_disposition:
                            messageBody = JustTheBody(body)
                        elif "attachment" in content_disposition:
                            # download attachment
                            filename = clean(part.get_filename())
                            if filename:
                                filename = cleanFileName(filename)
                                fullFilename = staticFolder+filename
                                open(fullFilename, "wb").write(part.get_payload(decode=True))

                    msgId = bytes(str(i), 'utf-8')
                    r = imap.copy(msgId, "INBOX.Trash")             # Copy the message to the Trash
                    r = imap.store(msgId, "+FLAGS", "\\Deleted")    # Mark the original message as deleted
                    r = imap.expunge()                              # Delete the original message
    disconnectFromEmail(imap)

def processEmails(postsFolder, staticFolder):

    # TODO:  If someone is alreay processing emails, get out.

    x = threading.Thread(target=doTheWork, args=(postsFolder, staticFolder))
    x.start()
