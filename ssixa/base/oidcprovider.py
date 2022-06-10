# General imports
from oic.oic import rndstr
from oic.oic.provider import Provider
from oic.utils.authn.authn_context import AuthnBroker
from oic.utils.authn.client import verify_client
from oic.utils.authz import AuthzHandling
from oic.utils.keyio import keyjar_init
from oic.oic.message import SCOPE2CLAIMS
from oic.oic import scope2claims
from oic.utils.sdb import DefaultToken
from oic.oauth2 import redirect_authz_error
from oic.oauth2.message import Message
from oic.utils.authn.user import NoSuchAuthentication
from oic.utils.authn.user import TamperAllert
from oic.utils.authn.user import ToOld
from oic.utils.sdb import AuthnEvent
from oic.oauth2.provider import max_age
from oic.oauth2.provider import re_authenticate
from oic.oic.message import EndSessionRequest
from oic.utils.sanitize import sanitize
from oic.oauth2 import error_response
from oic.oic.message import OpenIDRequest
from oic.utils.http_util import Response
from oic.utils.http_util import SeeOther

from base.database.clientdb import ClientDB
from base.database.userinfodb import UserInfoDB
from base.database.sessiondb import SessionDB
from base.blockchain import BlockchainAuthMethod

import base64
import logging

log = logging.getLogger(__name__)


EXTRA_SCOPES = {'name': ['name', 'name_unverified'],
                'avatar': ['avatar', 'avatar_unverified'],
                'firstname': ['firstname', 'firstname_unverified'],
                'lastname': ['lastname', 'lastname_unverified'],
                'ssi': ['ssi'],
                'did':['did'],
                'id':['id']}

class SSIXAOIDCProvider(Provider):

    def __init__(self, config):

        # Statistics Logger
        self.statlogger = config['statlogger']

        # BaseURL
        baseurl = config['protocol'] + "://" + config['url']
        log.info("Application baseurl: " + baseurl)

        # Set instance identifier
        self.instance = base64.b64encode(baseurl.encode('utf-8')).decode()

        # Client database
        self.cdb = ClientDB(config['source_db'])

        # User info db
        userinfodb = UserInfoDB(config['source_db'], self.instance)

        # AuthnBroker
        authn = AuthnBroker()
        authn.add(BlockchainAuthMethod.acr, BlockchainAuthMethod(baseurl + "/oidc", config['proxymode'], config, userinfodb, config['trustmodel']))

        super(SSIXAOIDCProvider, self).__init__(
            baseurl,
            self.setup_sessiondb(config['source_db'],
                              baseurl,
                              secret=config['oidc_config']['token_secret'],
                              password=config['oidc_config']['token_password'],
                              token_expires_in=config['oidc_config']['token_lifetime'],
                              refresh_token_expires_in=config['oidc_config']['token_refresh_time']),
            self.cdb,
            authn,
            userinfodb,
            AuthzHandling(),
            verify_client,
            verify_ssl=config['oidc_config']['verify_ssl'],
            extra_scope_dict=EXTRA_SCOPES)
        self.symkey=rndstr(16)
        self.baseurl = baseurl
        self.jwks_uri = "{}/{}".format(self.baseurl, config['oidc_config']['jwks']['name'])

        keyjar_init(self, config['oidc_config']['jwks']['keys'])


    def setup_sessiondb(self, db, base_url, secret, password, token_expires_in=3600, grant_expires_in=600,
                      refresh_token_expires_in=86400):

        code_factory = DefaultToken(secret, password, typ='A', lifetime = grant_expires_in)
        token_factory = DefaultToken(secret, password, typ='T', lifetime = token_expires_in)

        sdb = SessionDB(
            db,
            base_url,
            instance=self.instance,
            refresh_db=None,
            code_factory=code_factory,
            token_factory=token_factory,
            refresh_token_expires_in=refresh_token_expires_in,
            refresh_token_factory=None)
        return sdb

    def stop(self):
        # Delete userinfo/sdb entries that belong to the instance
        self.userinfo.cleanup()
        self.sdb.cleanup()

    @staticmethod
    def scope2claims(scopesandclaims):
        scopes = []
        # Split scopes and claims
        for el in scopesandclaims:
            if el in SCOPE2CLAIMS:
                scopes.append(el)
                scopesandclaims.remove(el)
        # Translate standard scopes to claims
        claims = list(scope2claims(scopes).keys())

        # Return both
        return scopesandclaims + claims

    def do_auth(self, areq, redirect_uri, cinfo, request, cookie, **kwargs):

        acrs = self._acr_claims(areq)
        if acrs:
            # If acr claims are present the picked acr value MUST match
            # one of the given
            tup = (None, None)
            for acr in acrs:
                res = self.authn_broker.pick(acr, "exact")
                log.debug("Picked AuthN broker for ACR %s: %s" % (
                    str(acr), str(res)))
                if res:  # Return the best guess by pick.
                    tup = res[0]
                    break
            authn, authn_class_ref = tup
        else:
            authn, authn_class_ref = self.pick_auth(areq)
            if not authn:
                authn, authn_class_ref = self.pick_auth(areq, "better")
                if not authn:
                    authn, authn_class_ref = self.pick_auth(areq, "any")

        if authn is None:
            return redirect_authz_error("access_denied", redirect_uri,
                                        return_type=areq["response_type"])

        try:
            try:
                _auth_info = kwargs["authn"]
            except KeyError:
                _auth_info = ""

            if "upm_answer" in areq and areq["upm_answer"] == "true":
                _max_age = 0
            else:
                _max_age = max_age(areq)

            identity, _ts = authn.authenticated_as(
                cookie, authorization=_auth_info, max_age=_max_age)
        except (NoSuchAuthentication, TamperAllert):
            identity = None
            _ts = 0
        except ToOld:
            log.info("Too old authentication")
            identity = None
            _ts = 0
        else:
            log.info("No active authentication")

        # gather information to be used by the authentication method
        authn_args = {"authn_class_ref": authn_class_ref}
        # Can't be something like JSON because it can't contain '"'
        if isinstance(request, Message):
            authn_args["query"] = request.to_urlencoded()
        elif isinstance(request, dict):
            authn_args["query"] = Message(**request).to_urlencoded()
        else:
            authn_args["query"] = request

        if "req_user" in kwargs:
            authn_args["as_user"] = kwargs["req_user"],

        for attr in ["policy_uri", "logo_uri", "tos_uri"]:
            try:
                authn_args[attr] = cinfo[attr]
            except KeyError:
                pass

        for attr in ["ui_locales", "acr_values"]:
            try:
                authn_args[attr] = areq[attr]
            except KeyError:
                pass

        # To authenticate or Not
        if identity is None or not (self.userinfo.uid_for_client_id_exist(identity['uid'],cinfo['client_id'])):  # No!
            if "prompt" in areq and "none" in areq["prompt"]:
                # Need to authenticate but not allowed
                return redirect_authz_error(
                    "login_required", redirect_uri,
                    return_type=areq["response_type"])
            else:
                return authn(**authn_args)
        else:
            if re_authenticate(areq, authn):
                # demand re-authentication
                return authn(**authn_args)
            else:
                # I get back a dictionary
                user = identity["uid"]
                if "req_user" in kwargs:
                    sids_for_sub = self.sdb.get_sids_by_sub_and_client(kwargs["req_user"], cinfo["client_id"])

                    if sids_for_sub and user != self.sdb.get_authentication_event(sids_for_sub[-1]).uid:
                        log.debug("Wanted to be someone else!")
                        if "prompt" in areq and "none" in areq["prompt"]:
                            # Need to authenticate but not allowed
                            return redirect_authz_error("login_required",
                                                        redirect_uri)
                        else:
                            return authn(**authn_args)



        authn_event = AuthnEvent(identity["uid"], identity.get('salt', ''),
                                 authn_info=authn_class_ref,
                                 time_stamp=_ts)

        return {"authn_event": authn_event, "identity": identity, "user": user}

    def end_session_endpoint(self, request="", cookie=None, **kwargs):
        esr = EndSessionRequest().from_urlencoded(request)

        log.debug("End session request: {}".format(sanitize(esr.to_dict())))

        redirect_uri = None
        if "post_logout_redirect_uri" in esr:
            redirect_uri = self.verify_post_logout_redirect_uri(esr, cookie)
            if not redirect_uri:
                msg = "Post logout redirect URI verification failed!"
                return error_response("%s", msg)

        authn, acr = self.pick_auth(esr)

        sid = None
        if "id_token_hint" in esr:
            id_token_hint = OpenIDRequest().from_jwt(esr["id_token_hint"],
                                                     keyjar=self.keyjar,
                                                     verify=True)
            sub = id_token_hint["sub"]
            try:
                # any sid will do, choose the first
                sid = self.sdb.get_sids_by_sub_and_client(sub, esr["client_id"])[0]
            except IndexError:
                pass
        else:
            identity, _ts = authn.authenticated_as(cookie)
            if identity:
                uid = identity["uid"]
                try:
                    # any sid will do, choose the first
                    sid = self.sdb.uid2sid[uid][0]
                except (KeyError, IndexError):
                    pass
            else:
                msg = "Not allowed: UID could not be retrieved"
                return error_response("%s", msg)

        if sid is not None:
            del self.sdb[sid]

        # Delete cookies
        headers = [authn.delete_cookie(), self.delete_session_cookie()]

        if redirect_uri is not None:
            return SeeOther(str(redirect_uri), headers=headers)

        return Response("Successful logout", headers=headers)