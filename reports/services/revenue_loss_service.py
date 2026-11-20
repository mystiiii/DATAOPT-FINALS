from .db_helper import execute_query

def get_revenue_and_loss_by_year():
    sql = """
    SELECT
        YEAR(soh.OrderDate) AS [Year],
        COUNT(DISTINCT soh.SalesOrderID) AS OrderCount,
        SUM(sod.OrderQty * sod.UnitPrice) AS GrossAmount,
        SUM(sod.OrderQty * sod.UnitPrice * sod.UnitPriceDiscount) AS DiscountLoss,
        SUM(sod.LineTotal) AS NetRevenue
    FROM Sales.SalesOrderHeader soh
    JOIN Sales.SalesOrderDetail sod ON sod.SalesOrderID = soh.SalesOrderID
    GROUP BY YEAR(soh.OrderDate)
    ORDER BY [Year];
    """
    return execute_query(sql)

def get_production_scrap_loss():
    sql = """
    SELECT
        sr.Name AS ScrapReason,
        COUNT(wo.WorkOrderID) AS ScrapOrders,
        SUM(wo.ScrappedQty) AS TotalScrappedQty,
        SUM(wo.ScrappedQty * p.StandardCost) AS ActualScrapCost
    FROM Production.WorkOrder wo
    JOIN Production.ScrapReason sr ON sr.ScrapReasonID = wo.ScrapReasonID
    JOIN Production.Product p ON p.ProductID = wo.ProductID
    WHERE wo.ScrappedQty > 0
    GROUP BY sr.Name
    ORDER BY TotalScrappedQty DESC;
    """
    return execute_query(sql)

def get_monthly_revenue_and_loss():
    sql = """
    SELECT
        YEAR(soh.OrderDate) AS [Year],
        MONTH(soh.OrderDate) AS [Month],
        COUNT(DISTINCT soh.SalesOrderID) AS OrderCount,
        SUM(sod.OrderQty * sod.UnitPrice) AS GrossAmount,
        SUM(sod.OrderQty * sod.UnitPrice * sod.UnitPriceDiscount) AS DiscountLoss,
        SUM(sod.LineTotal) AS NetRevenue,
        CASE WHEN SUM(sod.OrderQty * sod.UnitPrice) > 0
             THEN ROUND((SUM(sod.OrderQty * sod.UnitPrice * sod.UnitPriceDiscount) / SUM(sod.OrderQty * sod.UnitPrice)) * 100, 2)
             ELSE 0 END AS DiscountRatePct
    FROM Sales.SalesOrderHeader soh
    JOIN Sales.SalesOrderDetail sod ON sod.SalesOrderID = soh.SalesOrderID
    GROUP BY YEAR(soh.OrderDate), MONTH(soh.OrderDate)
    ORDER BY [Year], [Month];
    """
    return execute_query(sql)

def get_discount_loss_by_category():
    sql = """
    SELECT
        pc.Name AS Category,
        YEAR(soh.OrderDate) AS [Year],
        SUM(sod.OrderQty * sod.UnitPrice) AS GrossAmount,
        SUM(sod.OrderQty * sod.UnitPrice * sod.UnitPriceDiscount) AS DiscountLoss,
        SUM(sod.LineTotal) AS NetRevenue,
        CASE WHEN SUM(sod.OrderQty * sod.UnitPrice) > 0
             THEN ROUND((SUM(sod.OrderQty * sod.UnitPrice * sod.UnitPriceDiscount) / SUM(sod.OrderQty * sod.UnitPrice)) * 100, 2)
             ELSE 0 END AS DiscountRatePct
    FROM Sales.SalesOrderHeader soh
    JOIN Sales.SalesOrderDetail sod ON sod.SalesOrderID = soh.SalesOrderID
    JOIN Production.Product p ON p.ProductID = sod.ProductID
    JOIN Production.ProductSubcategory ps ON ps.ProductSubcategoryID = p.ProductSubcategoryID
    JOIN Production.ProductCategory pc ON pc.ProductCategoryID = ps.ProductCategoryID
    GROUP BY pc.Name, YEAR(soh.OrderDate)
    ORDER BY [Year], DiscountLoss DESC;
    """
    return execute_query(sql)
