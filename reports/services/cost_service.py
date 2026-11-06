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

def get_standard_cost_history(limit=6):
    sql = f"""
    SELECT TOP ({limit})
        p.Name AS ProductName,
        pch.StartDate,
        pch.EndDate,
        pch.StandardCost
    FROM Production.ProductCostHistory pch
    JOIN Production.Product p ON p.ProductID = pch.ProductID
    WHERE p.ProductID IN (779, 782, 783)
    ORDER BY p.Name, pch.StartDate;
    """
    return execute_query(sql)
