# Technical and Analytical Documentation
**AdventureWorks Data Analytics and Reporting System (DATAOPT — Group 2, BTIS1)**

---

## 1. System Architecture

The application uses a **dual-database Django 5.x architecture** ([config/settings.py](file:///Users/miguelherreros/DATAOPT-FINALS/config/settings.py), [config/db_router.py](file:///Users/miguelherreros/DATAOPT-FINALS/config/db_router.py)):
1. **`default` (SQLite — `db.sqlite3`)**: Stores Django authentication (`User`, `Group`), `accounts.UserProfile`, and governance models (`SavedReportPreset`, `ReportAnnotation`, `DataQualityLog`, `AuditLog`).
2. **`adventureworks` (Microsoft SQL Server — `AdventureWorks2019`)**: Read-only analytical source queried via `pyodbc` in [reports/services/db_helper.py](file:///Users/miguelherreros/DATAOPT-FINALS/reports/services/db_helper.py).

**Application layers:**
- `accounts/` — Authentication (`login_view`, `logout_view`), RBAC `Role` choices, and `@role_required` decorator.
- `reports/` — Analytical SQL service modules (`sales_service.py`, `customer_service.py`, `revenue_loss_service.py`, `cost_service.py`), view controllers (`views.py`), and interactive Chart.js templates.
- `governance/` — Saved filter presets, analytical notes, data quality logs, and administrator audit trail (`audit_log_view`).

---

## 2. Role-Based Access Control (RBAC) Matrix

Access is enforced server-side via `@role_required` ([accounts/decorators.py](file:///Users/miguelherreros/DATAOPT-FINALS/accounts/decorators.py)) and `_require_governance_access` ([reports/views.py](file:///Users/miguelherreros/DATAOPT-FINALS/reports/views.py)). Unauthorized attempts return HTTP `403` and record an `ACCESS_DENIED` entry in `AuditLog`.

| Role | Dashboard | Sales Report | Customer Profile | Revenue & Loss | Cost Report | Presets & Notes (View / Create / Edit / Delete) | Audit Log & Admin |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Administrator** | Full company view | View | View | View | View | Full (any record) | Full |
| **Manager** | Full company view | View | View | View | View | Full (any record) | Audit Log (Manager, Supervisor, Employee); Admin Users denied (`403`) |
| **Supervisor** | Sales + Customer view | View | View | Denied (`403`) | Denied (`403`) | Sales & Customers (own records only) | Audit Log (Supervisor, Employee); Admin Users denied (`403`) |
| **Employee** | Sales-only view | View | Denied (`403`) | Denied (`403`) | Denied (`403`) | View-only (`403` on mutations) | No |

---

## 3. Data Map & Table Lineage

| Module | AdventureWorks Tables | Join Keys | Purpose |
| :--- | :--- | :--- | :--- |
| **Sales** | `Sales.SalesOrderHeader`, `Sales.SalesOrderDetail`, `Sales.SalesTerritory`, `Production.Product`, `Production.ProductSubcategory`, `Production.ProductCategory` | `SalesOrderID`, `TerritoryID`, `ProductID`, `ProductSubcategoryID`, `ProductCategoryID` | Monthly/annual revenue trends, category & subcategory breakdown, territory totals, top/bottom SKUs |
| **Customers** | `Sales.Customer`, `Sales.SalesOrderHeader`, `Person.Person`, `Sales.Store`, `Sales.vStoreWithDemographics`, `Sales.vPersonDemographics`, `Person.Address`, `Person.StateProvince`, `Person.CountryRegion` | `CustomerID`, `PersonID`, `StoreID`, `BusinessEntityID`, `BillToAddressID`, `AddressID`, `StateProvinceID`, `CountryRegionCode` | B2B vs. B2C segmentation, store specialty & business-type profiles, B2C income & occupation demographics, geographic distribution, top accounts |
| **Revenue & Loss** | `Sales.SalesOrderHeader`, `Sales.SalesOrderDetail`, `Production.Product`, `Production.ProductSubcategory`, `Production.ProductCategory`, `Production.WorkOrder`, `Production.ScrapReason` | `SalesOrderID`, `ProductID`, `ProductSubcategoryID`, `ProductCategoryID`, `ScrapReasonID` | Gross-to-net waterfall, discount leakage by period/category, factory scrap Pareto |
| **Cost** | `Sales.SalesOrderHeader`, `Sales.SalesOrderDetail`, `Production.Product`, `Production.ProductSubcategory`, `Production.ProductCategory`, `Production.ProductCostHistory`, `Purchasing.Vendor`, `Purchasing.PurchaseOrderHeader` | `SalesOrderID`, `ProductID`, `ProductSubcategoryID`, `ProductCategoryID`, `VendorID` (`BusinessEntityID`) | Category COGS vs. revenue & margin %, manufacturing cost drivers, vendor spending, standard cost audit |

---

## 4. Calculation Definitions

- **Gross Sales (Order Lines):** `SUM(sod.OrderQty * sod.UnitPrice)`
- **Discount Loss:** `SUM(sod.OrderQty * sod.UnitPrice * sod.UnitPriceDiscount)`
- **Discount Rate %:** `(DiscountLoss / GrossAmount) * 100`
- **Net Revenue (Merchandise):** `SUM(sod.LineTotal)` (net of line discounts, before tax and freight)
- **Customer / Territory Sales (`TotalDue`):** `SUM(soh.TotalDue)` (includes tax and freight, as recorded on order headers)
- **Manufacturing COGS:** `SUM(sod.OrderQty * p.StandardCost)`
- **Gross Profit:** `SUM(sod.LineTotal - (sod.OrderQty * p.StandardCost))`
- **Margin %:** `((TotalRevenue - TotalCOGS) / TotalRevenue) * 100` (or `((ListPrice - StandardCost) / ListPrice) * 100` for catalog items)
- **Actual Scrap Cost:** `SUM(wo.ScrappedQty * p.StandardCost)` where `wo.ScrappedQty > 0`
- **Avg Sales / Buyer:** `TotalRevenue / ActiveBuyers` (`COUNT(DISTINCT soh.CustomerID)`)

---

## 5. Known Data Limitations & Governance Controls

1. **No returns or refunds table (`HIGH`):** AdventureWorks2019 does not track customer returns; losses are modeled using line-item discounts (`UnitPriceDiscount`) and production scrap (`WorkOrder.ScrappedQty * StandardCost`).
2. **Split customer schema (`MEDIUM`):** `Sales.Customer` links either to `Person.Person` (B2C) or `Sales.Store` (B2B). Queries use `LEFT JOIN` with `COALESCE(p.FirstName + ' ' + p.LastName, s.Name)` so neither segment is dropped.
3. **Partial 2014 data (`INFO`):** Order records end in June 2014; `2014` is labeled `(Jan to Jun)` in period selectors and compared on a monthly basis.
4. **Revenue scope difference (`INFO`):** Line-item reports (`Sales`, `Revenue & Loss`, `Cost`) use `LineTotal` (merchandise net of discounts), whereas order-header reports (`Territories`, `Customers`) use `TotalDue` (inclusive of tax and freight).

---

## 6. Analytical Summary & Business Recommendations

- **Sales:** Focus inventory and promotions on top-performing categories and territories while bundling or rationalizing lowest-velocity SKUs.
- **Customers:** B2B store accounts generate the majority of revenue with high per-buyer lifetime sales, whereas B2C individuals drive order volume with many 1-order buyers. Prioritize B2B account retention and targeted B2C repeat-purchase campaigns.
- **Revenue & Loss:** Track discount spikes by month and category to prevent margin erosion, and address top work-order scrap reasons through targeted quality inspections.
- **Cost:** Monitor categories and products with high COGS or negative margins (where standard cost exceeds discounted selling price) and consolidate purchasing leverage with top suppliers.
