# v2 Architecture — Agentic AI around the OR optimizer

## Hourly control loop

```text
Hourly trigger
   -> Weather API
   -> Multi-source news connector (Google News RSS + optional NewsAPI)
   -> Data-ingestion audit
   -> Risk + delay assessment
   -> Threshold gate
       -> no breach: store audit + send hourly OK email
       -> breach: re-optimize 60-day rolling horizon
                    -> generate revised procurement/inventory report
                    -> email disruption alert
```

## 08:00 control loop

```text
08:00 trigger
   -> fresh weather + news
   -> risk / delay estimates
   -> demand forecast
   -> inventory target
   -> LP optimization
   -> validation
   -> audit + planning report
   -> daily email
```

## OR decision variables
- `x[i,j,t]`: tonnes dispatched from source i to plant j on day t.
- `I[j,t]`: end-of-day inventory.
- `u[j,t]`: unmet consumption.
- `v[j,t]`: inventory-target violation.

## Live data -> OR mapping
- rain/flood risk at source -> source capacity factor decreases.
- widespread weather/news disruption -> corridor capacity factor decreases.
- route disruption -> predicted route lead time increases.
- disruption risk -> inventory target increases.
- updated demand forecast -> daily demand parameter changes.

The agent does not invent shipment allocations. It changes traceable model parameters and calls the LP solver.

## Alert gate
Default prototype triggers are configurable in `config/monitoring.yaml`:
- 24h rain >= 50 mm,
- 72h rain >= 120 mm,
- maximum 24h precipitation probability >= 85%,
- severe-rain flag,
- news risk >= 0.60,
- max route delay >= 12 h,
- effective corridor capacity <= 85%.

Any threshold breach can trigger an immediate re-solve and email. By default, the v5/v6 monitor sends one status email every hour; active disruptions receive a fresh alert each hourly check.

## Auditing
Every hourly snapshot persists raw/derived evidence:
- API connection success/failure,
- provider,
- weather measures by location,
- errors/fallback status,
- news article count and URLs,
- risk scores,
- capacity factors,
- worst predicted routes.

Full OR runs are stored in unique timestamped directories to avoid Windows/Excel file locks and to preserve decision history.


## v6 dashboard
Streamlit dashboard can load the saved 08:00 run or trigger a fresh live data + OR solve on demand.

## v7 scenario-control layer

Dashboard edits are persisted as absolute-date scenario inputs. Each run maps those dates onto the rolling day-0..59 horizon. The same active scenario is consumed by manual dashboard solves, daily 08:00 optimization, and disruption-triggered re-optimization.

The LP is a single 60-day demand-fulfillment model. The 1/7/30/60-day tables are reporting windows over one solution rather than separate optimizations.
