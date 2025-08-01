# tenders-monitoring

Automates keyword-based searches on [evergabe-online.de](https://www.evergabe-online.de/) to collect public tenders related to topics like AI, data platforms, and cloud technologies.

The search targets the following topics (in both English and German):
- Artificial Intelligence / Künstliche Intelligenz
- Generative AI / Generative KI
- Machine Learning / Maschinelles Lernen
- Chatbots / Chatbots
- Knowledge Graph / Wissensgraph
- RAG / Retrieval Augmentierte Generierung
- and many more...

## Components
The main components of the project include:
- `app/main.py`: The orchestrator script that runs the keyword searches and saves the results.
- `app/search.py`: Handles session management, query submission (via Selenium + requests), pagination, and HTML parsing.
- `app/utils.py`: Contains date helper functions.

## Features
- Searches both English and German translations of selected keywords.
- Limits results to tenders with deadlines one month from the current date.
- Extracts results across multiple pages (optional extensive mode).
- Outputs results in a user-friendly HTML table (`app/res/results.html`).
- Uses a hybrid of Selenium and requests to bypass cookie/session restrictions.

## Installation

### Prerequisites
- Python 3.11
- Google Chrome (or Chromium-based browser like Brave)
- ChromeDriver installed and in your PATH

Create python environemnt and install dependencies
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage
### Basic usage
```bash
cd app
python main.py
```
This performs a non-extensive search and exports the deduplicated results to `res/results.html`.

### Extensive (multi-page) search
```bash
cd app
python main.py --extensive
```
Enables deep scraping by following pagination links to collect **all matching tenders**, not just those on the first page. Useful for comprehensive monitoring when many results are expected.