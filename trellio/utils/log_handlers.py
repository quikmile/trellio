import string, logging, logging.handlers
import smtplib

class BufferingSMTPHandler(logging.handlers.BufferingHandler):
    def __init__(self, mailhost, mailport, fromaddr, toaddrs, subject, capacity):
        logging.handlers.BufferingHandler.__init__(self, capacity)
        self.mailhost = mailhost
        self.mailport = mailport
        self.fromaddr = fromaddr
        self.toaddrs = toaddrs
        self.setFormatter(logging.Formatter("%(asctime)s %(levelname)-5s %(message)s"))
        self.smtp = smtplib.SMTP(self.mailhost,self.mailport)
        self.smtp.ehlo()
        self.smtp.starttls()
        self.smtp.login()

    def handleError(self, record):
        print(record)

    def flush(self):
        if len(self.buffer) > 0:
            try:
                msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" % (self.fromaddr, string.join(self.toaddrs, ","), self.subject)
                for record in self.buffer:
                    s = self.format(record)
                    print(s)
                    msg = msg + s + "\r\n"
                self.smtp.sendmail(self.fromaddr, self.toaddrs, msg)
            except Exception as e:
                self.handleError(e)  # no particular record
            self.buffer = []

def test():
    MAILHOST = 'beta'
    FROM = 'log_test11@red-dove.com'
    TO = ['arkadi_renko']
    SUBJECT = 'Test Logging email from Python logging module (buffering)'
    logger = logging.getLogger("")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(BufferingSMTPHandler(MAILHOST, FROM, TO, SUBJECT, 10))
    for i in range(102):
        logger.info("Info index = %d", i)
    logging.shutdown()

if __name__ == "__main__":
    test()