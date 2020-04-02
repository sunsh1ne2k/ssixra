from ssixa.handlers.base import BaseHandler, BaseWebSocketHandler
from ssixa.base.utils import sanitize

from saml2.s_utils import rndstr

import pyqrcode
import io
import json
import logging

log = logging.getLogger(__name__)

class SAMLBlockchainAuthMehodHandler:
    name = "BlockchainAuthMethod"

class SAMLBlockchainAuthCreateChallengeHandler(BaseHandler, SAMLBlockchainAuthMehodHandler):
    # Initial handler for blockchain auth method
    # Choosable are all SSI solutions with uPort being pre-selected

    def get(self):
        self.call_createchallenge(self.request.query, self.cookies)

    def post(self):
        self.call_createchallenge(self.request.body, self.cookies)

    def call_createchallenge(self, data, cookies):
        prov = self.settings['saml_provider']
        authn, _ = prov.authn_broker.pick()[0]
        solutions = authn.get_available_ssi()
        key = self.get_argument("key","")

        # Get selected SSI from the request data, fall back to default in initial case
        ssi = self.get_argument("ssi","")
        if  ssi == "":
            ssi = authn.get_default_ssi()

        # Get required claims
        claims = prov.get_claims_forkey(key)

        # Get client that redirected to the gateway
        client_id = prov.get_entityid_fromkey(key)

        ret = authn.create_challenge(ssi, claims, client_id)

        qr = pyqrcode.create(ret['challenge'])
        buffer = io.BytesIO()
        qr.svg(buffer, scale=2, background="white", module_color="#000000", xmldecl=False)

        client_name = client_id

        # Write everything to template
        self.render('blockchain.html',
                qrcode=buffer.getvalue().decode(),
                url=ret['url_poll'],
                rand=ret['random'],
                ssi=ssi,
                solutions=solutions,
                action_verify="{}?{}".format(ret['url_verify'],data),
                client_name=client_name,
                key=key)

class SAMLBlockchainAuthVerificationHandler(BaseHandler, SAMLBlockchainAuthMehodHandler):

    def get(self):
        self.call_verification(self.request.query, self.cookies)

    def post(self):
        self.call_verification(self.request.body, self.cookies)

    def call_verification(self, data, cookies):
        prov = self.settings['saml_provider']
        authn, _ = prov.authn_broker.pick()[0]

        name = authn.verify(self.get_argument("random"))

        if not name is None:
            uid = rndstr(24)
            prov.cache.uid2user[uid] = name
            prov.cache.user2uid[name] = uid

            self.set_secure_cookie("pysaml",str(uid))
            self.redirect("{0}?id={1}&key={2}".format("/saml/sso/redirect",uid,self.get_argument("key","")))
        else:
            self.redirect("{0}".format("/saml/sso/redirect"))

class SAMLBlockchainAuthSideChannelVerificationHandler(BaseHandler, SAMLBlockchainAuthMehodHandler):

    def get(self):
        self.call_sideverification(self.request.query, self.cookies)

    def post(self):
        self.call_sideverification(self.request.body, self.cookies)

    def call_sideverification(self, data, cookies):
        authn, _ = self.settings['saml_provider'].authn_broker.pick()[0]

        rand = self.request.uri.split("/")[-1]
        authn.verify_sidechannel(rand, json.loads(data.decode("utf-8")))

        # Nothing to return to the smartphone
        self.write("")

class SAMLBlockchainAuthStatusVerificationHandler(BaseWebSocketHandler, SAMLBlockchainAuthMehodHandler):

    def open(self):
        auth, _ = self.settings['saml_provider'].authn_broker.pick()[0]
        auth.register_statuscallback(self.request.uri.split("/")[-1], self.callback)

    def on_close(self):
        auth, _ = self.settings['saml_provider'].authn_broker.pick()[0]
        auth.unregister_statuscallback(self.request.uri.split("/")[-1], self.callback)

    def on_message(self, message):
        pass

    def callback(self, result):
        self.write_message(result)