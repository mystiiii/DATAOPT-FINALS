from .db_helper import execute_query

def get_product_margins(limit=15):
    sql = f"""
    SELECT TOP ({limit})
        p.ProductID,
        p.Name AS ProductName,
        pc.Name AS Category,
        p.StandardCost,
        p.ListPrice,
        (p.ListPrice - p.StandardCost) AS Margin,
        CASE WHEN p.ListPrice > 0 
             THEN ROUND(((p.ListPrice - p.StandardCost) / p.ListPrice) * 100, 2) 
             ELSE 0 END AS MarginPercentage
    FROM Production.Product p
    LEFT JOIN Production.ProductSubcategory ps ON ps.ProductSubcategoryID = p.ProductSubcategoryID
    LEFT JOIN Production.ProductCategory pc ON pc.ProductCategoryID = ps.ProductCategoryID
    WHERE p.ListPrice > 0
    ORDER BY MarginPercentage DESC;
    """
    return execute_query(sql)

def get_vendor_purchasing_spend(limit=10):
    sql = f"""
    SELECT TOP ({limit})
        v.BusinessEntityID AS VendorID,
        v.Name AS VendorName,
        COUNT(poh.PurchaseOrderID) AS PurchaseOrdersCount,
        SUM(poh.TotalDue) AS TotalSpent
    FROM Purchasing.Vendor v
    JOIN Purchasing.PurchaseOrderHeader poh ON poh.VendorID = v.BusinessEntityID
    GROUP BY v.BusinessEntityID, v.Name
    ORDER BY TotalSpent DESC;
    """
    return execute_query(sql)

def get_standard_cost_history(limit=24):
    sql = f"""
    SELECT TOP ({limit})
        p.ProductID,
        p.Name AS ProductName,
        pch.StartDate,
        pch.EndDate,
        pch.StandardCost
    FROM Production.ProductCostHistory pch
    JOIN Production.Product p ON p.ProductID = pch.ProductID
    WHERE p.ProductID IN (
        SELECT ProductID
        FROM Production.ProductCostHistory
        GROUP BY ProductID
        HAVING COUNT(*) >= 2
    )
    ORDER BY p.Name, pch.StartDate;
    """
    rows = execute_query(sql) or []
    prev_by_product = {}
    for row in rows:
        pid = row.get('ProductID') or row.get('ProductName')
        curr_cost = float(row.get('StandardCost') or 0)
        prev_cost = prev_by_product.get(pid)
        if prev_cost and prev_cost > 0:
            row['VariancePct'] = round(((curr_cost - prev_cost) / prev_cost) * 100, 1)
        else:
            row['VariancePct'] = None
        prev_by_product[pid] = curr_cost
    return rows

def get_category_cost_summary():
    sql = """
    SELECT
        pc.Name AS Category,
        COUNT(DISTINCT p.ProductID) AS ProductCount,
        AVG(p.StandardCost) AS AvgStandardCost,
        AVG(p.ListPrice) AS AvgListPrice,
        SUM(sod.OrderQty * p.StandardCost) AS TotalCOGS,
        SUM(sod.LineTotal) AS TotalRevenue,
        CASE WHEN SUM(sod.LineTotal) > 0
             THEN ROUND(((SUM(sod.LineTotal) - SUM(sod.OrderQty * p.StandardCost)) / SUM(sod.LineTotal)) * 100, 1)
             ELSE 0 END AS MarginPercentage
    FROM Sales.SalesOrderDetail sod
    JOIN Production.Product p ON p.ProductID = sod.ProductID
    JOIN Production.ProductSubcategory ps ON ps.ProductSubcategoryID = p.ProductSubcategoryID
    JOIN Production.ProductCategory pc ON pc.ProductCategoryID = ps.ProductCategoryID
    GROUP BY pc.Name
    ORDER BY TotalRevenue DESC;
    """
    return execute_query(sql)

def get_purchasing_spend_by_year():
    sql = """
    SELECT
        YEAR(poh.OrderDate) AS [Year],
        COUNT(poh.PurchaseOrderID) AS PurchaseOrdersCount,
        SUM(poh.SubTotal) AS SubTotal,
        SUM(poh.Freight) AS FreightCost,
        SUM(poh.TotalDue) AS TotalSpent
    FROM Purchasing.PurchaseOrderHeader poh
    GROUP BY YEAR(poh.OrderDate)
    ORDER BY [Year];
    """
    return execute_query(sql)


def get_cogs_trend_by_year_category():
    """Return annual manufacturing COGS, revenue, and units sold grouped by category."""
    sql = """
    SELECT
        YEAR(soh.OrderDate) AS [Year],
        pc.Name AS Category,
        SUM(sod.OrderQty) AS UnitsSold,
        SUM(sod.OrderQty * p.StandardCost) AS TotalCOGS,
        SUM(sod.LineTotal) AS TotalRevenue
    FROM Sales.SalesOrderHeader soh
    JOIN Sales.SalesOrderDetail sod ON sod.SalesOrderID = soh.SalesOrderID
    JOIN Production.Product p ON p.ProductID = sod.ProductID
    JOIN Production.ProductSubcategory ps ON ps.ProductSubcategoryID = p.ProductSubcategoryID
    JOIN Production.ProductCategory pc ON pc.ProductCategoryID = ps.ProductCategoryID
    GROUP BY YEAR(soh.OrderDate), pc.Name
    ORDER BY [Year], TotalCOGS DESC;
    """
    return execute_query(sql)


def get_top_cost_products(per_category=10):
    """Return the top COGS-contributing products within each product category."""
    per_cat = max(1, int(per_category))
    sql = f"""
    WITH ProductCOGS AS (
        SELECT
            p.ProductID,
            p.Name AS ProductName,
            pc.Name AS Category,
            p.StandardCost AS UnitStandardCost,
            SUM(sod.OrderQty) AS UnitsSold,
            SUM(sod.OrderQty * p.StandardCost) AS TotalCOGS,
            SUM(sod.LineTotal) AS TotalRevenue,
            CASE WHEN SUM(sod.LineTotal) > 0
                 THEN ROUND(((SUM(sod.LineTotal) - SUM(sod.OrderQty * p.StandardCost)) / SUM(sod.LineTotal)) * 100, 1)
                 ELSE 0 END AS MarginPercentage,
            ROW_NUMBER() OVER (
                PARTITION BY pc.Name
                ORDER BY SUM(sod.OrderQty * p.StandardCost) DESC
            ) AS rn
        FROM Sales.SalesOrderDetail sod
        JOIN Production.Product p ON p.ProductID = sod.ProductID
        JOIN Production.ProductSubcategory ps ON ps.ProductSubcategoryID = p.ProductSubcategoryID
        JOIN Production.ProductCategory pc ON pc.ProductCategoryID = ps.ProductCategoryID
        GROUP BY p.ProductID, p.Name, pc.Name, p.StandardCost
    )
    SELECT
        ProductID,
        ProductName,
        Category,
        UnitStandardCost,
        UnitsSold,
        TotalCOGS,
        TotalRevenue,
        MarginPercentage
    FROM ProductCOGS
    WHERE rn <= {per_cat}
    ORDER BY TotalCOGS DESC;
    """
    return execute_query(sql)
