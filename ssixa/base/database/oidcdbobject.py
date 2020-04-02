from ssixa.base.database import SSIXASQLBaseDBBase

from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, Date, Table, ForeignKey, UniqueConstraint, Boolean

import logging
import datetime

log = logging.getLogger(__name__)

class OIDCClient(SSIXASQLBaseDBBase):
    __tablename__ = 'oidc_client'

    client_id = Column(String, primary_key=True)
    name = Column(String)
    client_secret = Column(String)
    client_salt = Column(String)
    redirect_uris = Column(String)
    token_endpoint_auth_method = Column(String)
    post_logout_redirect_uris = Column(String)
    subject_type = Column(String)

    def __init__(self, client_id, name, client_secret, client_salt, redirect_uris, token_endpoint_auth_method='', post_logout_redirect_uris='', subject_type='pairwise'):
        self.client_id = client_id
        self.name = name
        self.client_secret = client_secret
        self.client_salt = client_salt
        self.redirect_uris = redirect_uris
        self.token_endpoint_auth_method = token_endpoint_auth_method
        self.post_logout_redirect_uris = post_logout_redirect_uris
        self.subject_type = subject_type

    def toDict(self):
        converted_uris = []
        uris = self.redirect_uris.split(";")
        for u in uris:
            converted_uris.append(u.split(','))

        post_converted_uris = []
        post_uris = self.post_logout_redirect_uris.split(";")
        for u in post_uris:
            post_converted_uris.append(u.split(','))

        return dict(client_id=self.client_id,
                    name=self.name,
                    client_secret=self.client_secret,
                    client_salt=self.client_salt,
                    redirect_uris=converted_uris,
                    token_endpoint_auth_method=self.token_endpoint_auth_method,
                    post_logout_redirect_uris=post_converted_uris,
                    subject_type=self.subject_type)

    @staticmethod
    def fromDict(values):
        assert values is not None
        assert isinstance(values, dict)

        uris = ""
        for pair in values['redirect_uris']:
            if len(uris) == 0:
                uris = ",".join(pair)
            else:
                uris = uris + ";" + ",".join(pair)
        post_uris = ""
        for pair in values['post_logout_redirect_uris']:
            if len(post_uris) == 0:
                post_uris = ",".join(pair)
            else:
                post_uris = post_uris + ";" + ",".join(pair)

        client = OIDCClient(values['client_id'], values['name'], values['client_secret'],
                            values['client_salt'], uris,
                            values['token_endpoint_auth_method'], post_uris,
                            values['subject_type'])
        return client

usertoattribute_association = Table(
    'oidc_usertoattribute', SSIXASQLBaseDBBase.metadata,
    Column('oidc_user_id', Integer, ForeignKey('oidc_user.id')),
    Column('oidc_attribute_id', Integer, ForeignKey('oidc_attribute.id')),
    UniqueConstraint('oidc_user_id','oidc_attribute_id',name='oidc_user_attribute_uc')
)

class OIDCUser(SSIXASQLBaseDBBase):
    __tablename__ = 'oidc_user'
    __table_args__ = (
            UniqueConstraint('username','client_id',name='oidc_username_client_id_uc'),
    )

    id = Column(Integer, primary_key=True, unique=True)
    instance = Column(String)
    username = Column(String)
    client_id = Column(String)
    attributes = relationship("OIDCAttribute", secondary=usertoattribute_association)

    def __init__(self, username, client_id=None, instance=None):
        self.username = username
        self.client_id = client_id
        self.instance = instance

    def __eq__(self, other):
        if self.client_id is None and other.client_id is None:
            return self.username == other.username
        else:
            return self.client_id == other.client_id and self.username == other.username

    def __str__(self):
        return self.username

    def __hash__(self):
        if self.client_id is None:
            return hash(self.username)
        else:
            return hash(self.client_id + self.username)

    def toDict(self):
        d = {}
        for a in self.attributes:
            d[a.attribute] = a.value
        return d

    @staticmethod
    def fromDict(username, values, client_id=None, instance=None):
        assert username is not None
        assert isinstance(values, dict)

        user = OIDCUser(username, client_id, instance)
        for a in values:
            user.attributes.append(OIDCAttribute(a,values[a]))
        return user

class OIDCAttribute(SSIXASQLBaseDBBase):
    __tablename__ = 'oidc_attribute'

    id = Column(Integer, primary_key=True, unique=True)
    attribute = Column(String)
    value = Column(String)

    def __init__(self, attribute, value):
        self.attribute = attribute
        self.value = value

    def __eq__(self, other):
        return self.attribute == other.attribute

    def __str__(self):
        return self.attribute

    def __hash__(self):
        return hash(self.attribute)

    @staticmethod
    def fromDictToListofOIDCAttributes(attributes):
        assert isinstance(attributes, dict)

        l = []
        for att in attributes:
            l.append(OIDCAttribute(att,attributes[att]))
        return l

class OIDCSession(SSIXASQLBaseDBBase):
    __tablename__ = 'oidc_session'

    sid = Column(String, primary_key=True, unique=True)
    oauth_state = Column(String)
    code = Column(String)
    code_used = Column(Boolean)
    authzreq = Column(String)
    client_id = Column(String)
    response_type = Column(String) # list
    revoked = Column(Boolean)
    authn_event = Column(String)
    redirect_uri = Column(String)
    scope = Column(String) # list
    sub = Column(String)
    permission = Column(String)
    access_token = Column(String)
    access_token_scope = Column(String)
    token_type = Column(String)
    id_token = Column(String)
    instance = Column(String)

    def __init__(self, sid, oauth_state=None, code=None, code_used=False, authzreq=None, client_id=None,
                 response_type=None, revoked=False, authn_event=None, redirect_uri=None, scope=None,
                 sub=None, permission=None, access_token=None, access_token_scope=None, token_type=None,
                 id_token=None, instance=None):
        self.sid = sid
        self.oauth_state = oauth_state
        self.code = code
        self.code_used = code_used
        self.authzreq = authzreq
        self.client_id = client_id
        if isinstance(response_type, list):
            self.response_type = ",".join(response_type)
        else:
            self.response_type = response_type
        self.revoked = revoked
        self.authn_event = authn_event
        self.redirect_uri = redirect_uri
        if isinstance(response_type, list):
            self.scope = ",".join(scope)
        else:
            self.scope = scope
        self.sub = sub
        self.permission = permission
        self.access_token = access_token
        self.access_token_scope = access_token_scope
        self.token_type = token_type
        self.id_token = id_token
        self.instance = instance

    def __eq__(self, other):
            return self.sid == other.sid

    def __str__(self):
        return self.sid

    def __hash__(self):
        return hash(self.sid)

    def toDict(self):
        return {"oauth_state": self.oauth_state,
             "code": self.code,
             "code_used": self.code_used,
             "authzreq": self.authzreq,
             "client_id": self.client_id,
             "response_type": self.response_type.split(","),
             "revoked": self.revoked,
             "authn_event": self.authn_event,
             "redirect_uri": self.redirect_uri,
             "scope": self.scope.split(","),
             "sub": self.sub,
             "permission": self.permission,
             "access_token": self.access_token,
             "access_token_scope": self.access_token_scope,
             "token_type": self.token_type,
             "id_token": self.id_token}

    @staticmethod
    def fromDict(sid, values, instance=None):

        session = OIDCSession(sid,
                          oauth_state = values["oauth_state"] if "oauth_state" in values else None,
                          code = values["code"] if "code" in values else None,
                          code_used = values["code_used"] if "code_used" in values else False,
                          authzreq = values["authzreq"] if "authzreq" in values else None,
                          client_id = values["client_id"] if "client_id" in values else None,
                          response_type = ",".join(values["response_type"]) if "response_type" in values else None,
                          revoked = values["revoked"] if "revoked" in values else False,
                          authn_event = values["authn_event"] if "authn_event" in values else None,
                          redirect_uri = values["redirect_uri"] if "redirect_uri" in values else None,
                          scope = ",".join(values["scope"]) if "scope" in values else None,
                          sub = values["sub"] if "sub" in values else None,
                          permission = values["permission"] if "permission" in values else None,
                          access_token = values["access_token"] if "access_token" in values else None,
                          access_token_scope = values["access_token_scope"] if "access_token_scope" in values else None,
                          token_type = values["token_type"] if "token_type" in values else None,
                          id_token =values["id_token"] if "id_token" in values else None,
                          instance = instance)

        return session

    def updateFromDict(self, values):
        self.oauth_state = values["oauth_state"] if "oauth_state" in values else None
        self.code = values["code"] if "code" in values else None
        self.code_used = values["code_used"] if "code_used" in values else False
        self.authzreq = values["authzreq"] if "authzreq" in values else None
        self.client_id = values["client_id"] if "client_id" in values else None
        self.response_type = ",".join(values["response_type"]) if "response_type" in values else None
        self.revoked = values["revoked"] if "revoked" in values else False
        self.authn_event = values["authn_event"] if "authn_event" in values else None
        self.redirect_uri = values["redirect_uri"] if "redirect_uri" in values else None
        self.scope = ",".join(values["scope"]) if "scope" in values else None
        self.sub = values["sub"] if "sub" in values else None
        self.permission = values["permission"] if "permission" in values else None
        self.access_token = values["access_token"] if "access_token" in values else None
        self.access_token_scope = values["access_token_scope"] if "access_token_scope" in values else None
        self.token_type = values["token_type"] if "token_type" in values else None
        self.id_token = values["id_token"] if "id_token" in values else None

class OIDCUidToSid(SSIXASQLBaseDBBase):
    __tablename__ = 'oidc_uid2sid'
    __table_args__ = (
            UniqueConstraint('uid','sid',name='oidc_uid_sid_uc'),
    )

    uid = Column(String, primary_key=True)
    sid = Column(String)
    instance = Column(String)

    def __init__(self, uid, sid, instance=None):
        self.uid = uid
        self.sid = sid
        self.instance = instance

    def __eq__(self, other):
            return self.uid == other.uid and self.sid == other.sid

    def __str__(self):
        return "{}:{}".format(self.uid, self.sid)

    def __hash__(self):
        return hash(self.uid + self.sid)