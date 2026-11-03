from unittest.mock import MagicMock, patch

import requests

import worker


def test_check_url_up():
    fake = MagicMock(status_code=200)
    with patch("worker.requests.get", return_value=fake):
        code, latency, ok = worker.check_url("https://example.com")
    assert code == 200 and ok is True and latency >= 0


def test_check_url_server_error_is_down():
    fake = MagicMock(status_code=503)
    with patch("worker.requests.get", return_value=fake):
        code, _, ok = worker.check_url("https://example.com")
    assert code == 503 and ok is False


def test_check_url_connection_error_is_down():
    with patch("worker.requests.get",
               side_effect=requests.ConnectionError()):
        code, _, ok = worker.check_url("https://down.example")
    assert code is None and ok is False
