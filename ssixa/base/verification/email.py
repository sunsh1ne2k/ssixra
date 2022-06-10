from base.verification.verificationbase import VerificationMethodBase
from oic.oic import rndstr
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import smtplib
import datetime
import logging

log = logging.getLogger(__name__)

class SimpleEmailVerification(VerificationMethodBase):
    name = "simpleemail"
    display = "Email Address Attestation"
    claim = "email"
    description = "Verificiation of email addresses by sending an email to the specified address with a " \
                  "verification link. After the link has been opened, the attestation can be retrieved."

    input=["Email"]

    urls= dict(
        url_verify='/verification/email/simpleemail')

    def __init__(self, baseurl, cfg, testmode=False):
        super(SimpleEmailVerification, self).__init__(baseurl, cfg)

        self.db = {}
        self.random_to_user = {}

        self.server = cfg['server']
        self.port = cfg['port']
        self.username = cfg['username']
        self.password = cfg['password']
        self.fromAddress = cfg['fromAddress']
        self.debug = cfg['debug']

        self.testmode = testmode
        self.testoutput = None

        self.ttl = 30
        self.ttl_to_retrieve = 100

        # Extend entry points with base url
        for url in self.urls:
            self.urls[url] = baseurl + self.urls[url]

        # Set StartTLS flag
        self.startTLS = False
        if 'starttls' in cfg and cfg['starttls']:
            self.startTLS = True

    def __call__(self, username, email):
        log.debug("Username: " + str(username))
        log.debug("Email: " + str(email))

        msg = MIMEMultipart()

        random = rndstr(25)
        self.db[username] = dict(
            value=email,
            random=random,
            start=datetime.datetime.now(),
            verified=False
        )
        self.random_to_user[random] = username

        msg['From'] = self.fromAddress
        msg['To'] = email
        msg['Subject'] = "Email Address Verification"
        body = MIMEText("Dear receipient, \nthis email has been sent to you for verification of your email address. " \
               "Please click on the following link to verify your access to this mailbox: \n\n" + \
               "{}/{}".format(self.urls['url_verify'],random), 'plain', 'utf-8')
        msg.set_payload(body)
        text = msg.as_string()

        self.sendVerificationEmail(text, email)
        log.debug("Verification email sent")

    def sendVerificationEmail(self, text, recipient):
        if not self.testmode:
            server = smtplib.SMTP(self.server, self.port)

        if self.debug and not self.testmode:
            server.set_debuglevel(1)

        if self.startTLS:
            server.starttls()

        if len(self.username) > 0 and len(self.password) > 0:
            server.login(self.username, self.password)

        if not self.testmode:
            server.sendmail(self.fromAddress, recipient, text)
            server.quit()
        else:
            self.testoutput = dict(fromAddress=self.fromAddress, recipient=recipient, text=text)

    def process_verification(self, random):
        user = self.random_to_user[random]

        if self.db[user]['start'] + datetime.timedelta(minutes=self.ttl) > datetime.datetime.now():
            self.db[user]['verified'] = True
            self.db[user]['start_attest'] = datetime.datetime.now()

            return self.db[user]['value']

        return None

    def verification_completed(self, username):
        if username not in self.db:
            return False

        if self.db[username]['verified'] == True:
            return True
        else:
            return False

    def get_claim_value(self, username):
        if username not in self.db:
            return None

        if self.db[username]['verified'] == False:
            return None

        return self.db[username]['value']

    # Will be regularly called by the verification method manager
    def cleanExpiredEntries(self):
        for entry in self.db:
            # Expiration of non-verified claims
            if (self.db[entry]['verified'] == False) and (self.db[entry]['start'] + datetime.timedelta(minutes=self.ttl) < datetime.datetime.now()):
                random = self.db[entry]['random']
                del self.db[entry]
                del self.random_to_user[random]
            # Expiration of attestation retrieval of verified claims
            if (self.db[entry]['verified'] == True) and (self.db[entry]['start_attest'] + datetime.timedelta(minutes=self.ttl_to_retrieve) < datetime.datetime.now()):
                random = self.db[entry]['random']
                del self.db[entry]
                del self.random_to_user[random]