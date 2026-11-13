# TMDB Movie Financial & Reception Dashboard

## Interactive dashboard

This project is a working local Dash application. It explores relationships
among movie budget, revenue, popularity, genre, release year, and vote
average using coordinated interactive charts.

After starting the application, open:

<http://127.0.0.1:8050>

## Runtime requirements

To run the dashboard on another computer, install or provide:

- Python 3.9 or newer. Python 3.11 or 3.12 is recommended.
- `pip`, which normally comes with Python.
- The files `app.py`, `requirements.txt`, `data/movies_cleaned.csv`, and
  `assets/styles.css`.
- Internet access during setup so `pip` can download packages.
- A modern web browser such as Chrome, Edge, Firefox, or Safari.
- An available local TCP port, normally `8050`.

No Node.js, npm, database server, API key, or environment variables are
required.

## Dependencies

The direct Python dependencies are listed in `requirements.txt`:

- `dash` — web application framework and callback server.
- `dash-bootstrap-components` — Bootstrap layout and card components.
- `pandas` — CSV loading, cleaning, filtering, and aggregation.
- `plotly` — interactive scatter, bar, line, and histogram charts.

Running `python -m pip install -r requirements.txt` also installs the
transitive dependencies required by those packages, including Flask,
Werkzeug, Jinja2, itsdangerous, click, requests, retrying, narwhals,
packaging, numpy, python-dateutil, pytz/tzdata, six, and related support
packages. Do not install these individually; `pip` resolves compatible
versions automatically.

The runtime does not require a separate CSS package. Dash automatically
loads the project stylesheet from `assets/styles.css`, and the Bootstrap
theme is supplied by `dash-bootstrap-components`.

## Setup and run on Windows

1. Install Python from <https://www.python.org/downloads/windows/>.
   During installation, select **Add python.exe to PATH**. Python 3.11 or
   3.12 is recommended.
2. Open PowerShell in the project folder.
3. Create a virtual environment:

   ```powershell
   py -3.11 -m venv .venv
   ```

   If the Python launcher is unavailable, use:

   ```powershell
   python -m venv .venv
   ```

4. Activate it:

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

5. Upgrade packaging tools and install all project dependencies:

   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

6. Start the dashboard:

   ```powershell
   python app.py
   ```

7. Open <http://127.0.0.1:8050> in a browser. Keep the PowerShell window
   open while using the dashboard. Press `Ctrl+C` in that window to stop it.

If PowerShell blocks activation, allow scripts for the current user and
repeat activation:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Alternatively, use Command Prompt without activating:

```bat
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

## Setup and run on macOS or Linux

1. Install Python 3.9 or newer.
2. Open Terminal in the project folder.
3. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Upgrade packaging tools and install dependencies:

   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

5. Start the dashboard and open <http://127.0.0.1:8050>:

   ```bash
   python app.py
   ```

Keep the terminal open while using the dashboard. Press `Ctrl+C` to stop it.

## Data files and optional preprocessing

The raw files under `archive/` are not required to run the dashboard when
`data/movies_cleaned.csv` is included. They are required only when rebuilding
the cleaned dataset with `data/prepare_data.py`.

The dashboard uses the prepared file at `data/movies_cleaned.csv`. To rebuild
that file from the bundled raw TMDB export, run this from the project root:

Windows PowerShell:

```powershell
python data\prepare_data.py
```

macOS/Linux:

```bash
python data/prepare_data.py
```

The preprocessing script requires only pandas and the Python standard
library; those are already installed by `requirements.txt`.

## Dashboard interactions

- Use the genre dropdown and numeric range sliders to filter the dataset.
- Use box or lasso selection in the Budget vs. Revenue scatter plot.
- Click a genre bar, timeline point, or rating bin to cross-filter the views.
- Click **Reset All Filters** to restore the default view.
- Movies without recorded budget or revenue are excluded from financial
  range filters and financial charts; the interface reports this limitation.

## Submission files

- `app.py` — Dash application and callbacks.
- `requirements.txt` — Python dependencies.
- `data/prepare_data.py` — reproducible preprocessing script.
- `data/movies_cleaned.csv` — cleaned dashboard dataset.
- `usability_report.md` — usability test tasks, observations, issues, and
  design changes.
- `usability_report.pdf` — formatted usability report for submission.
- `feedback_log.md` — concise early-feedback log and the resulting fixes.
- `reflection.pdf` — compiled reflection for submission.
- `cover_page.pdf` — required submission cover page.
- `screenshots/` — annotated interaction screenshots.
- `assets/styles.css` — dashboard-specific layout styling.

## Data source

The dashboard uses the bundled TMDB 5000 Movies dataset in
`data/raw dataset/tmdb_5000_movies.csv`. The preprocessing script keeps released films
with known release years, converts numeric fields, treats zero placeholders as
missing measurements, and derives the fields used by the dashboard.
