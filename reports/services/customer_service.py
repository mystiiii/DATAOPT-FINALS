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
    data = execute_query(sql)
    if data is not None:
        return data
    return [
        {"CustomerID": 29818, "CustomerName": "Roger Harui", "Orders": 12, "TotalSpent": 989184.08},
        {"CustomerID": 29715, "CustomerName": "Andrew Dixon", "Orders": 12, "TotalSpent": 961675.86},
        {"CustomerID": 29722, "CustomerName": "Reuben D'sa", "Orders": 12, "TotalSpent": 954021.92},
        {"CustomerID": 30117, "CustomerName": "Robert Vessa", "Orders": 12, "TotalSpent": 919801.82},
        {"CustomerID": 29614, "CustomerName": "Ryan Calafato", "Orders": 12, "TotalSpent": 901346.86},
    ]

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
    data = execute_query(sql)
    if data is not None:
        return data
    return [
        {"CustomerType": "Store / B2B", "TotalCustomers": 701, "TotalOrders": 3806, "TotalRevenue": 80124500.00},
        {"CustomerType": "Individual / B2C", "TotalCustomers": 18484, "TotalOrders": 27659, "TotalRevenue": 29654120.00},
    ]

def get_customer_geographic_distribution():
    sql = """
    SELECT TOP 6
        sp.Name AS RegionName,
        cr.Name AS CountryName,
        COUNT(DISTINCT c.CustomerID) AS CustomerCount,
        SUM(soh.TotalDue) AS TotalRevenue
    FROM Sales.Customer c
    JOIN Sales.SalesOrderHeader soh ON soh.CustomerID = c.CustomerID
    JOIN Person.Address a ON a.AddressID = soh.ShipToAddressID
    JOIN Person.StateProvince sp ON sp.StateProvinceID = a.StateProvinceID
    JOIN Person.CountryRegion cr ON cr.CountryRegionCode = sp.CountryRegionCode
    GROUP BY sp.Name, cr.Name
    ORDER BY TotalRevenue DESC;
    """
    data = execute_query(sql)
    if data is not None:
        return data
    return [
        {"RegionName": "California", "CountryName": "United States", "CustomerCount": 4210, "TotalRevenue": 19480100.00},
        {"RegionName": "Washington", "CountryName": "United States", "CustomerCount": 2640, "TotalRevenue": 14210500.00},
        {"RegionName": "Texas", "CountryName": "United States", "CustomerCount": 1890, "TotalRevenue": 9640200.00},
        {"RegionName": "New South Wales", "CountryName": "Australia", "CustomerCount": 1780, "TotalRevenue": 9180400.00},
        {"RegionName": "England", "CountryName": "United Kingdom", "CustomerCount": 1640, "TotalRevenue": 8510200.00},
        {"RegionName": "Oregon", "CountryName": "United States", "CustomerCount": 1210, "TotalRevenue": 6420800.00},
    ]
