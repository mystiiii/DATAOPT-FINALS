from .db_helper import execute_query

def get_top_customers(limit=10):
    sql = f"""
    SELECT TOP ({limit})
        c.CustomerID,
        COALESCE(p.FirstName + ' ' + p.LastName, s.Name) AS CustomerName,
        CASE WHEN c.StoreID IS NOT NULL THEN 'Store (B2B)' ELSE 'Individual (B2C)' END AS CustomerType,
        COUNT(soh.SalesOrderID) AS Orders,
        SUM(soh.TotalDue) AS TotalSpent
    FROM Sales.Customer c
    JOIN Sales.SalesOrderHeader soh ON soh.CustomerID = c.CustomerID
    LEFT JOIN Person.Person p ON p.BusinessEntityID = c.PersonID
    LEFT JOIN Sales.Store s ON s.BusinessEntityID = c.StoreID
    GROUP BY c.CustomerID, p.FirstName, p.LastName, s.Name, c.StoreID
    ORDER BY TotalSpent DESC;
    """
    return execute_query(sql)

def get_customer_type_breakdown():
    sql = """
    SELECT
        CASE WHEN c.StoreID IS NOT NULL THEN 'Store / B2B' ELSE 'Individual / B2C' END AS CustomerType,
        COUNT(DISTINCT c.CustomerID) AS TotalCustomers,
        COUNT(DISTINCT soh.CustomerID) AS ActiveBuyers,
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

def get_country_customer_distribution():
    sql = """
    SELECT
        cr.Name AS CountryName,
        COUNT(DISTINCT c.CustomerID) AS CustomerCount,
        COUNT(soh.SalesOrderID) AS TotalOrders,
        SUM(soh.TotalDue) AS TotalRevenue
    FROM Sales.Customer c
    JOIN Sales.SalesOrderHeader soh ON soh.CustomerID = c.CustomerID
    JOIN Person.Address a ON a.AddressID = soh.BillToAddressID
    JOIN Person.StateProvince sp ON sp.StateProvinceID = a.StateProvinceID
    JOIN Person.CountryRegion cr ON cr.CountryRegionCode = sp.CountryRegionCode
    GROUP BY cr.Name
    ORDER BY TotalRevenue DESC;
    """
    return execute_query(sql)

def get_purchase_frequency_buckets():
    sql = """
    SELECT
        FrequencyBucket,
        CustomerSegment,
        COUNT(*) AS CustomerCount,
        SUM(TotalSpent) AS TotalRevenue,
        SUM(OrderCount) AS TotalOrders
    FROM (
        SELECT
            c.CustomerID,
            CASE WHEN c.StoreID IS NOT NULL THEN 'B2B' ELSE 'B2C' END AS CustomerSegment,
            COUNT(soh.SalesOrderID) AS OrderCount,
            SUM(soh.TotalDue) AS TotalSpent,
            CASE
                WHEN COUNT(soh.SalesOrderID) = 1 THEN '1 Order'
                WHEN COUNT(soh.SalesOrderID) BETWEEN 2 AND 3 THEN '2-3 Orders'
                WHEN COUNT(soh.SalesOrderID) BETWEEN 4 AND 6 THEN '4-6 Orders'
                WHEN COUNT(soh.SalesOrderID) BETWEEN 7 AND 12 THEN '7-12 Orders'
                ELSE '13+ Orders'
            END AS FrequencyBucket
        FROM Sales.Customer c
        JOIN Sales.SalesOrderHeader soh ON soh.CustomerID = c.CustomerID
        GROUP BY c.CustomerID, c.StoreID
    ) t
    GROUP BY FrequencyBucket, CustomerSegment
    ORDER BY CASE FrequencyBucket
        WHEN '1 Order' THEN 1
        WHEN '2-3 Orders' THEN 2
        WHEN '4-6 Orders' THEN 3
        WHEN '7-12 Orders' THEN 4
        ELSE 5
    END, CustomerSegment;
    """
    return execute_query(sql)

def get_customer_trends_by_year():
    sql = """
    SELECT
        YEAR(soh.OrderDate) AS [Year],
        CASE WHEN c.StoreID IS NOT NULL THEN 'Store / B2B' ELSE 'Individual / B2C' END AS CustomerType,
        COUNT(DISTINCT c.CustomerID) AS ActiveCustomers,
        COUNT(soh.SalesOrderID) AS TotalOrders,
        SUM(soh.TotalDue) AS TotalRevenue
    FROM Sales.Customer c
    JOIN Sales.SalesOrderHeader soh ON soh.CustomerID = c.CustomerID
    GROUP BY YEAR(soh.OrderDate), CASE WHEN c.StoreID IS NOT NULL THEN 'Store / B2B' ELSE 'Individual / B2C' END
    ORDER BY [Year], CustomerType;
    """
    return execute_query(sql)


def get_customer_demographics_breakdown():
    sql = """
    SELECT
        'B2B' AS Segment,
        'specialty' AS Dimension,
        d.Specialty AS GroupLabel,
        0 AS SortOrder,
        COUNT(DISTINCT c.CustomerID) AS ActiveBuyers,
        COUNT(soh.SalesOrderID) AS TotalOrders,
        SUM(soh.TotalDue) AS TotalRevenue,
        CASE WHEN COUNT(DISTINCT c.CustomerID) > 0
             THEN SUM(soh.TotalDue) / COUNT(DISTINCT c.CustomerID)
             ELSE 0 END AS AvgSpendPerBuyer
    FROM Sales.Customer c
    JOIN Sales.SalesOrderHeader soh ON soh.CustomerID = c.CustomerID
    JOIN Sales.vStoreWithDemographics d ON d.BusinessEntityID = c.StoreID
    WHERE c.StoreID IS NOT NULL AND d.Specialty IS NOT NULL
    GROUP BY d.Specialty

    UNION ALL

    SELECT
        'B2B' AS Segment,
        'business_type' AS Dimension,
        CASE d.BusinessType
            WHEN 'OS' THEN 'Warehouse (OS)'
            WHEN 'BM' THEN 'Value Added Reseller (BM)'
            WHEN 'BS' THEN 'Specialty Bike Shop (BS)'
            ELSE d.BusinessType
        END AS GroupLabel,
        0 AS SortOrder,
        COUNT(DISTINCT c.CustomerID) AS ActiveBuyers,
        COUNT(soh.SalesOrderID) AS TotalOrders,
        SUM(soh.TotalDue) AS TotalRevenue,
        CASE WHEN COUNT(DISTINCT c.CustomerID) > 0
             THEN SUM(soh.TotalDue) / COUNT(DISTINCT c.CustomerID)
             ELSE 0 END AS AvgSpendPerBuyer
    FROM Sales.Customer c
    JOIN Sales.SalesOrderHeader soh ON soh.CustomerID = c.CustomerID
    JOIN Sales.vStoreWithDemographics d ON d.BusinessEntityID = c.StoreID
    WHERE c.StoreID IS NOT NULL AND d.BusinessType IS NOT NULL
    GROUP BY d.BusinessType

    UNION ALL

    SELECT
        'B2C' AS Segment,
        'income' AS Dimension,
        CASE d.YearlyIncome
            WHEN '0-25000' THEN 'Under $25K'
            WHEN '25001-50000' THEN '$25K–$50K'
            WHEN '50001-75000' THEN '$50K–$75K'
            WHEN '75001-100000' THEN '$75K–$100K'
            WHEN 'greater than 100000' THEN '$100K+'
            ELSE d.YearlyIncome
        END AS GroupLabel,
        CASE d.YearlyIncome
            WHEN '0-25000' THEN 1
            WHEN '25001-50000' THEN 2
            WHEN '50001-75000' THEN 3
            WHEN '75001-100000' THEN 4
            WHEN 'greater than 100000' THEN 5
            ELSE 9
        END AS SortOrder,
        COUNT(DISTINCT c.CustomerID) AS ActiveBuyers,
        COUNT(soh.SalesOrderID) AS TotalOrders,
        SUM(soh.TotalDue) AS TotalRevenue,
        CASE WHEN COUNT(DISTINCT c.CustomerID) > 0
             THEN SUM(soh.TotalDue) / COUNT(DISTINCT c.CustomerID)
             ELSE 0 END AS AvgSpendPerBuyer
    FROM Sales.Customer c
    JOIN Sales.SalesOrderHeader soh ON soh.CustomerID = c.CustomerID
    JOIN Sales.vPersonDemographics d ON d.BusinessEntityID = c.PersonID
    WHERE c.StoreID IS NULL AND d.YearlyIncome IS NOT NULL
    GROUP BY d.YearlyIncome

    UNION ALL

    SELECT
        'B2C' AS Segment,
        'occupation' AS Dimension,
        d.Occupation AS GroupLabel,
        0 AS SortOrder,
        COUNT(DISTINCT c.CustomerID) AS ActiveBuyers,
        COUNT(soh.SalesOrderID) AS TotalOrders,
        SUM(soh.TotalDue) AS TotalRevenue,
        CASE WHEN COUNT(DISTINCT c.CustomerID) > 0
             THEN SUM(soh.TotalDue) / COUNT(DISTINCT c.CustomerID)
             ELSE 0 END AS AvgSpendPerBuyer
    FROM Sales.Customer c
    JOIN Sales.SalesOrderHeader soh ON soh.CustomerID = c.CustomerID
    JOIN Sales.vPersonDemographics d ON d.BusinessEntityID = c.PersonID
    WHERE c.StoreID IS NULL AND d.Occupation IS NOT NULL
    GROUP BY d.Occupation;
    """
    return execute_query(sql)
