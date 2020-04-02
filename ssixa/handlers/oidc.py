import logging

from ssixa.handlers.base import BaseHandler
from oic.utils.webfinger import OIC_ISSUER
from oic.utils.webfinger import WebFinger
from oic.utils.http_util import Redirect
from oic.utils.http_util import SeeOther

log = logging.getLogger(__name__)

class OIDCAuthorizationHandler(BaseHandler):

    def get(self):
        self.call_authorization(self.request.query, self.cookies)

    def post(self):
        self.call_authorization(self.request.body, self.cookies)

    def call_authorization(self, data, cookies):
        p = self.settings['oidc_provider']
        resp = p.authorization_endpoint(request=data, cookie=cookies)

        # Redirect to authentication uri of select UserAuthnMethod
        if isinstance(resp, Redirect):
            self.redirect("{0}?{1}".format(resp.message,data))
        elif isinstance(resp, SeeOther):
            if self.get_cookie("pyoidc") is not None:
                self.set_cookie("pyoidc",self.get_cookie("pyoidc"))
            self.redirect(resp.message)
        else:
            self.send_error()

class OIDCRegistrationHandler(BaseHandler):

    def get(self):
        self.call_registration(self.request.query, self.cookies)

    def post(self):
        self.call_registration(self.request.body, self.cookies)

    def call_registration(self, data, cookies):
        p = self.settings['oidc_provider']
        resp = p.registration_endpoint(request=data, cookie=cookies)
        self.write(resp.message)

class OIDCTokenHandler(BaseHandler):

    def get(self):
        self.call_token(self.request.query, self.cookies)

    def post(self):
        self.call_token(self.request.body, self.cookies)

    def call_token(self, data, cookies):
        p = self.settings['oidc_provider']
        resp = p.token_endpoint(request=data.decode("utf-8"), cookie=cookies)

        self.set_header("Content-type","application/json")
        self.write(resp.message)


class OIDCUserInfoHandler(BaseHandler):

    def get(self):
        self.call_userinfo(self.request.query, self.cookies)

    def post(self):
        self.call_userinfo(self.request.body, self.cookies)

    def call_userinfo(self, data, cookies):
        p = self.settings['oidc_provider']
        resp = p.userinfo_endpoint(request=data, cookie=cookies)

        self.set_header("Content-type","application/json")
        self.write(resp.message)


class OIDCEndSessionHandler(BaseHandler):

    def get(self):
        self.call_endsession(self.request.query, self.cookies)

    def post(self):
        self.call_endsession(self.request.body, self.cookies)

    def call_endsession(self, data, cookies):
        p = self.settings['oidc_provider']
        resp = p.endsession_endpoint(request=data.decode("utf-8"), cookie=cookies)

        self.write(resp.message)

class OIDCConfigurationHandler(BaseHandler):

    def get(self):
        self.call_configuration(self.request.query, self.cookies)

    def post(self):
        self.call_configuration(self.request.body, self.cookies)

    def call_configuration(self, data, cookies):
        p = self.settings['oidc_provider']
        resp = p.providerinfo_endpoint(request=data, cookie=cookies)
        self.write(resp.message)


class OIDCWebfingerHandler(BaseHandler):

    def get(self):
        params = self.request.query_arguments

        if params['rel'][0].decode('utf-8') == OIC_ISSUER:
            wf = WebFinger()
            self.write(wf.response(params["resource"][0].decode('utf-8'), self.settings['oidc_provider'].baseurl))
        else:
            return self.send_error()