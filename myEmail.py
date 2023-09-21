import email
from email.message import EmailMessage
from email.header import decode_header
import imaplib
import ssl

def emailExists():
    return False

def processEmails(rootFolder, emailParams):

    # Load system's trusted SSL certificates
    ssl_context = ssl.create_default_context()
    # Connect
    imap = imaplib.IMAP4_SSL(emailParams['ImapServer'], emailParams['ImapPort'], ssl_context=ssl_context)
    # authenticate
    imap.login(emailParams['Username'], emailParams['Password'])

    status, messages = imap.select("INBOX")
    # total number of emails
    messages = int(messages[0])
    # number of top emails to fetch
    # N = 3

    for i in range(messages, 0, -1):
        # fetch the email message by ID
        res, msg = imap.fetch(str(i), "(RFC822)")
        for response in msg:
            if isinstance(response, tuple):
                # parse a bytes email into a message object
                msg = email.message_from_bytes(response[1])
                # decode the email subject
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    # if it's a bytes, decode to str
                    subject = subject.decode(encoding)
                # decode email sender
                From, encoding = decode_header(msg.get("From"))[0]
                if isinstance(From, bytes):
                    From = From.decode(encoding)
                if msg.is_multipart():
                    # iterate over email parts
                    messageBody=""
                    fullJsonFilename=""
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
                                fullJsonFilename = requestsFolder+filename
                                open(fullJsonFilename, "wb").write(part.get_payload(decode=True))

                    msgId = bytes(str(i), 'utf-8')
                    r = imap.copy(msgId, "INBOX.Trash")             # Copy the message to the Trash
                    r = imap.store(msgId, "+FLAGS", "\\Deleted")    # Mark the original message as deleted
                    r = imap.expunge()                              # Delete the original message
    # close the connection and logout
    imap.close()
    imap.logout()
