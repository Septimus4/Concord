# coding: utf-8

from services.topic_service import parse_time_window


def test_parse_time_window_defaults_and_units():
    # Default when None or invalid
    assert parse_time_window(None).total_seconds() == 24 * 3600
    assert parse_time_window("abc").total_seconds() == 24 * 3600

    # Hours
    assert parse_time_window("1h").total_seconds() == 3600
    assert parse_time_window("24h").total_seconds() == 24 * 3600

    # Days
    assert parse_time_window("2d").days == 2

    # Minutes
    assert parse_time_window("30m").total_seconds() == 30 * 60
