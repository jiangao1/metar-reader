from metar_decoder import decode_metar, build_summary

CLEAR     = 'KHIO 131553Z 00000KT 10SM FEW025 17/09 A3001 RMK AO2'
STORM     = 'KJFK 131551Z 27015G25KT 240V310 2 1/2SM -TSRA BKN030CB OVC060 22/18 A2985'
INTL      = 'EGLL 131550Z 19012KT 9999 SCT025 BKN060 14/10 Q1018'
COLD      = 'KORD 010551Z 32010KT 10SM OVC015 M03/M08 A2991'
FOGGY     = 'KSFO 141056Z 00000KT 1/4SM FG OVC002 12/11 A3002'


def test_station_parsed():
    assert decode_metar(CLEAR)['station'] == 'KHIO'

def test_calm_wind():
    assert decode_metar(CLEAR)['wind'] == 'calm'

def test_temperature_conversion():
    d = decode_metar(CLEAR)
    assert d['temperature_c'] == 17
    assert d['temperature_f'] == 63

def test_negative_temperature():
    d = decode_metar(COLD)
    assert d['temperature_c'] == -3
    assert d['dewpoint_c'] == -8

def test_inhg_altimeter():
    assert decode_metar(CLEAR)['altimeter'] == '30.01 inHg'

def test_hpa_altimeter():
    assert 'hPa' in decode_metar(INTL)['altimeter']

def test_weather_phenomena_decoded():
    d = decode_metar(STORM)
    assert any('rain' in w.lower() for w in d['weather'])

def test_cumulonimbus_flagged():
    d = decode_metar(STORM)
    assert any('cumulonimbus' in c.lower() for c in d['clouds'])

def test_fractional_visibility():
    d = decode_metar(STORM)
    assert d['visibility'] is not None
    assert 'reduced' in d['visibility']

def test_poor_visibility_fog():
    assert 'poor' in decode_metar(FOGGY)['visibility']

def test_fog_phenomenon():
    d = decode_metar(FOGGY)
    assert any('fog' in w.lower() for w in d['weather'])

def test_metar_prefix_stripped():
    assert decode_metar('METAR ' + CLEAR)['station'] == 'KHIO'

def test_wind_variable_range():
    d = decode_metar(STORM)
    assert d['wind_variable'] is not None

def test_summary_contains_temperature():
    d = decode_metar(CLEAR)
    assert '63' in build_summary(d)

def test_summary_contains_calm_wind():
    assert 'calm' in build_summary(decode_metar(CLEAR)).lower()

def test_summary_contains_phenomena():
    assert 'rain' in build_summary(decode_metar(STORM)).lower()
