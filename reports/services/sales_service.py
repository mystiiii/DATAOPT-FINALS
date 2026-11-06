from .db_helper import execute_query

def get_sales_by_category_and_year():
    sql = """
    SELECT
        pc.Name AS Category,
        YEAR(soh.OrderDate) AS [Year],
        SUM(sod.LineTotal) AS Revenue,
        SUM(sod.OrderQty) AS UnitsSold
    FROM Sales.SalesOrderHeader soh
    JOIN Sales.SalesOrderDetail sod ON sod.SalesOrderID = soh.SalesOrderID
    JOIN Production.Product p ON p.ProductID = sod.ProductID
    JOIN Production.ProductSubcategory ps ON ps.ProductSubcategoryID = p.ProductSubcategoryID
    JOIN Production.ProductCategory pc ON pc.ProductCategoryID = ps.ProductCategoryID
    GROUP BY pc.Name, YEAR(soh.OrderDate)
    ORDER BY [Year], Revenue DESC;
    """
    return execute_query(sql)

def get_top_selling_products(limit=10):
    sql = f"""
    SELECT TOP ({limit})
        p.ProductID,
        p.Name AS ProductName,
        pc.Name AS Category,
        SUM(sod.LineTotal) AS TotalRevenue,
        SUM(sod.OrderQty) AS TotalQuantity
    FROM Sales.SalesOrderDetail sod
    JOIN Production.Product p ON p.ProductID = sod.ProductID
    JOIN Production.ProductSubcategory ps ON ps.ProductSubcategoryID = p.ProductSubcategoryID
    JOIN Production.ProductCategory pc ON pc.ProductCategoryID = ps.ProductCategoryID
    GROUP BY p.ProductID, p.Name, pc.Name
    ORDER BY TotalRevenue DESC;
    """
    return execute_query(sql)

def get_territory_sales():
    sql = """
    SELECT
        st.Name AS TerritoryName,
        st.[Group] AS TerritoryGroup,
        COUNT(soh.SalesOrderID) AS TotalOrders,
        SUM(soh.TotalDue) AS TotalRevenue
    FROM Sales.SalesTerritory st
    JOIN Sales.SalesOrderHeader soh ON soh.TerritoryID = st.TerritoryID
    GROUP BY st.Name, st.[Group]
    ORDER BY TotalRevenue DESC;
    """
    return execute_query(sql)
