import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from utils.remindme_helper import get_remindme_datetime_and_message, TimeFormat


@pytest.fixture
def now():
    return datetime(2024, 10, 10, 12, 0, 0)  # 2024 10 10 12:00


@patch("utils.remindme_helper._check_timeformat_regexes")
def test_invalid_format(mock_check, now):
    mock_check.return_value = TimeFormat.INVALID
    dt, msg = get_remindme_datetime_and_message(now, "???")
    assert dt is None
    assert msg == "Invalid Time Format."


@patch("utils.remindme_helper._check_timeformat_regexes")
def test_number_plus_valid(mock_check, now):
    mock_check.return_value  = TimeFormat.NUMBER  
    dt, msg = get_remindme_datetime_and_message(now, "5", "+", "take", "break")

    assert dt == now + timedelta(minutes=5)
    assert msg == "take break"


@patch("utils.remindme_helper._check_timeformat_regexes")
def test_number_missing_plus(mock_check, now):
    mock_check.return_value  = TimeFormat.NUMBER
    dt, msg = get_remindme_datetime_and_message(now, "5", "notplus")
    assert dt is None
    assert msg == "Invalid time format. Try  `+ <number>.`"


@patch("utils.remindme_helper._check_timeformat_regexes")
def test_non_number_with_plus(mock_check, now):
    mock_check.return_value  = TimeFormat.TIME_ONLY 
    dt, msg = get_remindme_datetime_and_message(now, "12:30", "+", "test")
    assert dt is None
    assert msg == "Invalid time format. Try  `+ <number>.`"


# -------------------------
# TIME ONLY (HH:mm)
# -------------------------

@patch("utils.remindme_helper._check_timeformat_regexes")
def test_time_only_future(mock_check, now):
    mock_check.return_value  = TimeFormat.TIME_ONLY  # mode only
    dt, msg = get_remindme_datetime_and_message(now, "15:30", "meeting")

    assert dt == now.replace(hour=15, minute=30)
    assert msg == "meeting"


@patch("utils.remindme_helper._check_timeformat_regexes")
def test_time_only_next_day(mock_check, now):
    mock_check.return_value  = TimeFormat.TIME_ONLY
    # 10:00 is before now's 12:00 → should roll to next day
    dt, msg = get_remindme_datetime_and_message(now, "10:00", "breakfast")

    assert dt == now.replace(day=11, hour=10, minute=0)
    assert msg == "breakfast"


@patch("utils.remindme_helper._check_timeformat_regexes")
def test_date_only_wrong_second_arg(mock_check, now):
    mock_check.side_effect = [TimeFormat.DATE_ONLY, TimeFormat.INVALID]
    dt, msg = get_remindme_datetime_and_message(now, "2024-05-10", "??")
    assert dt is None
    assert "Invalid time format" in msg


@patch("utils.remindme_helper._check_timeformat_regexes")
def test_full_date_time_valid(mock_check, now):
    mock_check.side_effect = [
        TimeFormat.DATE_ONLY,
        TimeFormat.TIME_ONLY,
        TimeFormat.FULL_DATE_TIME
    ]

    dt, msg = get_remindme_datetime_and_message(
        now,
        "2024-11-10",
        "14:00",
        "doctor",
        "appointment"
    )

    expected = now.replace(year=2024, month=11, day=10, hour=14, minute=0)
    assert dt == expected
    assert msg == "doctor appointment"


@patch("utils.remindme_helper._check_timeformat_regexes")
def test_date_time_no_year_rollover(mock_check, now):
    mock_check.side_effect = [
        TimeFormat.DATE_ONLY,         
        TimeFormat.TIME_ONLY,        
        TimeFormat.DATE_TIME_NO_YEAR  
    ]

    # month/day before Oct 10 → it must roll to next year (2025)
    dt, msg = get_remindme_datetime_and_message(
        now,
        "05-10",
        "10:00",
        "birthday"
    )

    expected = now.replace(year=2025, month=5, day=10, hour=10, minute=0)
    assert dt == expected
    assert msg == "birthday"


# -------------------------
# FALLBACK INVALID
# -------------------------

@patch("utils.remindme_helper._check_timeformat_regexes")
def test_fallback_invalid(mock_check, now):
    mock_check.return_value  = TimeFormat.INVALID  # mode
    dt, msg = get_remindme_datetime_and_message(now, "Something random", "??", "extra")
    assert dt is None
    assert msg == "Invalid Time Format."