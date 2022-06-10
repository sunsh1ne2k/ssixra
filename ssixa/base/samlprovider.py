# General imports
from base.blockchain import BlockchainAuthMethod
from base.database.metadatadb import MetaDataStoreDB

from saml2 import BINDING_HTTP_POST
from saml2 import BINDING_HTTP_REDIRECT

from saml2.server import Server as IdPServer
from saml2.config import IdPConfig
from saml2.response import IncorrectlySigned

from saml2.authn_context import AuthnBroker
from saml2.authn_context import UNSPECIFIED
from saml2.authn_context import authn_context_class_ref

from saml2.httputil import BadRequest
from saml2.httputil import Redirect
from saml2.httputil import Response
from saml2.httputil import ServiceError
from saml2.httputil import Unauthorized
from saml2.httputil import get_post
from saml2.httputil import geturl
from saml2.s_utils import UnknownPrincipal
from saml2.s_utils import UnsupportedBinding
from saml2.s_utils import exception_trace
from saml2.s_utils import rndstr
from saml2.sigver import encrypt_cert_from_item
from saml2.sigver import verify_redirect_signature

from saml2.config import Config
from saml2.mdstore import MetadataStore
from saml2.attribute_converter import ac_factory
from saml2.metadata import entity_descriptor, metadata_tostring_fix
from saml2.metadata import entities_descriptor
from saml2.metadata import sign_entity_descriptor
from saml2.sigver import security_context
from saml2.validate import valid_instance

import copy
from hashlib import sha1
import logging

log = logging.getLogger(__name__)

SSIXASAMLProvider_SERVICE_EP = {
        "idp": {
            "endpoints": {
                "single_sign_on_service": [
                    ("/saml/sso/redirect", BINDING_HTTP_REDIRECT),
                    ("/saml/sso/post", BINDING_HTTP_POST)],
                "single_logout_service": [
                    ("/saml/slo/post", BINDING_HTTP_POST),
                    ("/saml/slo/redirect", BINDING_HTTP_REDIRECT)]}}}

class Cache(object):
    def __init__(self):
        self.user2uid = {}
        self.uid2user = {}

class SAMLIdpConfig(IdPConfig):

    def __init__(self, config):
        assert type(config) == dict
        super(SAMLIdpConfig, self).__init__()

        self.create_from_dict(config)
        self.context = "idp"

    def create_from_dict(self, cfg):
        for elem in cfg:
            self.setattr(self.context, elem[0], elem[1])

class SAMLUserInfoDB():

    def __init__(self):
        self.db = {}

    def add_claims(self, uid, claims, client=None):

        if uid not in self.db:
            cl = copy.deepcopy(claims)
            self.db[uid] = cl
        else:
            self.db[uid].update(claims)

    def __get__(self, uid):
        return self.db[uid]

    def __getitem__(self, uid):
        return self.db[uid]


class SSIXASAMLProvider(IdPServer):

    def __init__(self, config):
        baseurl = config['protocol'] + "://" + config['url']
        log.info("Application baseurl: " + baseurl)

        # Update URLs with base
        for pro in SSIXASAMLProvider_SERVICE_EP:
            for serv in SSIXASAMLProvider_SERVICE_EP[pro]['endpoints']:
                if 'service' in serv:
                    for ep in SSIXASAMLProvider_SERVICE_EP[pro]['endpoints'][serv]:
                        SSIXASAMLProvider_SERVICE_EP[pro]['endpoints'][serv][0] = baseurl + ep[0]

        # Update SAML config
        config['saml_config'].update({'service': SSIXASAMLProvider_SERVICE_EP})
        cfg = SAMLIdpConfig(config['saml_config'])

        # Create SAML IdP server - Init super class after config preparation
        super(SSIXASAMLProvider,self).__init__(config=cfg, cache=Cache())

        # Add authn broker
        self.authn_broker = AuthnBroker()
        self.userinfodb = SAMLUserInfoDB()
        i = BlockchainAuthMethod(baseurl+ "/saml", config['proxymode'], config, self.userinfodb, config['trustmodel'])
        self.authn_broker.add(authn_context_class_ref(UNSPECIFIED), i, 3, {i.acr})

        # Add attribute converters
        self.config.attribute_converters = ac_factory()

        # Add metadata
        self.metadata = self.create_metadata(config['saml_config']['metadata'])

        # Response bindings that are offered
        self.response_bindings = [BINDING_HTTP_POST, BINDING_HTTP_REDIRECT]

        # Default claims
        self.defaul_claims = copy.deepcopy(config['saml_config']['default_claims'])

    def create_metadata(self, metadata):

        # For database implementation
        #mds = MetaDataStoreDB(db, self.config.attribute_converters, self.config)
        #mds.load_from_database()

        mds = MetadataStore(self.config.attribute_converters, self.config)
        mds.imp(metadata)

        return mds

    def store_request(self, msg):
        log.debug("Message: " + str(msg))

        key = sha1(msg["SAMLRequest"].encode()).hexdigest()
        log.debug("Key: " + str(key))

        self.ticket[key] = msg
        return key

    def get_entityid_fromkey(self, key):
        log.debug("Key: " + str(key))

        msg = self.ticket[key]
        req = self.parse_authn_request(msg["SAMLRequest"])
        return req.message.issuer.text

    def get_claims_forkey(self, key):
        # ToDo entity specific claim retrieval
        return self.defaul_claims

    def sso_redirect_or_post(self, request, binding):
        assert type(request) == dict

        if "key" in request:
            msg = self.ticket[request["key"]]

            req = self.parse_authn_request(msg["SAMLRequest"], binding)
            del self.ticket[request["key"]]

            if req.message.force_authn is not None and req.message.force_authn.lower() == "true":
                key = self.store_request(msg)

                auth_info = self.authn_broker.pick(req.requested_authn_context)
                if len(auth_info) > 0:
                    method, reference = auth_info[0]
                    return method(key=key)
                else:
                    log.debug("No authentication method found")
                    return Unauthorized("No usable authentication method")

            return self.sso_operation(msg, binding, uid=request["pysaml"])
        else:
            req_info = self.parse_authn_request(request["SAMLRequest"], binding)
            req = req_info.message

            key = self.store_request(request)

            auth_info = self.authn_broker.pick(req.requested_authn_context)

            if len(auth_info) > 0:
                method, reference = auth_info[0]
                log.debug("Authn chosen: " + str(method.acr))
                return method(key=key)
            else:
                log.debug("No authentication method found")
                return Unauthorized("No authentication method found")

    def sso_operation(self, msg, binding, uid=None):
        log.debug("Msg: " + str(msg))
        log.debug("Inbound binding: " + str(binding))

        if not (msg and "SAMLRequest" in msg):
            return BadRequest("Error parsing request or no request")
        else:
            if "Signature" in msg:
                try:
                    kwargs = {"signature": msg["Signature"], "sigalg": msg["SigAlg"]}
                except KeyError:
                    return BadRequest("Signature Algorithm specification is missing")
            else:
                kwargs = {}

            try:
                kwargs["encrypt_cert"] = encrypt_cert_from_item(msg["req_info"].message)
            except KeyError:
                pass

            try:
                kwargs["relay_state"] = msg["RelayState"]
            except KeyError:
                pass

            if not uid is None:
                kwargs["uid"] = uid

            return self.do(msg["SAMLRequest"], binding, **kwargs)

    def do(self, query, binding_in, relay_state="", encrypt_cert=None, **kwargs):
        log.debug("Query: " + str(query))
        log.debug("Inbound binding: " + str(binding_in))
        log.debug("Relay state: " + str(relay_state))
        log.debug("Encrypt_cert: " + str(encrypt_cert))
        log.debug("Kwargs: " + str(kwargs))

        try:
            resp_args = self.verify_request(query, binding_in)
        except Exception as excp:
            log.exception("SSO request verification failed.")
            return ServiceError("Request verification failed.")

        # Get user data
        try:
            userid=self.cache.uid2user[kwargs["uid"]]
            identity = self.userinfodb[userid]
            log.debug("Identity: " + str(identity))
        except Exception as excp:
            log.exception("Identity attributes retrieval failed")
            return ServiceError("Exception occurred")

        try:
            method = self.authn_broker.pick()[0]
            resp_args["authn"] = dict(blockchain=method)
            resp = self.create_authn_response(identity, userid=userid, encrypt_cert_assertion=encrypt_cert, **resp_args)
        except Exception as excp:
            log.exception("User data retrieval failed")
            return ServiceError("Exception occurred")

        kwargs = {}

        binding_out=resp_args['binding']
        destination=resp_args['destination']

        http_args = self.apply_binding(binding_out, "%s" % resp, destination, relay_state, response=True, **kwargs)
        return Response(http_args)

    def verify_request(self, query, binding):
        log.debug("Query: " + str(query))
        log.debug("Binding: " + str(binding))

        request = self.parse_authn_request(query, binding)

        authn_request = None
        if not request is None:
            authn_request = request.message

        resp_args = self.response_args(authn_request)
        log.debug("Response arguments: " + str(resp_args))

        return resp_args

    def slo_redirect_or_post(self, query, binding):
        log.debug("Query: " + query)
        log.debug("Binding: " + binding)

        try:
            req_info = self.parse_logout_request(query, binding)
        except Exception as exc:
            log.exception("Message parsing failed.")
            return BadRequest("Message parsing failed")

        msg = req_info.message
        if msg.name_id:
            lid = self.ident.find_local_id(msg.name_id)
            if lid in self.cache.user2uid:
                uid = self.cache.user2uid[lid]
                if uid in self.cache.uid2user:
                    del self.cache.uid2user[uid]
                del self.cache.user2uid[lid]
            try:
                self.session_db.remove_authn_statements(msg.name_id)
            except KeyError as exc:
                log.exception("Session removal failed")

        resp = self.create_logout_response(msg, [binding])

        binding, destination = self.pick_binding("single_logout_service", [binding], "spsso", req_info)
        response = True

        try:
            hinfo = self.apply_binding(binding, "%s" % resp, destination, query['relay_state'], response=response)
        except Exception as exc:
            log.exception("ServiceError: %s", exc)
            return ServiceError("%s" % exc)

        if binding == BINDING_HTTP_REDIRECT:
            for key, value in hinfo["headers"]:
                if key.lower() == "location":
                    return Redirect(value, headers=hinfo["headers"])

            return ServiceError("missing Location header")
        else:
            return Response(hinfo["data"], headers=hinfo["headers"])

    def stop(self):
        pass

EXTRA_SCOPES = {'name': ['name', 'name_unverified'],
                'avatar': ['avatar', 'avatar_unverified'],
                'firstname': ['firstname', 'firstname_unverified'],
                'lastname': ['lastname', 'lastname_unverified'],
                'ssi': ['ssi'],
                'did':['did'],
                'id':['id']}