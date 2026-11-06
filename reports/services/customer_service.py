from .db_helper import execute_query

def get_top_customers(limit=10):
    sql = f"""
    SELECT TOP ({limit})
        c.CustomerID,
        COALESCE(p.FirstName + ' ' + p.LastName, s.Name) AS CustomerName,
        COUNT(soh.SalesOrderID) AS Orders,
        SUM(soh.TotalDue) AS TotalSpent
    FROM Sales.Customer c
    JOIN Sales.SalesOrderHeader soh ON soh.CustomerID = c.CustomerID
    LEFT JOIN Person.Person p ON p.BusinessEntityID = c.PersonID
    LEFT JOIN Sales.Store s ON s.BusinessEntityID = c.StoreID
    GROUP BY c.CustomerID, p.FirstName, p.LastName, s.Name
    ORDER BY TotalSpent DESC;
    """
    return execute_query(sql)

def get_customer_type_breakdown():
    sql = """
    SELECT
        CASE WHEN c.StoreID IS NOT NULL THEN 'Store / B2B' ELSE 'Individual / B2C' END AS CustomerType,
        COUNT(DISTINCT c.CustomerID) AS TotalCustomers,
        COUNT(soh.SalesOrderID) AS TotalOrders,
        SUM(soh.TotalDue) AS TotalRevenue
    FROM Sales.Customer c
    LEFT JOIN Sales.SalesOrderHeader soh ON soh.CustomerID = c.CustomerID
    GROUP BY CASE WHEN c.StoreID IS NOT NULL THEN 'Store / B2B' ELSE 'Individual / B2C' END;
    """
    return execute_query(sql)

def get_customer_geographic_distribution(limit=6):
    sql = f"""
    SELECT TOP ({limit})
        sp.Name AS RegionName,
        cr.Name AS CountryName,
        COUNT(DISTINCT c.CustomerID) AS CustomerCount,
        SUM(soh.TotalDue) AS TotalRevenue
    FROM Sales.Customer c
    JOIN Sales.SalesOrderHeader soh ON soh.CustomerID = c.CustomerID
    JOIN Person.Address a ON a.AddressID = soh.BillToAddressID
    JOIN Person.StateProvince sp ON sp.StateProvinceID = a.StateProvinceID
    JOIN Person.CountryRegion cr ON cr.CountryRegionCode = sp.CountryRegionCode
    GROUP BY sp.Name, cr.Name
    ORDER BY TotalRevenue DESC;
    """
    return execute_query(sql)
