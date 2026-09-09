# Agentic OR Planning Brief

Run type: dashboard-live
Run time: 2026-09-08T16:35:24.627842+05:30
Optimization status: WARNING: inventory target cannot be fully maintained
Optimization objective value: 4,314,248,582.09

## 60-day planning logic
- The optimizer solves one integrated 60-day LP using the complete 60-day demand, supply-capacity and route-cost schedules.
- Today, 7-day, 30-day and 60-day allocations are cumulative slices of that same solution; they are not separate forecasts solved independently.
- Full-horizon demand satisfaction is ENFORCED in the LP.
- Only today's dispatch is executed; later-day allocations are re-optimized as new information arrives.

## Executive status
- Weather API live locations: 10/10
- News connector connected: YES
- News source(s): Google News RSS
- Live news items detected: 50
- Global disruption-news risk score: 1.00
- Effective corridor capacity factor today: 0.60
- Maximum route delay today: 56.3 hours

## Horizon demand coverage

| Horizon | Cumulative demand | Planned dispatch | Shortfall | Ending inventory | Demand satisfied? |
|---|---:|---:|---:|---:|---|
| 1d | 40,200 | 31,200 | 0 | 847,800 | YES |
| 7d | 285,906 | 257,920 | 0 | 765,052 | YES |
| 30d | 1,206,414 | 1,347,133 | 0 | 981,979 | YES |
| 60d | 2,414,015 | 2,507,234 | 0 | 981,219 | YES |

## Supply-node status

| Supply node | Status | Planned cap. t/day | Effective cap. t/day | Today allocated | Utilization |
|---|---|---:|---:|---:|---:|
| Talcher-area source | WATCH | 16,000 | 12,640 | 0 | 0.0% |
| Ib-Valley-area source | WATCH | 13,000 | 10,270 | 9,870 | 96.1% |
| Korba-area source | WATCH | 15,000 | 11,850 | 11,850 | 100.0% |
| Mand-Raigarh-area source | WATCH | 12,000 | 9,480 | 9,480 | 100.0% |

## Demand-node status

| Demand node | Status | Today demand | Opening inventory | Target inventory | Projected closing | Today dispatch |
|---|---|---:|---:|---:|---:|---:|
| Plant 1 | NORMAL | 7,200 | 145,000 | 122,502 | 137,800 | 0 |
| Plant 2 | WATCH | 6,500 | 145,000 | 169,141 | 138,500 | 9,870 |
| Plant 3 | WATCH | 6,800 | 155,000 | 176,948 | 148,200 | 0 |
| Plant 4 | WATCH | 7,600 | 175,000 | 197,765 | 167,400 | 11,850 |
| Plant 5 | WATCH | 5,900 | 130,000 | 153,528 | 124,100 | 9,480 |
| Plant 6 | WATCH | 6,200 | 138,000 | 161,335 | 131,800 | 0 |

## Today's source → demand allocation (tonnes)

| Supply node | Plant 1 | Plant 2 | Plant 3 | Plant 4 | Plant 5 | Plant 6 | Total supplied |
|---|---:|---:|---:|---:|---:|---:|---:|
| Talcher-area source | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Ib-Valley-area source | 0 | 9,870 | 0 | 0 | 0 | 0 | 9,870 |
| Korba-area source | 0 | 0 | 0 | 11,850 | 0 | 0 | 11,850 |
| Mand-Raigarh-area source | 0 | 0 | 0 | 0 | 9,480 | 0 | 9,480 |
| Total received | 0 | 9,870 | 0 | 11,850 | 9,480 | 0 | 31,200 |

## Next 7 days cumulative source → demand allocation (tonnes)

| Supply node | Plant 1 | Plant 2 | Plant 3 | Plant 4 | Plant 5 | Plant 6 | Total supplied |
|---|---:|---:|---:|---:|---:|---:|---:|
| Talcher-area source | 21,160 | 0 | 0 | 0 | 0 | 0 | 21,160 |
| Ib-Valley-area source | 0 | 76,677 | 0 | 0 | 0 | 0 | 76,677 |
| Korba-area source | 0 | 0 | 13,110 | 75,825 | 0 | 0 | 88,935 |
| Mand-Raigarh-area source | 0 | 0 | 0 | 0 | 71,148 | 0 | 71,148 |
| Total received | 21,160 | 76,677 | 13,110 | 75,825 | 71,148 | 0 | 257,920 |

## Next 30 days cumulative source → demand allocation (tonnes)

| Supply node | Plant 1 | Plant 2 | Plant 3 | Plant 4 | Plant 5 | Plant 6 | Total supplied |
|---|---:|---:|---:|---:|---:|---:|---:|
| Talcher-area source | 200,920 | 0 | 0 | 0 | 0 | 44,994 | 245,915 |
| Ib-Valley-area source | 0 | 225,838 | 66,181 | 0 | 0 | 41,094 | 333,113 |
| Korba-area source | 0 | 0 | 166,773 | 258,595 | 0 | 0 | 425,368 |
| Mand-Raigarh-area source | 0 | 0 | 0 | 0 | 206,607 | 136,131 | 342,738 |
| Total received | 200,920 | 225,838 | 232,954 | 258,595 | 206,607 | 222,219 | 1,347,133 |

## Full 60 days cumulative source → demand allocation (tonnes)

| Supply node | Plant 1 | Plant 2 | Plant 3 | Plant 4 | Plant 5 | Plant 6 | Total supplied |
|---|---:|---:|---:|---:|---:|---:|---:|
| Talcher-area source | 409,863 | 0 | 0 | 0 | 0 | 44,994 | 454,857 |
| Ib-Valley-area source | 0 | 414,467 | 66,181 | 0 | 0 | 44,888 | 525,535 |
| Korba-area source | 0 | 0 | 364,108 | 479,146 | 0 | 1,123 | 844,377 |
| Mand-Raigarh-area source | 0 | 0 | 0 | 0 | 377,824 | 304,640 | 682,464 |
| Total received | 409,863 | 414,467 | 430,289 | 479,146 | 377,824 | 395,645 | 2,507,234 |

## Procurement / dispatch recommendation by horizon

| Source | Today | Next 7d | Next 30d | Next 60d |
|---|---:|---:|---:|---:|
| Talcher-area source | 0 | 21,160 | 245,915 | 454,857 |
| Ib-Valley-area source | 9,870 | 76,677 | 333,113 | 525,535 |
| Korba-area source | 11,850 | 88,935 | 425,368 | 844,377 |
| Mand-Raigarh-area source | 9,480 | 71,148 | 342,738 | 682,464 |

## Today's route transportation cost matrix — ₹/tonne

| Supply node | Plant 1 | Plant 2 | Plant 3 | Plant 4 | Plant 5 | Plant 6 |
|---|---:|---:|---:|---:|---:|---:|
| Talcher-area source | ₹120 | ₹220 | ₹260 | ₹300 | ₹320 | ₹250 |
| Ib-Valley-area source | ₹230 | ₹110 | ₹170 | ₹200 | ₹170 | ₹190 |
| Korba-area source | ₹310 | ₹230 | ₹120 | ₹100 | ₹180 | ₹190 |
| Mand-Raigarh-area source | ₹280 | ₹150 | ₹160 | ₹170 | ₹105 | ₹140 |

## Today's selected-route cost review

| Route | Allocated | Base cost ₹/t | Delay | Effective modeled cost ₹/t | Cost contribution |
|---|---:|---:|---:|---:|---:|
| Korba-area source → Plant 4 | 11,850 | ₹100 | 36.4 h | ₹103.64 | ₹1,228,134 |
| Ib-Valley-area source → Plant 2 | 9,870 | ₹110 | 41.7 h | ₹114.17 | ₹1,126,858 |
| Mand-Raigarh-area source → Plant 5 | 9,480 | ₹105 | 37.0 h | ₹108.70 | ₹1,030,476 |
**Today's modeled transportation cost:** ₹3,385,468

## News triggers
- Heavy rain in Odisha: Minister Vaishnaw orders close watch on vulnerable rail sections - The Times of India — https://news.google.com/rss/articles/CBMi8gFBVV95cUxQd0tkQV9hVV9MbS1uTmRfV2k1NFNNZEp3UzlqYmQtRTNpQ1ZvOFpYSjFNekFFUU40Vm16MDJzdHhEOTNmSnA5MC1lVDQ5bng0THpTZWNCQnBvX0s1UDJRY01zbHQzVlBVbUhGNXFOc0NUYUtvNXdqdHhpbExtbnp1WWc5Rl9ES09RMThhYzhScW9DQ2lPdExKSV9MWjJ5aXZjMzV1Wm9QcENqQU15amUwZjgxVDdzODZTb05mbGRqMGVkOW9wWUkxSzVKZjNHYXVRV1R5Z3d1dTlIMXNhT3NVWVZTQlBuWU5xbW1mZ2g2d3NuZ9IB9wFBVV95cUxOUkpHNl85VXVkYV9oNlJxSEtJdXNpNGlnZGV6YTc2OFJXRXp2WTZlaUFVOWdnQW5QWXdsM0xFLUdTZWtHNzhfLVRoSEM2cG1LY1BnRHBaM2ZoLUtYRk1UakM2WWFzcEZoN2tJWXFjQkpTNDNOZ3duanczNnpOOWpoUU5vRWU0N1R6Y0tUbnU5eW1YVE93aFZydU1ua3h6TzdUc3FLZElzMzNfUC1JR0xNTTlJSWdqUm52MEZ1S043b2trYmo0eHB2TEV4dGVfakVNSU5uXzZJMVBSbFBULVo3enZlTXQwazFJZ0loZXhrZENTTjR2STg4?oc=5
- Odisha: Talcher-Puri MEMU train derails near Puri station, no injuries reported - ANI News — https://news.google.com/rss/articles/CBMi2AFBVV95cUxObmxCaGd1cXNKVkJmZEp3eVdxY0lNT09UbTBCbWo4SDV3dElLclpjNVlrWW84RHEwYVgwLW5QLTRkdGtTV0dEb25MTW5HdUdoM2VSTzN6LWoxd0pxbGR4YmgwZE9oMEcwOGZ6TEdELTBkd0dYR3dSVktnZDQ4SHAxQWk3TmdRUDBQdG9rMS0xeTRWbndObG93MlhDVGt6VDZXU1k2VTlHVzZvN3g5eVBwZS02Uzh1cWxCS0RDMVpOUElmWmdnZnpHeVVOS2ZPMXpBNHBqcGczRXE?oc=5
- Railway Minister Ashwini Vaishnaw Orders Enhanced Monitoring Of Vulnerable Odisha Rail Sections Amid Heavy Rain - swarajyamag.com — https://news.google.com/rss/articles/CBMi3wFBVV95cUxNRVZwRzdiQmhIMG1neTNueGxyUzRLQVA5c0JqQXRBck1nMGxlM0d6emFIOURTVTMtU2dmcWdTZ2Zwa1lSTGpGSklhQUx6QUk2SXhpenozZW43TkpObENuY0pJRjJVUGR1WEszZTZUaE5FanVOaDNDelRUeXFpVTk2a0p5X2JXcUw1cFRqcXRiX1lFQjV0cDc0VkNaT2hxMnd6ckhTRFJUdklJSVRacE5Wa0QtOUMyWFlKWVBNWFdhS0t0YnZYX0ZHOWVYX1MxeHVOb3hKZFFvSUVsV3haTk1J0gHvAUFVX3lxTE1rZVF2TGNhNWV6b2JiXzV1TFU0TEhtZFdBdjlvT1BVVHZ1MGJzalYyZFA5dTdYZTNRYloyNzctS0FPTVRnLXRhRHFYM3l0UjI1bjAzZkxjY2VKOW5KTXBUUmdHYWdKYWNrTTlXN2pQbUVuRGJiTmhROEhVNEJEV0JiTHk4Q1dEOXVsdHZsaHNtN1NPZVJKeEE0MVNPRjlwRGx3NFVEamw2ZU45dkhDVmh3LUpPeEF6M1ZaRnM3d2FYVk5VZ2ZVVGxPS0w1VEZlMG9aRmxxUlp0em8xakhoUkgwNjNhWndLbWJUbFo5ZHpr?oc=5
- Heavy Rains Trigger Inundation & Rail Damage - OdishaPlus — https://news.google.com/rss/articles/CBMihAFBVV95cUxOVEZVSTZDeURpZWp0YkticlAwcS1kUVRNWWVUelBZYWtTdUNQakN0d3Z2bHNIb2JYVlFzOW1CNGpFcnRaNjByaGZCVjZPQ21tY3hKRWNmZHN4TFhYNGRHU2tWcjZOZG9ydC1mTE9aMmVCVXR6cEd3Q092dkpDdndZSmIwdWk?oc=5
- Four districts in flood grip; over one lakh affected in Odisha - The New Indian Express — https://news.google.com/rss/articles/CBMivAFBVV95cUxONW9wWmN1V29hZDB5UWZvZEw0X2NrVjV0dElPaFVPa3A2OExtS3gyNXhuOEZtcHpaOWpsQVRvNmtDMF95dzQwYjEtZDVjeng3V0s1Qk1yVTlod092Z1pDZTloTU9PRXhGZHN2MGNJYTd1ek9JUlhQeGNoTkRBZnQtUzZfbm42c3A3T0NzbXVHdXJtVHVyaTRwZ21GZGx2c0xBSDEzV1ByaXB1UXdhOVk3TXZsOG9JS2lIWFFFd9IBygFBVV95cUxNODcwUVpfUWpJTWNQalF0WmpsT1pQZFM3ZzEtY0JyY0dXdzFpOGJRbVROVk5lOXZNSFJQQ0piQTRuYTkwa1ZURk11c2pnMGVLWGc3UzZqSlBGMmlwTXRmeW9EUVZYV3MzRXpDZVVZOEQ1UFcyVkhaSXhQdmphUy1zbHBTSFdzNFByTTBhVmoxYzB6WG5UN3M5N3hsWkJPRHY0d29HN0R4Z2dEM3FmOVdRMzQteXhIb1hqLWpyQ2xnNUVmeXlVTEdGSVdn?oc=5
- Kamakhya Superfast Express Derails Near Nergundi In Odisha | Akashvani News - newsonair.gov.in — https://news.google.com/rss/articles/CBMijAFBVV95cUxOXzdSYzV2YmowTHZqQ01DYVB6Nm1IMTl0N1ByNlR6RXUyNXB0VURwUDhaWlEwcWpYT1NZdjVVbjlPMU5oWGlEQnlmM18xQkcwaF9KcEdQUHQyeE1UTXhuam9xSXk0bnlRMWRSbkowdjFxUFhyMkdnaHdsRHRIaGN6ZVczbWNtMHRCOHowVg?oc=5
- 45 Indian coal power plants have critical low fuel, government data shows - ET EnergyWorld — https://news.google.com/rss/articles/CBMi0gFBVV95cUxOZzdFeEJBSXlrWkl1d0lmS0NPN1ZnNVVHa29kUmlVc1dXUTBOMVc2a09rTng0bTh3Z18wUWdrUjIwUnJvd05xbFhxcjVZN2FZbW55b3JEZ1hPRzJtMktqVTBqVjdxdzlFQWg0WGdyX2Z2dmN5UHhZaWdXVWw0RlNKYng4QTBHSV9ISmtjUHI4NElDT2lReDR3Qy0tTmNjNG9YSnZ0dW1aSUxFaHExUEFzOXoyU1Fod2lpTXlSZzZhNXkxWmYwTUg3eFVsTTYtQ3Y1M2fSAdcBQVVfeXFMTko4VHJmM3JRS1BDZXBMakxRV1NqMTgyNnNxVUpZcHZyRnY5ejJZYVg1VXdVS21kMmR3dTI4bi1iTmVuS1J4bW5UMmUxdjNLR0dKX1lEdFZ0QjVQUkNGSUVjNnhYSEJSTXAzb2NjVUFNWklSZXFBcHE5SmR6R3VXaWRjaVZWakwyVnlaMkp1OFZWbnBkZlZCU3Q0UEtEU0hmTndSU3FjRTVKUWg2c0xmMjV5WnZlaHBhZm50UFVNZ2psU3JZN0MySGZEdkRIb3hqdXpFb3c4aFk?oc=5
- Trains Come Face To Face In Odisha's Bhubaneswar, Probe Ordered - ETV Bharat — https://news.google.com/rss/articles/CBMisAFBVV95cUxPelh5NmswZUQwblh5SVJsRi16eUc0MUt2eEdUeGRDd1g0NGJQTVFNV3lQTWo1d0tTTGV6eXkyU1Jkelo3X04yV3B3UlM5LUYwUHBCaWpGSjVyN280by1BQ0g4bGt6QlJLYTNsMEtfMXZZRTlwdjNGcDhSWHVubU5EdnVZWU8yNFhQUVBKU016OVc3dXpOM3FpWEV4Y2NORTZEbTFQcVdwY1dKTUZ2a2ZRUtIBtgFBVV95cUxNT3ZIT3JOMEpreFBvdk9rekw3bm1zdFBmSlpzUXBzdnpkcExGODQxWTMya3BIeE9vV00yRU9QWWhxLXBpTWd3UDBSRG5ZS1prTjJmdDczX0I2ak9lTW9FQXBWTVJ1dnVBb0x4NV95VGZzcmhzeE9FWTdZSmVCa3BTbUx6U3VxMkJkQTJMMjNNUzFJaFA5UnJ4anZ3eFBrMUdBT0hUTmZFQ3FKTGVVRWpNbmEzYmtfUQ?oc=5

## Decision rule
The 1/7/30/60-day tables come from one 60-day demand-fulfillment optimization. Execute only today's dispatch, then re-solve the remaining horizon with refreshed weather, news and edited scenario inputs.

## Attached operational files
- allocation_matrix_today.csv / allocation_matrix_7d.csv / allocation_matrix_30d.csv / allocation_matrix_60d.csv
- horizon_demand_coverage.csv
- input_demand_60d.csv
- input_supply_60d.csv
- input_route_cost_60d.csv
- supply_node_status.csv
- demand_node_status.csv
- allocation_explanations_today.csv
- procurement_summary.csv
- inventory_plan.csv
- route_delay.csv
- today_route_cost_breakdown.csv
- audit_latest.md

## Model caveat
Bundled network values are illustrative. Dashboard edits become the active planning assumptions until reset or replaced.