# Agentic AI — Data Ingestion Audit

## Connectivity
- Weather API: CONNECTED (10/10 locations live)
- News connector: CONNECTED (50 articles)
- News source: Google News RSS
- News fetch error: None
- News connector details: NewsAPI unavailable: NEWSAPI_KEY not configured

## Weather observations
| Location | Live? | 24h rain mm | 72h rain mm | Max precip % | Severe flag |
|---|---|---:|---:|---:|---:|
| Talcher-area source | YES | 3.1 | 38.9 | 88 | 0 |
| Ib-Valley-area source | YES | 1.3 | 21.0 | 88 | 0 |
| Korba-area source | YES | 0.7 | 8.2 | 63 | 0 |
| Mand-Raigarh-area source | YES | 0.5 | 15.9 | 65 | 0 |
| Plant 1 | YES | 2.7 | 62.9 | 84 | 0 |
| Plant 2 | YES | 5.1 | 26.2 | 63 | 0 |
| Plant 3 | YES | 0.7 | 3.7 | 71 | 0 |
| Plant 4 | YES | 0.7 | 5.5 | 46 | 0 |
| Plant 5 | YES | 1.6 | 22.9 | 60 | 0 |
| Plant 6 | YES | 4.6 | 39.1 | 99 | 1 |

## Agent interpretation
- News risk: 1.00
- Effective corridor capacity factor: 0.60
- Maximum predicted route delay: 56.3 hours

## Latest disruption news
- Heavy rain in Odisha: Minister Vaishnaw orders close watch on vulnerable rail sections - The Times of India — https://news.google.com/rss/articles/CBMi8gFBVV95cUxQd0tkQV9hVV9MbS1uTmRfV2k1NFNNZEp3UzlqYmQtRTNpQ1ZvOFpYSjFNekFFUU40Vm16MDJzdHhEOTNmSnA5MC1lVDQ5bng0THpTZWNCQnBvX0s1UDJRY01zbHQzVlBVbUhGNXFOc0NUYUtvNXdqdHhpbExtbnp1WWc5Rl9ES09RMThhYzhScW9DQ2lPdExKSV9MWjJ5aXZjMzV1Wm9QcENqQU15amUwZjgxVDdzODZTb05mbGRqMGVkOW9wWUkxSzVKZjNHYXVRV1R5Z3d1dTlIMXNhT3NVWVZTQlBuWU5xbW1mZ2g2d3NuZ9IB9wFBVV95cUxOUkpHNl85VXVkYV9oNlJxSEtJdXNpNGlnZGV6YTc2OFJXRXp2WTZlaUFVOWdnQW5QWXdsM0xFLUdTZWtHNzhfLVRoSEM2cG1LY1BnRHBaM2ZoLUtYRk1UakM2WWFzcEZoN2tJWXFjQkpTNDNOZ3duanczNnpOOWpoUU5vRWU0N1R6Y0tUbnU5eW1YVE93aFZydU1ua3h6TzdUc3FLZElzMzNfUC1JR0xNTTlJSWdqUm52MEZ1S043b2trYmo0eHB2TEV4dGVfakVNSU5uXzZJMVBSbFBULVo3enZlTXQwazFJZ0loZXhrZENTTjR2STg4?oc=5
- Odisha: Talcher-Puri MEMU train derails near Puri station, no injuries reported - ANI News — https://news.google.com/rss/articles/CBMi2AFBVV95cUxObmxCaGd1cXNKVkJmZEp3eVdxY0lNT09UbTBCbWo4SDV3dElLclpjNVlrWW84RHEwYVgwLW5QLTRkdGtTV0dEb25MTW5HdUdoM2VSTzN6LWoxd0pxbGR4YmgwZE9oMEcwOGZ6TEdELTBkd0dYR3dSVktnZDQ4SHAxQWk3TmdRUDBQdG9rMS0xeTRWbndObG93MlhDVGt6VDZXU1k2VTlHVzZvN3g5eVBwZS02Uzh1cWxCS0RDMVpOUElmWmdnZnpHeVVOS2ZPMXpBNHBqcGczRXE?oc=5
- Railway Minister Ashwini Vaishnaw Orders Enhanced Monitoring Of Vulnerable Odisha Rail Sections Amid Heavy Rain - swarajyamag.com — https://news.google.com/rss/articles/CBMi3wFBVV95cUxNRVZwRzdiQmhIMG1neTNueGxyUzRLQVA5c0JqQXRBck1nMGxlM0d6emFIOURTVTMtU2dmcWdTZ2Zwa1lSTGpGSklhQUx6QUk2SXhpenozZW43TkpObENuY0pJRjJVUGR1WEszZTZUaE5FanVOaDNDelRUeXFpVTk2a0p5X2JXcUw1cFRqcXRiX1lFQjV0cDc0VkNaT2hxMnd6ckhTRFJUdklJSVRacE5Wa0QtOUMyWFlKWVBNWFdhS0t0YnZYX0ZHOWVYX1MxeHVOb3hKZFFvSUVsV3haTk1J0gHvAUFVX3lxTE1rZVF2TGNhNWV6b2JiXzV1TFU0TEhtZFdBdjlvT1BVVHZ1MGJzalYyZFA5dTdYZTNRYloyNzctS0FPTVRnLXRhRHFYM3l0UjI1bjAzZkxjY2VKOW5KTXBUUmdHYWdKYWNrTTlXN2pQbUVuRGJiTmhROEhVNEJEV0JiTHk4Q1dEOXVsdHZsaHNtN1NPZVJKeEE0MVNPRjlwRGx3NFVEamw2ZU45dkhDVmh3LUpPeEF6M1ZaRnM3d2FYVk5VZ2ZVVGxPS0w1VEZlMG9aRmxxUlp0em8xakhoUkgwNjNhWndLbWJUbFo5ZHpr?oc=5
- Heavy Rains Trigger Inundation & Rail Damage - OdishaPlus — https://news.google.com/rss/articles/CBMihAFBVV95cUxOVEZVSTZDeURpZWp0YkticlAwcS1kUVRNWWVUelBZYWtTdUNQakN0d3Z2bHNIb2JYVlFzOW1CNGpFcnRaNjByaGZCVjZPQ21tY3hKRWNmZHN4TFhYNGRHU2tWcjZOZG9ydC1mTE9aMmVCVXR6cEd3Q092dkpDdndZSmIwdWk?oc=5
- Four districts in flood grip; over one lakh affected in Odisha - The New Indian Express — https://news.google.com/rss/articles/CBMivAFBVV95cUxONW9wWmN1V29hZDB5UWZvZEw0X2NrVjV0dElPaFVPa3A2OExtS3gyNXhuOEZtcHpaOWpsQVRvNmtDMF95dzQwYjEtZDVjeng3V0s1Qk1yVTlod092Z1pDZTloTU9PRXhGZHN2MGNJYTd1ek9JUlhQeGNoTkRBZnQtUzZfbm42c3A3T0NzbXVHdXJtVHVyaTRwZ21GZGx2c0xBSDEzV1ByaXB1UXdhOVk3TXZsOG9JS2lIWFFFd9IBygFBVV95cUxNODcwUVpfUWpJTWNQalF0WmpsT1pQZFM3ZzEtY0JyY0dXdzFpOGJRbVROVk5lOXZNSFJQQ0piQTRuYTkwa1ZURk11c2pnMGVLWGc3UzZqSlBGMmlwTXRmeW9EUVZYV3MzRXpDZVVZOEQ1UFcyVkhaSXhQdmphUy1zbHBTSFdzNFByTTBhVmoxYzB6WG5UN3M5N3hsWkJPRHY0d29HN0R4Z2dEM3FmOVdRMzQteXhIb1hqLWpyQ2xnNUVmeXlVTEdGSVdn?oc=5
- Kamakhya Superfast Express Derails Near Nergundi In Odisha | Akashvani News - newsonair.gov.in — https://news.google.com/rss/articles/CBMijAFBVV95cUxOXzdSYzV2YmowTHZqQ01DYVB6Nm1IMTl0N1ByNlR6RXUyNXB0VURwUDhaWlEwcWpYT1NZdjVVbjlPMU5oWGlEQnlmM18xQkcwaF9KcEdQUHQyeE1UTXhuam9xSXk0bnlRMWRSbkowdjFxUFhyMkdnaHdsRHRIaGN6ZVczbWNtMHRCOHowVg?oc=5
- 45 Indian coal power plants have critical low fuel, government data shows - ET EnergyWorld — https://news.google.com/rss/articles/CBMi0gFBVV95cUxOZzdFeEJBSXlrWkl1d0lmS0NPN1ZnNVVHa29kUmlVc1dXUTBOMVc2a09rTng0bTh3Z18wUWdrUjIwUnJvd05xbFhxcjVZN2FZbW55b3JEZ1hPRzJtMktqVTBqVjdxdzlFQWg0WGdyX2Z2dmN5UHhZaWdXVWw0RlNKYng4QTBHSV9ISmtjUHI4NElDT2lReDR3Qy0tTmNjNG9YSnZ0dW1aSUxFaHExUEFzOXoyU1Fod2lpTXlSZzZhNXkxWmYwTUg3eFVsTTYtQ3Y1M2fSAdcBQVVfeXFMTko4VHJmM3JRS1BDZXBMakxRV1NqMTgyNnNxVUpZcHZyRnY5ejJZYVg1VXdVS21kMmR3dTI4bi1iTmVuS1J4bW5UMmUxdjNLR0dKX1lEdFZ0QjVQUkNGSUVjNnhYSEJSTXAzb2NjVUFNWklSZXFBcHE5SmR6R3VXaWRjaVZWakwyVnlaMkp1OFZWbnBkZlZCU3Q0UEtEU0hmTndSU3FjRTVKUWg2c0xmMjV5WnZlaHBhZm50UFVNZ2psU3JZN0MySGZEdkRIb3hqdXpFb3c4aFk?oc=5
- Trains Come Face To Face In Odisha's Bhubaneswar, Probe Ordered - ETV Bharat — https://news.google.com/rss/articles/CBMisAFBVV95cUxPelh5NmswZUQwblh5SVJsRi16eUc0MUt2eEdUeGRDd1g0NGJQTVFNV3lQTWo1d0tTTGV6eXkyU1Jkelo3X04yV3B3UlM5LUYwUHBCaWpGSjVyN280by1BQ0g4bGt6QlJLYTNsMEtfMXZZRTlwdjNGcDhSWHVubU5EdnVZWU8yNFhQUVBKU016OVc3dXpOM3FpWEV4Y2NORTZEbTFQcVdwY1dKTUZ2a2ZRUtIBtgFBVV95cUxNT3ZIT3JOMEpreFBvdk9rekw3bm1zdFBmSlpzUXBzdnpkcExGODQxWTMya3BIeE9vV00yRU9QWWhxLXBpTWd3UDBSRG5ZS1prTjJmdDczX0I2ak9lTW9FQXBWTVJ1dnVBb0x4NV95VGZzcmhzeE9FWTdZSmVCa3BTbUx6U3VxMkJkQTJMMjNNUzFJaFA5UnJ4anZ3eFBrMUdBT0hUTmZFQ3FKTGVVRWpNbmEzYmtfUQ?oc=5
- BJD to raise MPLADS hurdles, coal royalty, textbook errors during Parliament Monsoon Session - ThePrint — https://news.google.com/rss/articles/CBMiwwFBVV95cUxPZ0Z0OVRDY3NrMVR0bmlCbVZCTnh3NlF4Tk5yV0k5SVVLUjNabE10ekZVVHVpQUdYUmFid3h2UXFZWTRwU0owdTlnQnVYR21lLWVWRDJPc0lYUmZFQmRxdGdwVk5OWjBieWZMWl8wTGJmUkZveVVzU25HMTFKUElaNEh6VFdCbmtqcy1yRjFVdzZ2SkZjYTJNOXF6blMyQXRQSzFrMXg3TVN6V2kwOHlHSmVIYTR0S01fSUlDeTVRdENJOTTSAcgBQVVfeXFMTmZqem4xeFYtRTV1em9PQVg0X1ZBd3NWWnIwczhmdnltS2l0UTNod2ZNV1JWNkFyVXdDODlYdXl0Qnk0ZUUxbzBVVHBpdkE2dUVQODFJd2tUb051aTNWaThlYWg5Zlo0bTZQTW1raW54d1Rpd0lYOTRwM2kwTDMzMllGaTF4d0RQRDJnLWdVWkNYUFFzMk9YTVNxLXRRT0VDT0tCRGRGMFZWY1BhNjlaRHJPekhGZ3p0WGNBWlVEY0dxMDlMR1JNNEI?oc=5
- Rainwater floods railway tunnel in Odisha, four workers rescued - The New Indian Express — https://news.google.com/rss/articles/CBMivgFBVV95cUxOU2oybjY3VTRtU2ZXNlEtY0gwRUdfYURXc0tFWUFaWGtqTjVrQ1FPWGRFbEg4M3k2VkNydVhscHhxU1AtY1lKOFl5aXYtTVgzS1FDY3BrWFVOMWY3bTBTYWxXNXFJT0hKUGo2cTllMFczbHpZdFY5WGhqZUEwSEF2bnlnZVFRS3R2cGx3SXE2RERrNDdpSDA5OXp6ZGQtQWdHa2pQSnUybHhweTZmcWFWVWprTjJqQ1lsbTlhcGtn0gHLAUFVX3lxTFB4cXJOTnpsLUsyY3J5MU9rRzF3RTNXWC14dUVHZEtpSzdjNW5lblNya2V2b0NqTmVLQ2hXQ0FOaTJ3Szd4b1c2N05UNHpIQk5lVm1NUzRRdFdCTUtyS1Q5Q3drOUVzdS1PZGNXM0VJdzNySkNQcS01b296OHA2V1ZKbGtSb2pJd0pyMHZ1cU5xYVZ5YkhITmQyVUEwWDd0bExOSXFycUVRTGZ2YVlHVUxISjVGdkx1T2JuSVJWeGVQeGE5R1c0X1hEUFZj?oc=5