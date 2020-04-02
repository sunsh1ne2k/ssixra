from ssixa.base.database.basedb import SSIXADBBase
from ssixa.base.database.basedbobject import BaseStatistic

import logging
log = logging.getLogger(__name__)

class SSIXADB(SSIXADBBase):

    def __init__(self, db):
        super(SSIXADB, self).__init__(db)


class StatisticsLoggerDB(SSIXADBBase):

    def __init__(self, db):
        super(StatisticsLoggerDB, self).__init__(db)

    def cleanup(self):
        s = None
        try:
            s = self._database.get_session()
            stats = s.query(BaseStatistic).filter().all()
            for stat in stats:
                s.delete(stat)
            s.commit()
        except Exception as e:
            log.exception("Database commit failed")
        finally:
            if s is not None:
                s.close()

    def log(self, name, value, application):
        s = None
        try:
            stat = BaseStatistic(name, value, application)
            s = self._database.get_session()
            s.add(stat)
            s.commit()
            log.debug(str(stat))
        except Exception as e:
            log.exception("Database commit failed")
        finally:
            if s is not None:
                s.close()

    def get_logs(self, name, start = None, end = None):
        s = None
        stats = None
        try:
            s = self._database.get_session()
            if start is not None and end is not None:
                stats = s.query(BaseStatistic).filter(BaseStatistic.name == name
                                                  and BaseStatistic.event_time > start
                                                  and BaseStatistic.event_time < end).all()
            elif start is None and end is not None:
                stats = s.query(BaseStatistic).filter(BaseStatistic.name == name
                                                      and BaseStatistic.event_time < end).all()
            elif start is not None and end is None:
                stats = s.query(BaseStatistic).filter(BaseStatistic.name == name
                                                      and BaseStatistic.event_time > start).all()
            else:
                stats = s.query(BaseStatistic).filter(BaseStatistic.name == name).all()
            log.debug(stats)
        except Exception as e:
            log.exception("Database query failed")
        finally:
            if s is not None:
                s.close()

        return stats