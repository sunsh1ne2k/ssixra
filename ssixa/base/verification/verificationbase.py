from queue import Queue
import threading
import time
import logging

log = logging.getLogger(__name__)


class VerificationMethodManager():

    def __init__(self):
        self.verificationmethod_byname = {}
        self.verificationmethod_byclaim = {}

        # Start cleanup background routine
        self.msg = Queue()

    def add_verificationmethod(self, verificationmethod):
        assert isinstance(verificationmethod, VerificationMethodBase)

        self.verificationmethod_byname[verificationmethod.name] = verificationmethod

        if verificationmethod.claim not in self.verificationmethod_byclaim:
            self.verificationmethod_byclaim[verificationmethod.claim] = []
        self.verificationmethod_byclaim[verificationmethod.claim].append(verificationmethod)

    def remove_verificationmethod(self, name):
        v = self.verificationmethod_byname[name]

        for method in self.verificationmethod_byclaim[v.claim]:
            if method.name == v.name:
                self.verificationmethod_byclaim[v.claim].remove(method)
        del self.verificationmethod_byname[name]

    def get_verificationmethod_byname(self, name):
        if name in self.verificationmethod_byname:
            return self.verificationmethod_byname[name]
        else:
            return None

    def get_verificationmethods_byclaim(self, claim):
        if claim in self.verificationmethod_byclaim:
            return self.verificationmethod_byclaim[claim]
        else:
            return []

    def get_verificationmethods(self):
        return self.verificationmethod_byname

    def verificationmethod_count(self, claim=None):
        if claim == None:
            return len(self.verificationmethod_byname)
        else:
            return len(self.verificationmethod_byclaim[claim])

    def start_cleanup(self):
        cleanup_cb = []
        for m in self.verificationmethod_byname:
            cleanup_cb.append(self.verificationmethod_byname[m].cleanExpiredEntries)

        self.cleanup_thread = threading.Thread(target=self.cleanup, args=(cleanup_cb, self.msg))
        self.cleanup_thread.do_run = True
        self.cleanup_thread.daemon = True
        self.cleanup_thread.start()

    def stop(self):
        self.cleanup_thread.do_run = False
        #self.cleanup_thread.join()

    def cleanup(self, callbacks, msg):
        while getattr(self.cleanup_thread, "do_run", True):
            try:
                for cb in callbacks:
                    cb()
                time.sleep(60 * 60)
            except Exception as e:
                msg.put(lambda: self.on_cleanup_error(e))

    def on_cleanup_error(self, exception):
        log.error(str(exception))
        raise exception



class VerificationMethodBase(object):
    name = ""
    display = ""
    claim=""
    description=""

    input=[]

    def __init__(self, baseurl, cfg):
        pass

    def __call__(self, **kwargs):
        # To be implemented for initiating claim verificiation
        raise Exception("Not implemented")

    def verification_completed(self, claim):
        # To be implemented for retrieving a verification result
        raise Exception("Not implemented")

    def get_claim_value(self, username):
        # To be implemented for retrieving verified claim
        raise Exception("Not implemented")

    def propertiesToDict(self):
        res = dict()
        res['name'] = self.name
        res['display'] = self.display
        res['claim'] = self.claim
        res['description'] = self.description
        res['input'] = self.input
        return res

    def cleanExpiredEntries(self):
        # To be implemented as callback for regular cleaning expired entries
        raise Exception("Not implemented")

class DatabaseVerificationBase(VerificationMethodBase):
    pass

class WebServiceVerificationBase(VerificationMethodBase):
    pass


class RequiredClaimMissingException(Exception):
    pass