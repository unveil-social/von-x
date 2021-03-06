import time
import datetime
from uuid import uuid4
from random import randrange


def uuid() -> str:
    """
    Generate a unique ID
    """
    return str(uuid4())


def pst():
    return '%d%d%d%d%d %d%d%d%d' % tuple(randrange(10) for i in range(9))


def now():
    """
    Get the current time as the number of seconds since the epoch
    """
    return int(time.mktime(
        datetime.datetime.now().timetuple()
    ))


def one_year():
    """
    Get the time for a year from now, as the number of seconds since the epoch
    """
    return int(time.mktime(
        (datetime.datetime.now() + datetime.timedelta(days=365)).timetuple()
    ))
