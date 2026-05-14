# METAR Weather Reader

A lightweight Flask web app that turns cryptic METAR aviation weather reports into plain-English summaries anyone can understand.

Type in any ICAO airport code (e.g. `KHIO`, `KLAX`, `EGLL`) and get a friendly weather report like:

> *Sky: a few clouds at 3,900 ft; overcast at 5,500 ft. Temperature is 63°F (17°C), feeling comfortable. Wind is 16 mph from the WSW, gusting to 25 mph. Visibility is 10 miles (excellent). Barometric pressure is 30.14 inHg.*

Weather data is fetched live from the [aviationweather.gov](https://aviationweather.gov) public API — no API key required.

---

## Features

- Decodes all standard METAR fields:
  - Wind speed, direction (compass + degrees), and gusts
  - Visibility in miles or meters
  - Sky conditions (cloud coverage and altitude)
  - Present weather phenomena (rain, snow, fog, thunderstorms, etc.)
  - Temperature and dew point in °F and °C
  - Barometric pressure in inHg or hPa
- Plain-English summary alongside the raw METAR string
- Works with any ICAO airport code worldwide
- No API key or account needed

## Screenshots

| Search | Results |
|---|---|
| Enter any ICAO code | Instant plain-English report with labeled detail rows |

## Requirements

- Python 3.8+
- pip

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/metar-reader.git
cd metar-reader

# 2. Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
.venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

## Running the app

```bash
python app.py
```

Then open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

## Running with Docker

The easiest way to run the app anywhere Docker is available.

**Using Docker Compose (recommended):**

```bash
docker compose up --build
```

Then open [http://localhost:5000](http://localhost:5000).

To run in the background:

```bash
docker compose up --build -d
docker compose down   # stop
```

**Using Docker directly:**

```bash
docker build -t metar-reader .
docker run -p 5000:5000 metar-reader
```

## Production deployment

The built-in Flask development server is for local use only. The Docker image uses **gunicorn** as the WSGI server automatically, making it production-ready out of the box.

For non-Docker deployments:

```bash
gunicorn --bind 0.0.0.0:5000 --workers 2 app:app
```

Or deploy to any platform that supports Python web apps (Railway, Render, Fly.io, Heroku, etc.).

## Project structure

```
metar-reader/
├── app.py              # Flask routes and API endpoint
├── metar_decoder.py    # METAR parsing and plain-English translation
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container image definition
├── docker-compose.yml  # Compose config for one-command startup
└── templates/
    └── index.html      # Single-page frontend
```

## Data source

Live METAR data is retrieved from the [Aviation Weather Center API](https://aviationweather.gov/api/data/metar):

```
https://aviationweather.gov/api/data/metar?ids=KHIO
```

No authentication is required. Data is updated approximately once per hour at most stations.

## License

MIT
