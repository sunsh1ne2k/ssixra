from handlers.base import BaseHandler

from urllib.parse import parse_qs
from saml2.httputil import BadRequest
from saml2.httputil import NotFound
from saml2.httputil import Redirect
from saml2.httputil import Response
from saml2.httputil import ServiceError
from saml2.httputil import Unauthorized
from saml2 import BINDING_HTTP_POST
from saml2 import BINDING_HTTP_REDIRECT
from oic.utils.http_util import Redirect as OICRedirect

import re
import logging

log = logging.getLogger(__name__)

class SAMLSSOPostHandler(BaseHandler):

    def post(self):
        self.call(self.request.body, self.cookies)

    def call(self, data, cookies):
        p = self.settings['saml_provider']
        elements = dict([(k, v[0]) for k, v in parse_qs(data).items()])

        uid = self.get_secure_cookie("pysaml")
        if not uid is None:
            elements["pysaml"] = uid.decode()

        resp = p.sso_redirect_or_post(elements, BINDING_HTTP_POST)
        if isinstance(resp, BadRequest) or isinstance(resp, ServiceError) or isinstance(resp, Unauthorized):
            self.send_error(int(resp.status[:3]), message=resp.message)
        elif isinstance(resp, OICRedirect):
            self.redirect("{0}".format(resp.message))
        else:
            self.write(resp.message)

class SAMLSSORedirectHandler(BaseHandler):

    def get(self):
        self.call(self.request.query, self.cookies)

    def call(self, data, cookies):
        p = self.settings['saml_provider']
        elements = dict([(k, v[0]) for k, v in parse_qs(data).items()])

        uid = self.get_secure_cookie("pysaml")
        if not uid is None:
            elements["pysaml"] = uid.decode()

        resp = p.sso_redirect_or_post(elements, BINDING_HTTP_REDIRECT)
        if isinstance(resp, BadRequest) or isinstance(resp, ServiceError) or isinstance(resp, Unauthorized):
            self.send_error(int(resp.status[:3]), message=resp.message)
        elif isinstance(resp, OICRedirect):
            self.redirect("{0}".format(resp.message))
        elif isinstance(resp, Response):
            if resp.message['method'] == BINDING_HTTP_POST:
                body = re.search('<body[a-zA-Z0-9\s=:\".\[\]\(\)\>\<\/,+]*</body>',resp.message['data']).group()
                self.write(body)
            else:
                self.write(resp.message['data'])
        else:
            self.write(resp.message)

class SAMLSLORedirectHandler(BaseHandler):

    def get(self):
        self.call(self.request.query, self.cookies)

    def call(self, data, cookies):
        p = self.settings['saml_provider']
        elements = dict([(k, v[0]) for k, v in parse_qs(data).items()])

        resp = p.sso_redirect_or_post(elements, BINDING_HTTP_REDIRECT)
        self.clear_cookie("pysaml")
        self.write(resp.message)

class SAMLSLOPostHandler(BaseHandler):

    def post(self):
        self.call(self.request.query, self.cookies)

    def call(self, data, cookies):
        p = self.settings['saml_provider']
        elements = dict([(k, v[0]) for k, v in parse_qs(data).items()])

        resp = p.sso_redirect_or_post(elements, BINDING_HTTP_POST)
        self.clear_cookie("pysaml")
        self.write(resp.message)