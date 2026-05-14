import re

WIND_DIRECTIONS = [
    'N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
    'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'
]

WEATHER_DESCRIPTOR = {
    'MI': 'shallow', 'PR': 'partial', 'BC': 'patches of',
    'DR': 'low drifting', 'BL': 'blowing', 'SH': 'showers of',
    'TS': 'thunderstorm with', 'FZ': 'freezing',
}

WEATHER_PRECIP = {
    'DZ': 'drizzle', 'RA': 'rain', 'SN': 'snow', 'SG': 'snow grains',
    'IC': 'ice crystals', 'PL': 'ice pellets', 'GR': 'hail',
    'GS': 'small hail', 'UP': 'unknown precipitation',
}

WEATHER_OBSCURATION = {
    'BR': 'mist', 'FG': 'fog', 'FU': 'smoke', 'VA': 'volcanic ash',
    'DU': 'dust', 'SA': 'sand', 'HZ': 'haze', 'PY': 'spray',
}

WEATHER_OTHER = {
    'PO': 'dust/sand whirls', 'SQ': 'squalls',
    'FC': 'tornado/waterspout', 'SS': 'sandstorm', 'DS': 'dust storm',
}

CLOUD_COVERAGE = {
    'SKC': 'clear skies', 'CLR': 'clear skies',
    'NSC': 'no significant clouds', 'NCD': 'no clouds detected',
    'FEW': 'a few clouds', 'SCT': 'scattered clouds',
    'BKN': 'broken cloud layer', 'OVC': 'overcast',
    'VV': 'sky obscured, vertical visibility',
}

ALL_WEATHER_STARTS = (
    set(WEATHER_DESCRIPTOR) | set(WEATHER_PRECIP) |
    set(WEATHER_OBSCURATION) | set(WEATHER_OTHER)
)


def degrees_to_compass(degrees):
    return WIND_DIRECTIONS[round(degrees / 22.5) % 16]


def c_to_f(celsius):
    return round(celsius * 9 / 5 + 32)


def knots_to_mph(knots):
    return round(knots * 1.15078)


def parse_fraction(s):
    if not s:
        return None
    if '/' in s:
        parts = s.split('/')
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            return int(parts[0]) / int(parts[1])
        return None
    try:
        return float(s)
    except ValueError:
        return None


def decode_temp_val(s):
    if not s or s == 'XX':
        return None
    negative = s.startswith('M')
    try:
        val = int(s[1:] if negative else s)
        return -val if negative else val
    except ValueError:
        return None


def decode_wind(wind_str):
    m = re.match(r'^(VRB|\d{3})(\d{2,3})(?:G(\d{2,3}))?(KT|MPS|KMH)$', wind_str)
    if not m:
        return wind_str

    direction, speed_s, gust_s, unit = m.groups()
    speed = int(speed_s)
    gust = int(gust_s) if gust_s else None

    if unit == 'KT':
        speed_disp = knots_to_mph(speed)
        gust_disp = knots_to_mph(gust) if gust else None
        unit_label = 'knots'
        disp_unit = 'mph'
    elif unit == 'MPS':
        speed_disp = round(speed * 2.237)
        gust_disp = round(gust * 2.237) if gust else None
        unit_label = 'm/s'
        disp_unit = 'mph'
    else:
        speed_disp = round(speed * 0.621371)
        gust_disp = round(gust * 0.621371) if gust else None
        unit_label = 'km/h'
        disp_unit = 'mph'

    if speed == 0 and direction == '000':
        return 'calm'

    if direction == 'VRB':
        dir_text = 'from a variable direction'
    else:
        deg = int(direction)
        compass = degrees_to_compass(deg)
        dir_text = f'from the {compass} ({deg}°)'

    text = f'{speed_disp} {disp_unit} ({speed} {unit_label}) {dir_text}'
    if gust_disp:
        text += f', gusting to {gust_disp} {disp_unit} ({gust} {unit_label})'
    return text


def format_visibility_miles(miles, prefix=''):
    if miles >= 10:
        label = 'excellent'
        fmt = f'{miles:.0f} miles'
    elif miles >= 5:
        label = 'good'
        fmt = f'{miles:.1f}'.rstrip('0').rstrip('.') + ' miles'
    elif miles >= 1:
        label = 'reduced'
        fmt = f'{miles:.2f}'.rstrip('0').rstrip('.') + ' miles'
    else:
        label = 'poor'
        if miles == 0.75:
            fmt = '3/4 mile'
        elif miles == 0.5:
            fmt = '1/2 mile'
        elif miles == 0.25:
            fmt = '1/4 mile'
        else:
            fmt = f'{miles:.2f}'.rstrip('0').rstrip('.') + ' miles'
    return f'{prefix}{fmt} ({label} visibility)'


def decode_visibility(tokens, idx):
    if idx >= len(tokens):
        return None
    part = tokens[idx]

    if part == 'CAVOK':
        return 'more than 10 km — ceiling and visibility OK', 1

    # International: 4-digit meters
    if re.match(r'^\d{4}$', part):
        meters = int(part)
        if meters >= 9999:
            return 'more than 10 km (excellent)', 1
        elif meters == 0:
            return 'near zero', 1
        return f'{meters} meters', 1

    # Statute miles (single token: 10SM, 3/4SM, M1/4SM, P6SM)
    if part.endswith('SM'):
        vis_str = part[:-2]
        less_than = greater_than = False
        if vis_str.startswith('M'):
            less_than = True
            vis_str = vis_str[1:]
        elif vis_str.startswith('P'):
            greater_than = True
            vis_str = vis_str[1:]
        miles = parse_fraction(vis_str)
        if miles is not None:
            prefix = 'less than ' if less_than else ('greater than ' if greater_than else '')
            return format_visibility_miles(miles, prefix), 1

    # Two-token fractional miles: "1 1/2SM", "2 3/4SM"
    if re.match(r'^\d+$', part) and idx + 1 < len(tokens):
        next_part = tokens[idx + 1]
        if next_part.endswith('SM') and '/' in next_part:
            whole = int(part)
            frac = parse_fraction(next_part[:-2])
            if frac is not None:
                return format_visibility_miles(whole + frac), 2

    return None


def is_weather_token(token):
    t = token
    if t.startswith('-') or t.startswith('+'):
        t = t[1:]
    elif t.startswith('VC'):
        t = t[2:]
    if not t:
        return False
    for code in ALL_WEATHER_STARTS:
        if t.startswith(code):
            return True
    return False


def decode_weather_token(token):
    remaining = token
    intensity = ''
    if remaining.startswith('VC'):
        intensity = 'in the vicinity'
        remaining = remaining[2:]
    elif remaining.startswith('-'):
        intensity = 'light'
        remaining = remaining[1:]
    elif remaining.startswith('+'):
        intensity = 'heavy'
        remaining = remaining[1:]

    descriptor = precip = obscuration = other = ''
    for code, label in WEATHER_DESCRIPTOR.items():
        if remaining.startswith(code):
            descriptor = label
            remaining = remaining[len(code):]
            break
    for code, label in WEATHER_PRECIP.items():
        if remaining.startswith(code):
            precip = label
            remaining = remaining[len(code):]
            break
    for code, label in WEATHER_OBSCURATION.items():
        if remaining.startswith(code):
            obscuration = label
            remaining = remaining[len(code):]
            break
    for code, label in WEATHER_OTHER.items():
        if remaining.startswith(code):
            other = label
            remaining = remaining[len(code):]
            break

    parts = [c for c in [intensity, descriptor, precip, obscuration, other] if c]
    return ' '.join(parts) if parts else token


def decode_cloud(cloud_str):
    m = re.match(r'^(SKC|CLR|NSC|NCD|FEW|SCT|BKN|OVC|VV)(\d{3})?(CB|TCU)?$', cloud_str)
    if not m:
        return cloud_str
    coverage, height, cloud_type = m.groups()
    text = CLOUD_COVERAGE.get(coverage, coverage)
    if height:
        feet = int(height) * 100
        text += f' at {feet:,} ft'
    if cloud_type == 'CB':
        text += ' (cumulonimbus — thunderstorm potential)'
    elif cloud_type == 'TCU':
        text += ' (towering cumulus)'
    return text


def decode_metar(raw_metar):
    raw_metar = raw_metar.strip()
    line = raw_metar.splitlines()[0]

    # Strip optional METAR/SPECI type prefix
    if line.startswith(('METAR ', 'SPECI ')):
        line = line[6:]

    tokens = line.split()
    result = {
        'raw': raw_metar,
        'station': None,
        'time': None,
        'auto': False,
        'wind': None,
        'wind_variable': None,
        'visibility': None,
        'weather': [],
        'clouds': [],
        'temperature_c': None,
        'dewpoint_c': None,
        'temperature_f': None,
        'dewpoint_f': None,
        'altimeter': None,
        'remarks': None,
        'summary': None,
    }

    if not tokens:
        return result

    idx = 0

    # Station ID
    if idx < len(tokens) and re.match(r'^[A-Z]{3,4}$', tokens[idx]):
        result['station'] = tokens[idx]
        idx += 1

    # Date/time DDHHMMz
    if idx < len(tokens) and re.match(r'^\d{6}Z$', tokens[idx]):
        t = tokens[idx]
        day, hour, minute = int(t[0:2]), int(t[2:4]), int(t[4:6])
        result['time'] = f'Day {day} of month, {hour:02d}:{minute:02d} UTC'
        idx += 1

    # AUTO / COR modifier
    if idx < len(tokens) and tokens[idx] in ('AUTO', 'COR'):
        result['auto'] = tokens[idx] == 'AUTO'
        idx += 1

    # Wind
    if idx < len(tokens) and re.match(r'^(\d{3}|VRB)\d{2,3}(G\d{2,3})?(KT|MPS|KMH)$', tokens[idx]):
        result['wind'] = decode_wind(tokens[idx])
        idx += 1
        # Variable wind direction range e.g. 280V350
        if idx < len(tokens) and re.match(r'^\d{3}V\d{3}$', tokens[idx]):
            v = tokens[idx]
            result['wind_variable'] = f'varying {v[:3]}° to {v[4:]}°'
            idx += 1

    # Visibility
    vis = decode_visibility(tokens, idx)
    if vis:
        result['visibility'], consumed = vis
        idx += consumed

    # RVR — skip (R28L/0600FT etc.)
    while idx < len(tokens) and re.match(r'^R\d{2}[LCR]?/', tokens[idx]):
        idx += 1

    # Present weather
    weather = []
    while idx < len(tokens) and is_weather_token(tokens[idx]):
        weather.append(decode_weather_token(tokens[idx]))
        idx += 1
    result['weather'] = weather

    # Sky conditions
    clouds = []
    while idx < len(tokens) and re.match(r'^(SKC|CLR|NSC|NCD|FEW|SCT|BKN|OVC|VV)\d{0,3}(CB|TCU)?$', tokens[idx]):
        clouds.append(decode_cloud(tokens[idx]))
        idx += 1
    result['clouds'] = clouds

    # Temperature / dew point
    if idx < len(tokens) and re.match(r'^M?\d{2}/M?\d{0,2}$', tokens[idx]):
        td = tokens[idx]
        slash = td.index('/')
        temp_c = decode_temp_val(td[:slash])
        dew_c = decode_temp_val(td[slash + 1:]) if td[slash + 1:] else None
        result['temperature_c'] = temp_c
        result['dewpoint_c'] = dew_c
        if temp_c is not None:
            result['temperature_f'] = c_to_f(temp_c)
        if dew_c is not None:
            result['dewpoint_f'] = c_to_f(dew_c)
        idx += 1

    # Altimeter
    if idx < len(tokens) and re.match(r'^[AQ]\d{4}$', tokens[idx]):
        alt = tokens[idx]
        if alt[0] == 'A':
            result['altimeter'] = f'{int(alt[1:]) / 100:.2f} inHg'
        else:
            result['altimeter'] = f'{int(alt[1:])} hPa'
        idx += 1

    # Remarks
    if idx < len(tokens) and tokens[idx] == 'RMK':
        result['remarks'] = ' '.join(tokens[idx + 1:])

    return result


def build_summary(decoded):
    sentences = []

    # Sky / weather headline
    if decoded['weather']:
        sentences.append('Currently experiencing: ' + ', '.join(decoded['weather']) + '.')

    if decoded['clouds']:
        sentences.append('Sky: ' + '; '.join(decoded['clouds']) + '.')
    elif not decoded['weather']:
        sentences.append('Sky conditions not reported.')

    # Temperature
    if decoded['temperature_c'] is not None:
        tf, tc = decoded['temperature_f'], decoded['temperature_c']
        if decoded['dewpoint_c'] is not None:
            spread = tc - decoded['dewpoint_c']
            feel = 'humid' if spread <= 3 else ('comfortable' if spread <= 10 else 'dry')
            df, dc = decoded['dewpoint_f'], decoded['dewpoint_c']
            sentences.append(
                f'Temperature is {tf}°F ({tc}°C), feeling {feel}. '
                f'Dew point is {df}°F ({dc}°C).'
            )
        else:
            sentences.append(f'Temperature is {tf}°F ({tc}°C).')

    # Wind
    if decoded['wind']:
        wind_text = f'Wind is {decoded["wind"]}'
        if decoded.get('wind_variable'):
            wind_text += f', {decoded["wind_variable"]}'
        sentences.append(wind_text + '.')

    # Visibility
    if decoded['visibility']:
        sentences.append(f'Visibility is {decoded["visibility"]}.')

    # Pressure
    if decoded['altimeter']:
        sentences.append(f'Barometric pressure is {decoded["altimeter"]}.')

    return ' '.join(sentences)
