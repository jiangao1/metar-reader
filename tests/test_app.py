import pytest
import requests as req_lib
from unittest.mock import patch, MagicMock
from app import app as flask_app

SAMPLE_METAR = 'KHIO 131553Z 00000KT 10SM FEW025 17/09 A3001 RMK AO2'


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        yield c


def mock_ok(text):
    m = MagicMock()
    m.text = text
    m.raise_for_status = MagicMock()
    return m


# --- Home page ---

def test_home_returns_200(client):
    assert client.get('/').status_code == 200


# --- Input validation ---

def test_missing_airport_returns_400(client):
    assert client.get('/weather').status_code == 400

def test_empty_airport_returns_400(client):
    assert client.get('/weather?airport=').status_code == 400

def test_code_with_digits_returns_400(client):
    assert client.get('/weather?airport=K1IO').status_code == 400

def test_code_too_long_returns_400(client):
    assert client.get('/weather?airport=TOOLONG').status_code == 400

def test_lowercase_accepted(client):
    with patch('app.requests.get', return_value=mock_ok(SAMPLE_METAR)):
        assert client.get('/weather?airport=khio').status_code == 200


# --- Successful response ---

def test_response_has_summary(client):
    with patch('app.requests.get', return_value=mock_ok(SAMPLE_METAR)):
        data = client.get('/weather?airport=KHIO').get_json()
        assert 'summary' in data and len(data['summary']) > 0

def test_response_has_raw_metar(client):
    with patch('app.requests.get', return_value=mock_ok(SAMPLE_METAR)):
        data = client.get('/weather?airport=KHIO').get_json()
        assert data['raw'] == SAMPLE_METAR

def test_temperature_decoded(client):
    with patch('app.requests.get', return_value=mock_ok(SAMPLE_METAR)):
        data = client.get('/weather?airport=KHIO').get_json()
        assert data['temperature_c'] == 17 and data['temperature_f'] == 63


# --- Error handling ---

def test_empty_api_response_returns_404(client):
    with patch('app.requests.get', return_value=mock_ok('')):
        assert client.get('/weather?airport=XXXX').status_code == 404

def test_timeout_returns_504(client):
    with patch('app.requests.get', side_effect=req_lib.Timeout()):
        assert client.get('/weather?airport=KHIO').status_code == 504

def test_connection_error_returns_500(client):
    with patch('app.requests.get', side_effect=req_lib.RequestException('fail')):
        assert client.get('/weather?airport=KHIO').status_code == 500
