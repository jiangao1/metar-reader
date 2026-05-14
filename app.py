"""
Flask web application for the METAR Weather Reader.

Serves a single-page UI and a JSON API endpoint that fetches raw METAR
data from aviationweather.gov and returns a decoded, human-readable report.
"""

import re
from flask import Flask, render_template, request, jsonify
import requests
from metar_decoder import decode_metar, build_summary

app = Flask(__name__)

# ICAO airport codes are 3–4 uppercase letters (e.g. KHIO, EGLL, RJTT).
_ICAO_RE = re.compile(r'^[A-Z]{3,4}$')

# Source API — swap the `ids` query parameter to change the station.
_METAR_API = 'https://aviationweather.gov/api/data/metar?ids={}'


@app.route('/')
def index():
    """Render the main search page."""
    return render_template('index.html')


@app.route('/weather')
def get_weather():
    """Fetch and decode a METAR report for the requested airport.

    Query parameters:
        airport (str): ICAO airport code (3–4 letters, e.g. ``KHIO``).

    Returns:
        JSON: Decoded weather fields plus a plain-English ``summary`` string,
        or an ``error`` key with an HTTP 4xx/5xx status on failure.
    """
    airport = request.args.get('airport', '').strip().upper()

    if not airport:
        return jsonify({'error': 'Please enter an airport code.'}), 400

    if not _ICAO_RE.match(airport):
        return jsonify({'error': 'Please enter a valid 3–4 letter ICAO airport code.'}), 400

    try:
        resp = requests.get(_METAR_API.format(airport), timeout=10)
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
    # debug=True enables auto-reload and the interactive debugger.
    # Use a production WSGI server (e.g. gunicorn) for public deployments.
    app.run(debug=True)
