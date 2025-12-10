from datetime import datetime, timedelta
from enum import Enum, auto
import re
from typing import Optional

class TimeFormat(Enum):
    FULL_DATE_TIME = auto()         # yyyy-mm-dd HH:MM
    DATE_TIME_NO_YEAR = auto()      # mm-dd HH:MM
    DATE_ONLY = auto()              # yyyy-mm-dd or mm-dd
    TIME_ONLY = auto()              # HH:MM
    NUMBER = auto()                 # integer
    INVALID = auto()

def get_remindme_datetime_and_message(nowtime: datetime, *args) -> tuple[Optional[datetime], str]:

    mode = args[0]
    regex_res_mode = _check_timeformat_regexes(mode)

    if regex_res_mode == TimeFormat.INVALID:
        return (None, "Invalid Time Format.")

    #1 - ('some number', '+', 'msg1', 'msg2' etc)
    if(regex_res_mode == TimeFormat.NUMBER and args[1] != "+" or regex_res_mode != TimeFormat.NUMBER and args[1] == "+"):
         return (None, "Invalid time format. Try  `+ <number>.`")
    
    if(regex_res_mode == TimeFormat.NUMBER and args[1] == "+"):
        message_to_send = ' '.join(args[1:])
        message_to_send = message_to_send[2:]  # cuts the "+"
        minutes = int(mode)
        return (nowtime + timedelta(minutes=minutes), message_to_send)
    
    #2 - ('20:30', 'msg1', 'msg2' etc)
    if(regex_res_mode == TimeFormat.TIME_ONLY):
        message_to_send = ' '.join(args[1:])
        hour, minute = map(int, mode.split(":"))
        target_time = nowtime.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target_time <= nowtime:
            target_time = target_time + timedelta(days=1)
        return (target_time, message_to_send)
    
    time_element = args[1]
    regex_res_time = _check_timeformat_regexes(time_element)

    #3 - ('1999-01-01', '20:30', 'msg1', 'msg2' etc)
    if(regex_res_mode == TimeFormat.DATE_ONLY and regex_res_time != TimeFormat.TIME_ONLY):
        return None, "Invalid time format. Try  `YYYY-MM-DD HH:mm or MM-DD HH:mm`"
    
    if(regex_res_mode == TimeFormat.DATE_ONLY and regex_res_time == TimeFormat.TIME_ONLY):
        message_to_send = ' '.join(args[2:])
        date_time = mode + " " + time_element
        hour, minute = map(int, time_element.split(":"))
        #either FULL_DATE_TIME or DATE_TIME_NO_YEAR
        datetime_regex = _check_timeformat_regexes(date_time)

        target_time = nowtime
        if datetime_regex == TimeFormat.FULL_DATE_TIME:
            year, month, day = map(int, mode.split("-"))
            target_time = nowtime.replace(year=year, month=month, day=day, hour=hour, minute=minute)
        elif datetime_regex == TimeFormat.DATE_TIME_NO_YEAR:
            month, day = map(int, mode.split("-"))
            target_time = nowtime.replace(month=month, day=day, hour=hour, minute=minute)

        if target_time <= nowtime:
            target_time = target_time.replace(year=target_time.year + 1)

        return (target_time, message_to_send)
    
    return (None, "Invalid Time Format.")
    

def _check_timeformat_regexes(time: str) -> TimeFormat:

        if re.match(r'([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))\s((0[0-9]|1[0-9]|2[0-4]):[0-5][0-9])', time):
            return TimeFormat.FULL_DATE_TIME

        elif re.match(r'((0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))\s((0[0-9]|1[0-9]|2[0-4]):[0-5][0-9])', time):
            return TimeFormat.DATE_TIME_NO_YEAR

        elif re.match(r'(([12]\d{3}-)?(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))', time):
            return TimeFormat.DATE_ONLY

        elif re.match(r'^[0-2]?[0-9]:[0-5][0-9]$', time):
            return TimeFormat.TIME_ONLY

        elif re.match(r'^[1-9][0-9]{0,3}$', time):
            return TimeFormat.NUMBER

        return TimeFormat.INVALID