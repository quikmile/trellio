import logging
import logging.handlers
import smtplib

logger = logging.getLogger(__name__)


class BufferingSMTPHandler(logging.handlers.BufferingHandler):
    def __init__(self, mailhost, mailport, fromaddr, toaddrs, subject, capacity, password):
        logging.handlers.BufferingHandler.__init__(self, capacity)
        self.mailhost = mailhost
        self.mailport = mailport
        self.fromaddr = fromaddr
        self.subject = subject
        self.toaddrs = toaddrs
        self.setFormatter(logging.Formatter("%(asctime)s %(levelname)-5s %(message)s"))
        self.smtp = smtplib.SMTP(self.mailhost, self.mailport)
        self.smtp.ehlo()
        self.smtp.starttls()
        self.smtp.login(fromaddr, password)

    def handleError(self, record):
        print(record)  # overriding original and not doing anything

    def flush(self):
        if len(self.buffer) > 0:
            try:
                msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" % (
                    self.fromaddr, ",".join(self.toaddrs), self.subject)
                for record in self.buffer:
                    s = self.format(record)
                    msg = msg + s + "\r\n"
                self.smtp.sendmail(self.fromaddr, self.toaddrs, msg)
            except Exception as e:
                self.handleError(e)  # no particular record
            self.buffer = []
