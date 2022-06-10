from handlers.base import BaseHandler, BaseWebSocketHandler
from base.oidcprovider import SSIXAOIDCProvider
from base.database.oidcdbobject import OIDCClient
from base.utils import sanitize

import pyqrcode
import io
import json
import logging
import requests

log = logging.getLogger(__name__)

class OIDCBlockchainAuthMehodHandler:
    name = "BlockchainAuthMethod"

class OIDCBlockchainAuthCreateChallengeHandler(BaseHandler, OIDCBlockchainAuthMehodHandler):
    # Initial handler for blockchain auth method
    # Choosable are all SSI solutions with uPort being pre-selected

    def get(self):
        self.call_createchallenge(self.request.query, self.cookies)

    def post(self):
        self.call_createchallenge(self.request.body, self.cookies)

    def call_createchallenge(self, data, cookies):
        authn = self.settings['oidc_provider'].authn_broker.get_method(self.name)
        solutions = authn.get_available_ssi()

        # Get selected SSI from the request data, fall back to default in initial case
        ssi = self.get_argument("ssi","")
        if  ssi == "":
            ssi = authn.get_default_ssi()

        scopes = self.get_query_argument('scope').split(" ")
        claims = SSIXAOIDCProvider.scope2claims(scopes)

        # Get client that redirected to the gateway
        client_id = sanitize(self.get_query_argument('client_id'))

        ret = authn.create_challenge(ssi, claims, client_id)

        qr = pyqrcode.create(ret['challenge'])
        buffer = io.BytesIO()
        qr.svg(buffer, scale=2, background="white", module_color="#000000", xmldecl=False)

        client = None
        if client_id is not None and client_id != "":
            session = None
            try:
                session = self.settings['oidc_provider'].cdb.get_session()
                client = session.query(OIDCClient).filter(OIDCClient.client_id == client_id) \
                    .limit(1) \
                    .all()
            except Exception as e:
                log.debug(str(e))
            finally:
                if session is not None:
                    session.close()
        client_name = ""
        if client is not None:
            client_name = client[0].name

        # Write everything to template
        self.render('blockchain.html',
                qrcode=buffer.getvalue().decode(),
                url=ret['url_poll'],
                rand=ret['random'],
                ssi=ssi,
                solutions=solutions,
                action_verify="{}?{}".format(ret['url_verify'],data),
                client_name=client_name,
                key="")

class OIDCBlockchainAuthVerificationHandler(BaseHandler, OIDCBlockchainAuthMehodHandler):

    def get(self):
        self.call_verification(self.request.query, self.cookies)

    def post(self):
        self.call_verification(self.request.body, self.cookies)

    def call_verification(self, data, cookies):
        authn = self.settings['oidc_provider'].authn_broker.get_method(self.name)

        name = authn.verify(self.get_argument("random"))

        # Get cookie from the OIDC provider and parse it to set it manually with tornado
        _ , cookie_value = authn.create_cookie(name, "auth")
        val = cookie_value.split(";")[0][8:-1]

        self.set_cookie("pyoidc",val)
        self.redirect("{0}?{1}".format("/oidc/authorization",self.request.query))

class OIDCBlockchainAuthSideChannelVerificationHandler(BaseHandler, OIDCBlockchainAuthMehodHandler):

    def get(self):
        self.call_sideverification(self.request.query, self.cookies)

    def post(self):
        self.call_sideverification(self.request.body, self.cookies)

    def call_sideverification(self, data, cookies):
        authn = self.settings['oidc_provider'].authn_broker.get_method(self.name)

        rand = self.request.uri.split("/")[-1]
        authn.verify_sidechannel(rand, json.loads(data.decode("utf-8")))

        # Nothing to return to the smartphone
        self.write("")

class OIDCBlockchainAuthStatusVerificationHandler(BaseWebSocketHandler, OIDCBlockchainAuthMehodHandler):

    def open(self):
        self.settings['oidc_provider'].authn_broker.get_method(self.name).register_statuscallback(self.request.uri.split("/")[-1], self.callback)

    def on_close(self):
        self.settings['oidc_provider'].authn_broker.get_method(self.name).unregister_statuscallback(self.request.uri.split("/")[-1], self.callback)

    def on_message(self, message):
        pass

    def callback(self, result):
        self.write_message(result)

class BlockchainAuthLissiRoutingHandler(BaseHandler, OIDCBlockchainAuthMehodHandler):
    ssi_name = "lissi"

    def get(self):
        url = self.settings['oidc_provider'].authn_broker.get_method(self.name).ssi[self.ssi_name].acapy_inbound_url
        data = self.request.body
        data = data.decode()

        try:
            resp = requests.get(url, data=data)
        except Exception as ex:
            log.info(str(ex))

    def post(self):
        url = self.settings['oidc_provider'].authn_broker.get_method(self.name).ssi[self.ssi_name].acapy_inbound_url
        data = self.request.body
        data = data.decode()

        try:
            resp = requests.post(url, data=data)
        except Exception as ex:
            log.info(str(ex))

class BlockchainAuthLissiWebhookConnectionTopicHandler(BaseHandler, OIDCBlockchainAuthMehodHandler):
    # Class to receive web hooks related to topic connections
    ssi_name = "lissi"

    def get(self):
        pass

    def post(self):
        data = json.loads(self.request.body.decode())

        # Check state of connection handling
        if data['state'] == 'invitation':
            # New connection invitation has been generated by ACA-Py
            # Nothing to react on
            pass
        elif data['state'] == 'request':
            # Other agent has sent a connection request as response to the invitation
            # Nothing to react on
            pass
        elif data['state'] == 'response':
            # ACA-Py has sent a connection response based on the connection request
            # Final state to initiate credential presentation request
            # ToDo provide requested claims
            self.settings['oidc_provider'].authn_broker.get_method(self.name).ssi[self.ssi_name]\
                .retrieve_credentials(data['connection_id'],['email','firstname','name'])
        elif data['state'] == 'active':
            # If other agent sends an ack after the response. This ack is not mandatory
            # and is usually substituted by a subsequent process
            pass
        else:
            pass

class BlockchainAuthLissiWebhookPresentationProofTopicHandler(BaseHandler, OIDCBlockchainAuthMehodHandler):
    # Class to receive web hooks related to topic present_proof
    ssi_name = "lissi"

    def get(self):
        pass

    def post(self):
        data = json.loads(self.request.body.decode())

        # Check state of connection handling
        if data['state'] == 'request_sent':
            # New presentation proof request has been sent via ACA-Py admin interface
            # Nothing to react on
            pass
        elif data['state'] == 'request':
            # Response state
            # ToDo redirect to lissi verify challenge function and parse attributes
            pass
        else:
            pass

class BlockchainAuthLissiWebhookOtherTopicHandler(BaseHandler, OIDCBlockchainAuthMehodHandler):
    # General class to receive non-specific web hooks
    ssi_name = "lissi"

    def get(self):
        test = ""
        pass

    def post(self):
        test = ""
        pass