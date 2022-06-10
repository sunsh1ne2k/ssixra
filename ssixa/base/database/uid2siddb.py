from base.database.basedb import SSIXADBBase
from base.database.oidcdbobject import OIDCUidToSid

import logging
log = logging.getLogger(__name__)

class UidToSidDB(SSIXADBBase):

    def __init__(self, db, instance):
        SSIXADBBase.__init__(self, db)
        self.instance = instance

    def cleanup(self):
        log.debug("UidToSidDB cleanup")
        s = None

        try:
            s = self.get_session()
            uid2sids = s.query(OIDCUidToSid).filter(OIDCUidToSid.instance == self.instance)
            for u2s in uid2sids:
                s.delete(u2s)
            s.commit()
        except Exception as e:
            log.exception("Commit to database failed")
        finally:
            if s is not None:
                s.close()

    def __getitem__(self, uid):
        log.debug("Uid: " + str(uid))
        s = None
        uid2sids = None
        item = []

        try:
            s = self.get_session()
            uid2sids = s.query(OIDCUidToSid).filter(OIDCUidToSid.uid == uid).all()
            if uid2sids is not None and len(uid2sids) > 0:
                for e in uid2sids:
                    item.append(e.sid)
        except Exception as e:
            log.exception("Database query failed")
        finally:
            if s is not None:
                s.close()
        log.debug(str(item))
        return item

    def __setitem__(self, uid, sid):
        log.debug("Uid: " + str(uid))
        log.debug("Sid: " + str(sid))
        assert uid is not None
        assert sid is not None

        if isinstance(sid,list) and len(sid) == 1:
            sid = sid[0]

        # Set key with value and check if item already exists
        s = None
        try:
            s = self.get_session()
            ex_uid2sid = s.query(OIDCUidToSid).filter(OIDCUidToSid.uid == uid and OIDCUidToSid.sid == sid).all()
            if len(ex_uid2sid) > 0:
                log.debug("uid2sid combination already exists")
            else:
                s.add(OIDCUidToSid(uid,sid, self.instance))
                s.commit()
        except Exception as e:
            log.exception("Database commit failed")
        finally:
            if s is not None:
                s.close()

    def __delitem__(self, uid, sid=None):
        log.debug("Uid: " + str(uid))
        log.debug("Sid: " + str(sid))
        # Remove key from database.
        assert uid is not None

        s = None
        try:
            s = self.get_session()
            uid2sids = s.query(OIDCUidToSid).filter(OIDCUidToSid.uid == uid and OIDCUidToSid.sid == sid).all()
            if uid2sids is not None and len(uid2sids) > 0:
                for e in uid2sids:
                    s.delete(e)
            s.commit()
        except Exception as e:
            log.exception("Database commit failed")
        finally:
            if s is not None:
                s.close()

    def values(self):
        sids = []
        s = None
        try:
            s = self.get_session()
            uid2sids = s.query(OIDCUidToSid).filter().all()
            if uid2sids is not None and len(uid2sids) > 0:
                for e in uid2sids:
                    sids.append(e.sid)
        except Exception as e:
            log.exception("Database query failed")
        finally:
            if s is not None:
                s.close()
        log.debug(str(sids))
        return sids

    def items(self):
        kv = []

        s = None
        try:
            s = self.get_session()
            uid2sids = s.query(OIDCUidToSid).filter().all()
            if uid2sids is not None and len(uid2sids) > 0:
                for e in uid2sids:
                    kv.append((e.uid,e.sid))
        except Exception as e:
            log.exception("Database query failed")
        finally:
            if s is not None:
                s.close()
        log.debug(str(kv))
        return kv