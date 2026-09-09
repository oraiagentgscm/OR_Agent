# Agentic AI + Daily Rolling-Horizon OR Optimizer — v6

This version adds **auditable live-data ingestion, hourly disruption monitoring, threshold-triggered re-optimization, email alerts, and an 08:00 daily email** to the coal transportation-with-inventory prototype.

## What happens automatically

### Every hour (default: HH:05, Asia/Kolkata)
1. Fetch weather for all configured source and plant coordinates.
2. Fetch and merge disruption news from Google News RSS and optional NewsAPI.
3. Write a timestamped data-ingestion audit.
4. Calculate weather risk, news risk, corridor capacity factor and route-delay estimates.
5. Check configurable disruption thresholds.
6. If no threshold is crossed: stop after the audit.
7. If a threshold is crossed: immediately re-run the 60-day OR model using the **same live snapshot**.
8. Send an alert email with the threshold breaches, updated prediction, news, audit, procurement report, route delays and inventory plan.
9. Suppress duplicate unchanged alerts for the configured cooldown period.

### Every day at 08:00
1. Fetch fresh weather/news.
2. Re-run the rolling 60-day model.
3. Generate today / 7-day / 30-day / 60-day procurement recommendations.
4. Generate inventory targets and route-delay projections.
5. Email the complete report and audit files.

## Important architecture rule
The AI/agent layer **senses, forecasts, updates model parameters, triggers the solver and communicates results**. The LP remains the allocation decision engine.

---

# 1. Setup on Windows

Open PowerShell in this project folder.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If `.venv` is already active, do not recreate it; simply run `pip install -r requirements.txt`.

Copy the email configuration template:

```powershell
Copy-Item .env.example .env
notepad .env
```

---

# 2. Configure email

For Gmail, `.env` can be:

```text
LIVE_WEB_ENABLED=true
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USE_SSL=true
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=recipient@example.com
EMAIL_FROM_NAME=Agentic OR Monitor
```

Use a Google **App Password** rather than your normal Google account password when your account configuration requires it. For another provider, replace the SMTP host, port and TLS/SSL settings with that provider's SMTP settings.

Never commit `.env`; it is ignored by `.gitignore`.

Test email:

```powershell
python test_email.py
```

Successful output:

```text
{'sent': True, 'recipients': ['recipient@example.com']}
```

---

# 3. Verify actual web connectivity

Run:

```powershell
python test_web.py
```

You want output similar to:

```text
WEATHER: 10/10 locations connected
S1: source=open-meteo live=True ...
...
NEWS: connected=True articles=12 source=Google News RSS + NewsAPI
```

`source=open-meteo` + `live=True` proves that location came from the web rather than fallback data.

`NEWS CONNECTOR: connected=True` means at least one configured news provider responded. `articles=0` can still be a valid web response when the query has no matching articles.

---

# 4. Run a complete analysis manually

```powershell
python run_once.py
```

Each run is written to a unique folder such as:

```text
outputs\runs\20260906_080001_manual\
```

This prevents Excel from locking the next run's CSV files.

Files include:

```text
audit_latest.md
audit_latest.json
daily_brief.md
procurement_summary.csv
inventory_plan.csv
route_delay.csv
full_plan.csv
run_meta.json
```

The audit explicitly shows:
- how many weather locations connected live,
- provider name,
- 24h / 72h rainfall,
- maximum precipitation probability,
- fallback/error details,
- whether news retrieval connected,
- article count and URLs,
- news-risk score,
- effective source/corridor factors,
- maximum predicted route delay.

---

# 5. Test the hourly disruption monitor manually

```powershell
python monitor_once.py
```

Every check is preserved under:

```text
outputs\hourly_snapshots\<timestamp>\
```

If no threshold is crossed, it records the audit and sends no alert.

If a threshold is crossed, it re-runs the OR model and emails the revised report unless the alert is a duplicate inside the cooldown window.

---

# 6. Edit disruption thresholds

Open:

```text
config\monitoring.yaml
```

Defaults:

```yaml
weather:
  rain_24h_mm: 50.0
  rain_72h_mm: 120.0
  precip_probability_24h_pct: 85.0
  require_severe_rain_flag: true

risk:
  news_risk: 0.60
  max_route_delay_hours: 12.0
  min_corridor_capacity_factor: 0.85

alerts:
  cooldown_hours: 6
  resend_if_signature_changes: true
```

These are prototype alert values, not statutory limits. Calibrate them against historical operational delay data before presenting them as predictive thresholds.

---

# 7. Run continuously

Option A — keep the Python scheduler running:

```powershell
python scheduler.py
```

It runs:
- daily report at 08:00,
- hourly monitor at minute :05.

Option B — recommended on Windows: install Windows Scheduled Tasks:

```powershell
powershell -ExecutionPolicy Bypass -File .\install_windows_tasks.ps1
```

This creates:
- `AgenticOR-Daily-8AM`
- `AgenticOR-Hourly-Monitor`

Inspect them in **Task Scheduler → Task Scheduler Library**.

Your PC must still be awake/running and connected to the internet. For genuine 24×7 production delivery, deploy the same `daily_once.py` and `monitor_once.py` commands to a cloud VM/container/scheduler.

---

# 8. Daily email test

After email is configured, test the actual daily workflow immediately:

```powershell
python daily_once.py
```

This performs a fresh analysis, creates the timestamped report folder and sends the same report that the 08:00 task will send.

---

# 9. Data quality note

The network, cost, capacity, inventory and demand values supplied in `config/network.yaml` remain illustrative placeholders. Replace them with the project team's validated 4-source × 6-plant data.

The current delay estimator remains a transparent heuristic. A production-quality delay predictor should be trained and back-tested on historical scheduled-vs-actual rail/rake transit, loading/unloading, rainfall/warnings, track disruption and wagon/rake availability data.


## v3 email/report additions
- Status table for every supply node.
- Status table for every demand node.
- Today's full source-to-demand allocation matrix.
- CSV exports: `supply_node_status.csv`, `demand_node_status.csv`, `allocation_matrix_today.csv`.
- Disruption-alert emails include the full revised planning brief after re-optimization.
- See `deploy/CLOUD_DEPLOYMENT.md` for true 24×7 hosting.

## v4 route-cost email review
Every daily and disruption-triggered full report now includes:
- the complete 4×6 base transportation-cost matrix (₹/tonne),
- today's selected routes and allocated tonnes,
- predicted delay on each selected route,
- effective modeled cost per tonne after the configured delay-risk adder,
- today's modeled transport-cost contribution by route and total.

CSV exports:
- `route_cost_matrix.csv`
- `today_route_cost_breakdown.csv`


## v5 hourly email behavior
The hourly monitor now sends exactly one status email each hourly check when email is enabled:
- No threshold breach: `[OK] No disruption detected` with a short health/risk summary.
- Threshold breach: `[ALERT] Coal corridor disruption` with immediate re-optimization and the full revised report.

Email addresses are configured in `.env`, not hard-coded in Python:
- `SMTP_USERNAME`: SMTP login account
- `EMAIL_FROM`: sender address shown in the email
- `EMAIL_TO`: recipient address(es), comma-separated for multiple recipients

The scheduler reads `.env` via `python-dotenv`, and `src/coal_agent/emailer.py` reads these environment variables when sending.


## v6 — Multi-source news + dashboard

### GDELT removed
The project no longer calls GDELT. `src/coal_agent/news.py` now uses a resilient multi-source connector:
1. **Google News RSS search** — no API key required; always attempted.
2. **NewsAPI** — optional structured enrichment when `NEWSAPI_KEY` is configured.
3. Results are merged and deduplicated. The news connector is considered live if at least one provider succeeds.
4. Both providers use retry/backoff logic for transient failures and HTTP 429 responses.

Optional `.env` setting:

```text
NEWSAPI_KEY=your_newsapi_key
```

If `NEWSAPI_KEY` is blank, the project still operates using Google News RSS. This removes the former GDELT dependency and reduces single-provider failure risk.

### Dashboard
Install the new dependency once:

```powershell
pip install -r requirements.txt
```

Start the dashboard:

```powershell
streamlit run dashboard.py
```

or:

```powershell
.\run_dashboard.ps1
```

The dashboard has two operating modes:
- **Latest 08:00 daily snapshot** — reads the most recent saved `*_daily-08am` run without calling external APIs again.
- **Refresh live now** — the `Hit live data + re-optimize` button fetches fresh weather/news signals, recalculates risk, re-runs the 60-day OR model, and displays the newly created `dashboard-live` run.

Dashboard views include:
- weather/news connectivity,
- news source and article count,
- news-risk score,
- effective corridor capacity,
- maximum route delay,
- all supply-node statuses,
- all demand-node statuses,
- 4×6 source-to-demand allocation,
- procurement summary,
- inventory plan,
- route delay table,
- 4×6 route cost matrix,
- selected-route cost contributions,
- live disruption headlines and links.

## v7 — 60-day editable scenario + integrated demand-fulfillment logic

The Streamlit dashboard now includes a persistent 60-day planning input editor:

- Daily demand for every demand node (P1–P6) for each of the next 60 days.
- Daily available supply/capacity for every supply node (S1–S4) for each of the next 60 days.
- Daily transportation cost for every one of the 24 source→plant routes for each of the next 60 days.

Use **Save active scenario** to persist edits under `scenario_inputs/`. Those inputs are then automatically used by dashboard live runs, the scheduled 08:00 run, and disruption-triggered re-optimization. Use **Reset to baseline** to remove the saved scenario.

### Revised horizon logic
The OR model performs one integrated 60-day solve. Demand is enforced day-by-day across the full 60-day demand schedule when `enforce_full_horizon_demand: true`.

The dashboard/email views are cumulative slices of that same solution:
- Today = day 0 dispatch from the 60-day solution
- 7 days = cumulative dispatch on days 0–6
- 30 days = cumulative dispatch on days 0–29
- 60 days = cumulative dispatch on days 0–59

They are not four independent forecasts. Only today's dispatch is executed; the remaining plan is rolling guidance and is re-solved as new inputs arrive.

New outputs include:
- `allocation_matrix_today.csv`
- `allocation_matrix_7d.csv`
- `allocation_matrix_30d.csv`
- `allocation_matrix_60d.csv`
- `horizon_demand_coverage.csv`
- `input_demand_60d.csv`
- `input_supply_60d.csv`
- `input_route_cost_60d.csv`

## v8 dashboard explainability
- Allocation matrix is now the primary, full-width dashboard view.
- Non-zero allocations are highlighted and Today's plan includes plant-level explanations.
- Each plant explanation uses opening inventory days-cover, target days, future dispatch timing,
  route cost/delay and network-wide constraints.
- New output: `allocation_explanations_today.csv`.
- Dashboard visual theme and live-check controls have been redesigned.
- The on-demand live action is now described as a network reassessment / disruption check rather
  than generic "fetching live data".
