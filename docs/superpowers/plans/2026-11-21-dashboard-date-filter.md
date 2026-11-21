# Dashboard Month & Custom Date Range Filter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Dashboard's yearly dropdown with **All time**, **Month**, and **Custom date range** filters backed by parameterized SQL queries across all Dashboard KPIs, charts, and explorer tables.

**Architecture:** `dashboard_view` parses GET query parameters (`period`, `month`, `start_date`, `end_date`) into `(start_date, end_date)` bounds and passes them to all service functions in `reports/services/`. A shared helper in `db_helper.py` builds safe `?`-parameterized `>=` / `< (end + 1 day)` SQL clauses. `dashboard.html` renders the new filter toolbar and updates Chart.js/KPI/Explorer scripts to reflect the filtered backend data.

**Tech Stack:** Django 5.1, `pyodbc` / SQL Server (`AdventureWorks2019`), Tailwind CSS, Chart.js 4.

**Spec:** [2026-11-21-dashboard-date-filter-design.md](file:///Users/miguelherreros/DATAOPT-FINALS/docs/superpowers/specs/2026-11-21-dashboard-date-filter-design.md)

## Global Constraints
- Preserve existing service function defaults (`start_date=None, end_date=None`) so `/reports/sales/`, `/reports/customers/`, `/reports/revenue-loss/`, and `/reports/cost/` keep working unchanged.
- Never interpolate user-supplied date strings directly into SQL; always bind parameters via `execute_query(sql, params)`.
- Preserve existing RBAC restrictions in `dashboard_view` (Employee/Supervisor must never receive `ManufacturingCost`, `GrossProfit`, `MarginPercentage`, `scrap`, or `vendor` data).

## Review Focus
- Malformed `month`, `start_date`, or `end_date` GET params: must not raise 500 `ValueError`; fall back to unfiltered `all` with a warning message.
- Reversed custom date range (`start_date > end_date`): swap bounds automatically so valid data is still shown.
- Single-sided custom date range (only `start_date` or only `end_date` supplied): filter with open upper or lower bound instead of failing.
- Empty result set for a date range (e.g. `2015-01`): KPIs/charts render `0` / empty gracefully with no `ZeroDivisionError` or JS crash.
- SQL `DATETIME` end-of-day inclusivity: filtering `end_date=2013-06-30` must include all orders on `2013-06-30` via `< 2013-07-01`.

---

### Task 1: Shared SQL Date Filter Helper (`db_helper.py`)

**Files:**
- Modify: `reports/services/db_helper.py`
- Test: `reports/tests.py`

**Interfaces:**
- Produces: `build_date_filter(column: str, start_date: date | None = None, end_date: date | None = None) -> tuple[str, list[str]]`

- [ ] **Step 1: Write failing tests for `build_date_filter`**
  Add unit tests in `reports/tests.py` verifying:
  - `(None, None)` returns `("", [])`.
  - `(date(2013, 6, 1), date(2013, 6, 30))` returns `("soh.OrderDate >= ? AND soh.OrderDate < ?", ["2013-06-01", "2013-07-01"])`.
  - Single-sided `(date(2013, 6, 1), None)` and `(None, date(2013, 6, 30))` return single bound clauses and params.
- [ ] **Step 2: Run tests to verify they fail**
  Run: `DB_TRUSTED_CONNECTION=no DB_PASSWORD="" .venv/bin/python manage.py test reports.tests.DateFilterHelperTests`
  Expected: FAIL (`ImportError: cannot import name 'build_date_filter'`).
- [ ] **Step 3: Implement `build_date_filter` in `reports/services/db_helper.py`**
  Add `build_date_filter(column, start_date=None, end_date=None)` returning `(clause, params)` using `timedelta(days=1)` for exclusive upper bound `< ?`.
- [ ] **Step 4: Run tests to verify they pass**
  Expected: PASS.

---

### Task 2: Add Parameterized Date Filtering to All Four Service Modules

**Files:**
- Modify: `reports/services/sales_service.py`
- Modify: `reports/services/customer_service.py`
- Modify: `reports/services/revenue_loss_service.py`
- Modify: `reports/services/cost_service.py`
- Test: `reports/tests.py`

**Interfaces:**
- Consumes: `db_helper.build_date_filter`
- Produces:
  - `sales_service.get_sales_by_category_and_year(start_date=None, end_date=None)`
  - `sales_service.get_top_selling_products(limit=10, start_date=None, end_date=None)`
  - `sales_service.get_territory_sales(start_date=None, end_date=None)`
  - `sales_service.get_monthly_sales_trend(start_date=None, end_date=None)`
  - `customer_service.get_top_customers(limit=10, start_date=None, end_date=None)`
  - `customer_service.get_customer_type_breakdown(start_date=None, end_date=None)`
  - `revenue_loss_service.get_revenue_and_loss_by_year(start_date=None, end_date=None)`
  - `revenue_loss_service.get_production_scrap_loss(start_date=None, end_date=None)`
  - `cost_service.get_vendor_purchasing_spend(limit=10, start_date=None, end_date=None)`

- [ ] **Step 1: Write failing tests verifying SQL & bound params**
  Mock `execute_query` (via `pyodbc` mock or `patch`) and assert each service function passes no params when `(None, None)` and passes parameterized `>= ?` / `< ?` bounds when `(start_date, end_date)` are provided (including `Sales.SalesOrderHeader` join in `get_top_selling_products`, `soh.OrderDate` in `get_customer_type_breakdown`, `wo.StartDate` in `get_production_scrap_loss`, and `poh.OrderDate` in `get_vendor_purchasing_spend`).
- [ ] **Step 2: Run tests to verify they fail**
  Expected: FAIL (`TypeError: unexpected keyword argument 'start_date'`).
- [ ] **Step 3: Implement `start_date=None, end_date=None` filtering in all four service files**
  Ensure `execute_query(sql, params or None)` is called cleanly.
- [ ] **Step 4: Run tests to verify they pass**
  Expected: PASS.

---

### Task 3: Dashboard Period Parsing & View Integration (`reports/views.py`)

**Files:**
- Modify: `reports/views.py`
- Test: `reports/tests.py`

**Interfaces:**
- Consumes: Task 2 service signatures
- Produces: `_parse_dashboard_period(query_params)` and updated `dashboard_view` context (`period_mode`, `selected_month`, `start_date_str`, `end_date_str`, `period_label`, `is_filtered`).

- [ ] **Step 1: Write failing tests for `_parse_dashboard_period` and `dashboard_view` GET filters**
  Cover:
  - Default (`all`), `month=2013-06` (`2013-06-01` to `2013-06-30`), `custom` (`start_date=2013-06-05&end_date=2013-06-20`).
  - Reversed custom dates (`start > end` swaps bounds).
  - Single-bound custom dates (`start_date` only / `end_date` only).
  - Malformed `month=invalid` or `start_date=bad` falls back safely to `all` with warning message and status 200.
  - Empty query result sets render status 200 with zero totals (`total_orders=0`, `avg_order=0`, `b2b_pct=0.0`).
  - Verify `dashboard_view` passes `(start_date, end_date)` to all dashboard service calls and respects Employee RBAC stripping.
- [ ] **Step 2: Run tests to verify they fail**
  Expected: FAIL.
- [ ] **Step 3: Implement `_parse_dashboard_period` and update `dashboard_view` in `reports/views.py`**
  Update `total_scrap_loss` and all context variables cleanly.
- [ ] **Step 4: Run tests to verify they pass**
  Expected: PASS.

---

### Task 4: Dashboard UI Toolbar & Chart.js Updates (`templates/reports/dashboard.html`)

**Files:**
- Modify: `templates/reports/dashboard.html`
- Test: `reports/tests.py`

- [ ] **Step 1: Write failing template tests**
  Assert `dashboard` HTML contains `#dashboardPeriodForm`, `#periodModeSelect` (`all`, `month`, `custom`), `#periodMonthInput` (`type="month"`), `#periodStartInput`, `#periodEndInput`, does NOT contain `#globalYearFilter`, and displays the active `period_label` when `?period=month&month=2013-06` is requested.
- [ ] **Step 2: Run tests to verify they fail**
  Expected: FAIL.
- [ ] **Step 3: Update `templates/reports/dashboard.html`**
  - Replace `#globalYearFilter` with the GET form (`All time`, `Month`, `Custom dates` + conditional month/date inputs + `Apply` / `Reset`).
  - Update JS `updateTopKPIs()`, `renderCategoryChart()` (category-level bars when `IS_FILTERED` is true, `FY` grouped bars when `false`), `renderWaterfallChart()`, and `renderVelocityChart()` to use the backend-filtered datasets directly and display `PERIOD_LABEL`.
- [ ] **Step 4: Run full Django test suite**
  Run: `DB_TRUSTED_CONNECTION=no DB_PASSWORD="" .venv/bin/python manage.py test`
  Expected: All tests PASS.
