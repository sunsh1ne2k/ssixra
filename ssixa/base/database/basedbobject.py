from base.database import SSIXASQLBaseDBBase

from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, Date, Table, ForeignKey, UniqueConstraint

import datetime
import logging

log = logging.getLogger(__name__)


class BaseStatistic(SSIXASQLBaseDBBase):
    __tablename__ = 'base_statistic'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    value = Column(String)
    application = Column(String)
    event_time = Column(Date)

    def __init__(self, name, value, application):
        self.name = name
        self.value = value
        self.application = application
        self.event_time = datetime.datetime.now()

    def __str__(self):
        return str(self.event_time) + " " + self.name + ";" + self.value + ";" + self.application