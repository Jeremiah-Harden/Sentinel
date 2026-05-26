# Workflow: Scrape DailyRemote Jobs → Excel

## Objective
Scrape job listings from DailyRemote for a given search query and export all relevant fields to an Excel file for review and tracking.

## Inputs
| Input | Description | Default |
|-------|-------------|---------|
| `search` | Search query string | *(required)* |
| `page` | Page number of results | `1` |
| `output` | Output Excel file path | `.tmp/jobs.xlsx` |

## Tool
`tools/scrape_jobs.py`

## Steps

1. **Resolve inputs** — confirm the search query with the user if not provided.
2. **Run the tool**:
   ```
   python tools/scrape_jobs.py --search "<query>" --page <n> --output .tmp/jobs.xlsx
   ```
3. **Verify output** — confirm `.tmp/jobs.xlsx` was created and contains the expected number of rows.
4. **Deliver** — open or share the Excel file with the user.

## Output
`.tmp/jobs.xlsx` with the following columns:
- Job Title
- Company Name
- Location
- Job Type
- Salary
- Date Posted
- Tags / Skills
- Job Description
- Requirements
- Apply URL
- DailyRemote URL

## Edge Cases
| Scenario | Handling |
|----------|----------|
| No listings found | Tool prints a message and exits cleanly — check the search term or try page 1 |
| Company name missing | Falls back to `N/A` — some listings may not expose company name even on detail page |
| Apply URL missing | Falls back to `N/A` — use the DailyRemote URL column to visit the posting manually |
| Firecrawl rate limit / API error | Re-run the tool; Firecrawl errors surface as exceptions with descriptive messages |
| `.tmp/` directory missing | Tool creates it automatically |

## Self-Improvement
If a field is consistently missing or wrong (e.g., company names always `N/A`), update the `DETAIL_SCHEMA` prompt in `tools/scrape_jobs.py` and re-verify before updating this workflow.
