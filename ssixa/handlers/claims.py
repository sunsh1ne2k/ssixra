from handlers.base import BaseHandler
from base.utils import sanitize
from base.ssi.jolocom import Jolocom

import tornado
import pyqrcode
import io
import json
import logging

log = logging.getLogger(__name__)

class ClaimsHandler(BaseHandler):

    def get(self):
        # Get enabled verification modules
        params = dict()
        params['claims'] = dict()

        for module in self.settings['verificationmanager'].get_verificationmethods():
            mo = self.settings['verificationmanager'].get_verificationmethod_byname(module)
            params['claims'][mo.name] = mo.propertiesToDict()

        self.render("claims.html", params=params)


# Handler must be called with Javascript, it does not deliver a complete page
class VerifyClaimsHandler(BaseHandler):

    def get(self):
        name = sanitize(self.get_argument("claim_name", ""))
        claim_value = sanitize(self.get_argument("claim_value", ""))

        if name == "" or claim_value == "":
            return self.write("error")

        error = False
        try:
            method = self.settings['verificationmanager'].get_verificationmethod_byname(name)

            # Start verification
            method(self.current_user, claim_value)
        except Exception as e:
            log.error("Exception occurred during verification. " + str(e))
            error = True

        if error:
            self.write("error")
        else:
            self.write("ok")


# Handler must be called with Javascript, it does not deliver a complete page
class GetAttestationClaimsHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        authn = self.settings['oidc_provider'].authn_broker.get_method("BlockchainAuthMethod")
        ssi = authn.ssi[self.settings['temp_db']['userinfo'][self.current_user]['ssi']]

        name = sanitize(self.get_argument("claim_name",""))
        if name == "":
            return self.write("error")

        error = False
        attestation = ""
        try:
            method = self.settings['verificationmanager'].get_verificationmethod_byname(name)

            # On successful verification return attestation
            if method.verification_completed(self.current_user):
                claim_value = method.get_claim_value(self.current_user)
                ret = ssi.createAttestedClaim(self.settings['temp_db']['userinfo'][self.current_user]['id'], method.claim, claim_value)
                qr = pyqrcode.create(ret)
                buffer = io.BytesIO()
                qr.svg(buffer, scale=2, background="white", module_color="#000000", xmldecl=False)

                attestation=buffer.getvalue().decode()

        except Exception as e:
            log.error("Exception occurred during attestation generation. " + str(e))
            error = True

        if error:
            self.write("error")
        else:
            self.write(attestation)

class ReceiveJolocomCredentialOfferResponseHandler(BaseHandler):

    def get(self):
        self.process_responsetoken(self.request.body.decode("utf-8"))

    def post(self):
        self.process_responsetoken(self.request.body.decode("utf-8"))

    def process_responsetoken(self, token):
        authn = self.settings['oidc_provider'].authn_broker.get_method("BlockchainAuthMethod")

        rand = self.request.uri.split("/")[-1]

        ssi = authn.ssi['jolocom']
        tk = ssi.receiveCredentialOfferResponse(rand, token)

        self.write(json.dumps(tk))