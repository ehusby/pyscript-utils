
import psutils.custom_errors as cerr

import datetime

datetime_date_types = [
    datetime.date,
    datetime.datetime
]


def datetime_to_timestamp(dt):
    dt_type = type(dt)
    if dt_type is datetime.datetime:
        return "{:04}{:02}{:02}_{:02}{:02}{:02}".format(
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second
        )
    elif dt_type is datetime.date:
        return "{:04}{:02}{:02}".format(
            dt.year,
            dt.month,
            dt.day
        )
    else:
        raise cerr.InvalidArgumentError(
            "`dt` type must be one of {}, but was {}".format(
                datetime_date_types, dt_type
            ))

def datetime_to_datestring(dt):
    if type(dt) not in datetime_date_types:
        raise cerr.InvalidArgumentError(
            "`dt` type must be one of {}, but was {}".format(
                datetime_date_types, type(dt)
            )
        )
    return "{:04}-{:02}-{:02}".format(
        dt.year,
        dt.month,
        dt.day
    )

def datetime_to_timestring(dt):
    if type(dt) is not datetime.datetime:
        raise cerr.InvalidArgumentError(
            "`dt` type must be {}, but was {}".format(
                datetime.datetime, type(dt)
            )
        )
    return "{:02}:{:02}:{:02}".format(
        dt.hour,
        dt.minute,
        dt.second
    )
