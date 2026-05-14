import re
from flask import Flask, render_template, request, jsonify
import requests
from metar_decoder import decode_metar, build_summary

app = Flask(__name__)

_ICAO_RE = re.compile(r'^[A-Z]{3,4}$')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/weather')
def get_weather():
    airport = request.args.get('airport', '').strip().upper()

    if not airport:
        return jsonify({'error': 'Please enter an airport code.'}), 400

    if not _ICAO_RE.match(airport):
        return jsonify({'error': 'Please enter a valid 3–4 letter ICAO airport code.'}), 400

    try:
        url = f'https://aviationweather.gov/api/data/metar?ids={airport}'
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        raw = resp.text.strip()

        if not raw:
            return jsonify({
                'error': f'No METAR data found for {airport}. '
                         'Check that it is a valid ICAO code (e.g. KHIO, KLAX).'
            }), 404

        decoded = decode_metar(raw)
        decoded['summary'] = build_summary(decoded)
        return jsonify(decoded)

    except requests.Timeout:
        return jsonify({'error': 'Request timed out. Please try again.'}), 504
    except requests.RequestException as e:
        return jsonify({'error': f'Failed to fetch weather data: {e}'}), 500


if __name__ == '__main__':
    app.run(debug=True)
