from ssixa.base.database.basedb import SSIXADBBase
from ssixa.base.database.oidcdbobject import OIDCSession, OIDCUidToSid
from ssixa.base.database.uid2siddb import UidToSidDB

from oic.utils.sdb import SessionDB as SessionDBBase

import logging
log = logging.getLogger(__name__)


class SessionDB(SessionDBBase, SSIXADBBase):

    def __init__(self, db, base_url, instance=None, refresh_db=None, refresh_token_expires_in=86400,
                 token_factory=None, code_factory=None, refresh_token_factory=None):
        SSIXADBBase.__init__(self, db)
        SessionDBBase.__init__(self, base_url, self, refresh_db, refresh_token_expires_in,
                                    token_factory, code_factory, refresh_token_factory)

        self.instance = instance
        # Overwrite uid2sid store
        self.uid2sid = UidToSidDB(db, self.instance)

    def cleanup(self):
        log.debug("Session DB cleanup")
        s = None
        try:
            s = self.get_session()
            sessions = s.query(OIDCSession).filter(OIDCSession.instance == self.instance).all()
            for u in sessions:
                s.delete(u)
            s.commit()
        except Exception as e:
            log.exception("Database commit failed")
        finally:
            if s is not None:
                s.close()
        self.uid2sid.cleanup()

    def __getitem__(self, key):
        log.debug("Get item from Session DB: "+ str(key))
        s = None
        users = None
        session = None
        item = None

        try:
            s = self.get_session()
            sessions = s.query(OIDCSession).filter(OIDCSession.sid == key).all()
            if sessions is not None and len(sessions) == 1:
                item = sessions[0].toDict()
            else:
                sid = self._get_token_key(key)
                sessions = s.query(OIDCSession).filter(OIDCSession.sid == sid).all()
                if sessions is not None and len(sessions) == 1:
                    item = sessions[0].toDict()
        except Exception as e:
            log.exception("Database query failed")
        finally:
            if s is not None:
                s.close()
        log.debug(str(item))
        return item

    def __setitem__(self, key, value):
        log.debug("Set Key: " + str(key))
        log.debug("Set Value: " + str(value))
        assert key is not None
        assert isinstance(value, dict)

        # Set key with value and check if item already exists
        s = None
        try:
            s = self.get_session()
            ex_session = s.query(OIDCSession).filter(OIDCSession.sid == key).all()
            session = None
            if len(ex_session) > 0:
                session = ex_session[0]
                session.updateFromDict(value)
            else:
                session = OIDCSession.fromDict(key, value, instance=self.instance)
            s.add(session)
            s.commit()
        except Exception as e:
            log.exception("Database commit failed")
        finally:
            if s is not None:
                s.close()

    def __delitem__(self, key):
        log.debug("Delte key: " + str(key))
        # Remove key from database.
        assert key is not None

        s = None
        try:
            s = self.get_session()
            session = s.query(OIDCSession).filter(OIDCSession.sid == key).all()
            if len(session) == 1:
                s.delete(session[0])
            uidtosids = s.query(OIDCUidToSid).filter(OIDCUidToSid.sid == key).all()
            if len(uidtosids) > 0:
                for u2s in uidtosids:
                    s.delete(u2s)
            s.commit()
        except Exception as e:
            log.debug(str(e))
        finally:
            if s is not None:
                s.close()

    def __contains__(self, key):
        log.debug("Contains: " + str(key))
        # Return True if key is contained in the database.
        assert key is not None

        s = None
        count=0
        try:
            s = self.get_session()
            sessions = s.query(OIDCSession).filter(OIDCSession.sid == key).all()
            count = len(sessions)
        except Exception as e:
            log.debug(str(e))
        finally:
            if s is not None:
                s.close()

        if count > 0:
            return True
        else:
            return False

    def get_sids_by_sub(self, sub):
        log.debug("Sub: " + str(sub))
        final_sids = []
        sids = self.uid2sid.values()

        try:
            s = self.get_session()
            sis = s.query(OIDCSession).filter(OIDCSession.sub == sub).all()
            for si in sis:
                if si.sid in sids:
                    final_sids.append(si.sid)
        except Exception as e:
            log.debug(str(e))
        finally:
            if s is not None:
                s.close()
        log.debug("SID list: " + str(final_sids))
        return final_sids

    def get_sids_by_sub_and_client(self, sub, client_id):
        log.debug("Sub: " + str(sub))
        log.debug("Client ID: " + str(client_id))
        final_sids = []
        sids = self.uid2sid.values()

        try:
            s = self.get_session()
            sis = s.query(OIDCSession).filter(OIDCSession.sub == sub and OIDCSession.client_id == client_id).all()
            for si in sis:
                if si.sid in sids:
                    final_sids.append(si.sid)
        except Exception as e:
            log.debug(str(e))
        finally:
            if s is not None:
                s.close()
        log.debug("SID list: " + str(final_sids))
        return final_sids

    def get_sids_by_uid_and_client(self, uid, client_id):
        log.debug("Uid: " + str(uid))
        log.debug("Cient ID: " + str(client_id))
        final_sids = []
        sids = self.uid2sid[uid]

        try:
            s = self.get_session()
            sis = s.query(OIDCSession).filter(OIDCSession.sid.in_(sids) and OIDCSession.client_id == client_id).all()
            for si in sis:
                if si.sid in sids:
                    final_sids.append(si.sid)
        except Exception as e:
            log.debug(str(e))
        finally:
            if s is not None:
                s.close()
        log.debug("SID list: " + str(final_sids))
        return final_sids