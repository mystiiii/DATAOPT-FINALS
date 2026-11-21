# Dashboard Month & Custom Date Range Filter — Design

**Goal:** Replace the Dashboard's yearly `Period` dropdown (`All years`, `2011`–`2014`) with a flexible period filter supporting **All time**, **Specific Month** (`YYYY-MM`), and **Custom Date Range** (`start_date` to `end_date`), backed by parameterized SQL filtering across all Dashboard widgets.

**Architecture:**
- **GET query-parameter filtering on `dashboard_view`:** Submitting the toolbar form reloads `/` with `?period=all`, `?period=month&month=YYYY-MM`, or `?period=custom&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`.
- **Parameterized SQL filtering (`reports/services/`):** Add a shared `build_date_filter(column, start_date=None, end_date=None)` helper in `reports/services/db_helper.py` using `>= ?` and `< ?` (exclusive next-day bound) so `DATETIME` columns include the full `end_date`. Update all dashboard-consumed service functions with optional `start_date=None, end_date=None` keyword parameters (defaulting to `None` so all existing report pages and tests remain untouched).
- **Dashboard UI (`templates/reports/dashboard.html`):** Replace `#globalYearFilter` with a mode selector (`All time` | `Month` | `Custom dates`), conditional `<input type="month">` and `<input type="date">` controls, `Apply` button, and `Reset` link. Update dashboard JS so KPIs, Waterfall, Monthly Trend, Territory Map/Bars, Customers Donut, and Explorer Tables render the backend-filtered data directly, and `categoryChart` switches from multi-year `FY` bars to category bars when a month or custom date range is active.

**Constraints & Edge Cases:**
- `AdventureWorks2019` order dates span `2011-05-31` to `2014-06-30`; inputs set `min`/`max` hints without blocking valid queries.
- Invalid `month` or `start_date`/`end_date` strings fall back safely with a warning message; reversed `start_date > end_date` swaps bounds cleanly; empty query results render `$0` / `0` without division-by-zero errors.
- RBAC stripping for non-managers/non-supervisors (`_strip_fields`, role-gated queries) remains identical.
