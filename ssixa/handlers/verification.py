from handlers.base import BaseHandler
from base.utils import sanitize

import logging
import tornado

log = logging.getLogger(__name__)

class SimpleEmailVerificationStartHandler(BaseHandler):

    def get(self):
        self.start_verification()

    def start_verification(self):
        user = sanitize(self.get_query_argument("user"))
        email = sanitize(self.get_query_argument("email"))

        try:
            method = self.settings['verificationmanager'].get_verificationmethod_byname('simpleemail')
            method(user, email)
        except Exception as e:
            log.exception("Start email verification failed")
            self.send_error()
        self.set_status(200)

class SimpleEmailVerificationProcessVerificationHandler(BaseHandler):

    def get(self):
        self.verify()

    def verify(self):
        try:
            method = self.settings['verificationmanager'].get_verificationmethod_byname('simpleemail')
            email = method.process_verification(self.request.uri.split("/")[-1])
            if email is None:
                email = ''
        except Exception as e:
            log.exception("Email verification failed")

        self.render("verification/simpleemailverification.html", email=email)

class LDAPVerificationStartHandler(BaseHandler):

    def get(self):
        self.verify()

    def verify(self):
        user = sanitize(self.get_query_argument("user"))
        password = sanitize(self.get_query_argument("password"))

        try:
            method = self.settings['verificationmanager'].get_verificationmethod_byname('ldapver')

            method(user,password)

        except Exception as e:
            log.exception("LDAP verification failed")

        self.set_status(200)