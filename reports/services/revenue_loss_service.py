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
        SUM(wo.ScrappedQty) AS TotalScrappedQty
    FROM Production.WorkOrder wo
    JOIN Production.ScrapReason sr ON sr.ScrapReasonID = wo.ScrapReasonID
    WHERE wo.ScrappedQty > 0
    GROUP BY sr.Name
    ORDER BY TotalScrappedQty DESC;
    """
    return execute_query(sql)
