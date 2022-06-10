from base.database.basedb import SSIXADBBase
from base.database.oidcdbobject import OIDCUser, OIDCAttribute

from oic.utils.userinfo import UserInfo

import logging
log = logging.getLogger(__name__)


class UserInfoDB(UserInfo, SSIXADBBase):

    def __init__(self, db, instance=None):
        UserInfo.__init__(self)
        SSIXADBBase.__init__(self, db)
        self.instance = instance

    def __call__(self, userid, client_id, user_info_claims=None, **kwargs):
        try:
            return self.filter(self[userid], user_info_claims)
        except KeyError:
            return {}

    def add_claims(self, uid, claims, client=None):
        log.debug("Uid: " + str(uid))
        log.debug("Claims: " + str(claims))
        assert isinstance(claims, dict)
        s = None

        try:
            s = self.get_session()
            users = s.query(OIDCUser).filter(OIDCUser.username == uid).all()
            if users is not None and len(users) == 1:
                for c in claims:
                    found = False
                    for oidc_a in users[0].attributes:
                        if c == oidc_a.attribute:
                            oidc_a.value = c
                            found  = True
                    if not found:
                        users[0].attributes.append(OIDCAttribute(c,claims[c]))
                s.add(users[0])
            else:
                u = OIDCUser.fromDict(uid, claims, instance=self.instance)
                s.add(u)
            s.commit()
        except Exception as e:
            log.exception("Database commit failed")
        finally:
            if s is not None:
                s.close()

        if client is not None:
            self.add_client_id_to_uid(uid, client)

    def remove_claims(self, uid, claims):
        log.debug("Uid: " + str(uid))
        log.debug("Claims: " + str(claims))
        assert isinstance(claims, dict)
        s = None

        try:
            s = self.get_session()
            users = s.query(OIDCUser).filter(OIDCUser.username == uid).all()
            if users is not None and len(users) == 1:
                for c in claims:
                    users[0].attributes.remove(OIDCAttribute(c, claims[c]))
                s.add(users[0])
                s.commit()
        except Exception as e:
            log.exception("Database commit failed")
        finally:
            if s is not None:
                s.close()

    def uid_for_client_id_exist(self, userid, client_id):
        log.debug("User Id: " + str(userid))
        log.debug("Client Id: " + str(client_id))
        assert userid is not None
        assert client_id is not None

        s = None
        count = 0
        try:
            s = self.get_session()
            users = s.query(OIDCUser).filter(OIDCUser.username == userid).all()
            if users is not None and len(users) > 0:
                for cid in users[0].client_id.split(','):
                    if cid == client_id:
                        count = count + 1
        except Exception as e:
            log.exception("Database query failed")
        finally:
            if s is not None:
                s.close()

        if count > 0:
            log.debug("Result True")
            return True
        else:
            log.debug("Result False")
            return False

    def add_client_id_to_uid(self, uid, client_id):
        log.debug("Uid: " + str(uid))
        log.debug("Client Id: " + str(client_id))
        s = None

        try:
            s = self.get_session()
            users = s.query(OIDCUser).filter(OIDCUser.username == uid).all()
            if users is not None and len(users) == 1:
                cid = users[0].client_id
                if (cid is None) or (client_id not in cid.split(',')):
                    if cid is None:
                        cid = client_id
                    else:
                        cid = cid + "," + client_id
                    users[0].client_id = cid
                    s.add(users[0])
                    s.commit()
        except Exception as e:
            log.exception("Database commit failed")
        finally:
            if s is not None:
                s.close()

    def remove_client_id_from_uid(self, uid, client_id):
        log.debug("Uid: " + str(uid))
        log.debug("Client Id: " + str(client_id))
        s = None

        try:
            s = self.get_session()
            users = s.query(OIDCUser).filter(OIDCUser.username == uid).all()
            if users is not None and len(users) == 1:
                cid = users[0].client_id
                if cid is not None:
                    if (client_id + ',') in cid:
                        cid = cid.replace(client_id + ',','')
                    else:
                        cid = cid.replace(client_id, '')
                    users[0].client_id = cid
                    s.add(users[0])
                    s.commit()
        except Exception as e:
            log.exception("Database commit failed")
        finally:
            if s is not None:
                s.close()

    def cleanup(self):
        log.debug("Database cleanup")
        s = None
        try:
            s = self.get_session()
            users = s.query(OIDCUser).filter(OIDCUser.instance == self.instance).all()
            for u in users:
                for a in u.attributes:
                    s.delete(a)
                s.delete(u)
            s.commit()
        except Exception as e:
            log.exception("Database commit failed")
        finally:
            if s is not None:
                s.close()

    def __getitem__(self, key):
        log.debug("Key: " + str(key))
        s = None
        users = None
        item = None

        try:
            s = self.get_session()
            users = s.query(OIDCUser).filter(OIDCUser.username == key).all()
            if users is not None and len(users) == 1:
                item = users[0].toDict()
            else:
                log.error("User not found.")
        except Exception as e:
            log.exception("Database query failed")
        finally:
            if s is not None:
                s.close()

        log.debug(item)
        return item

    def __setitem__(self, key, value):
        log.debug("Key: " + str(key))
        log.debug("Value: " + str(value))
        assert key is not None
        assert isinstance(value, dict)

        # Set key with value and check if item already exists
        s = None
        try:
            s = self.get_session()
            ex_user = s.query(OIDCUser).filter(OIDCUser.username == key).all()
            if len(ex_user) > 0:
                user = ex_user[0]
                user.attributes = OIDCAttribute.fromDictToListofOIDCAttributes(value)
            else:
                user = OIDCUser.fromDict(key, value, instance=self.instance)
            s.add(user)
            s.commit()
        except Exception as e:
            log.exception("Database commit failed")
        finally:
            if s is not None:
                s.close()

    def __delitem__(self, key):
        log.debug("Key: " + str(key))
        # Remove key from database.
        assert key is not None

        s = None
        try:
            s = self.get_session()
            users = s.query(OIDCUser).filter(OIDCUser.username == key).all()
            if len(users) == 1:
                s.delete(users[0])
            s.commit()
        except Exception as e:
            log.exception("Database commit failed")
        finally:
            if s is not None:
                s.close()

    def __contains__(self, key):
        log.debug("Key: " + str(key))
        # Return True if key is contained in the database.
        assert key is not None

        s = None
        count=0
        try:
            s = self.get_session()
            users = s.query(OIDCUser).filter(OIDCUser.username == key).all()
            count = len(users)
        except Exception as e:
            log.exception("Database query failed")
        finally:
            if s is not None:
                s.close()

        if count > 0:
            log.debug("Result True")
            return True
        else:
            log.debug("Result False")
            return False