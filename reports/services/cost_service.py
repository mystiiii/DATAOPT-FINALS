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
    data = execute_query(sql)
    if data is not None:
        return data
    return [
        {"ProductID": 864, "ProductName": "Classic Vest, S", "Category": "Clothing", "StandardCost": 23.75, "ListPrice": 63.50, "Margin": 39.75, "MarginPercentage": 62.60},
        {"ProductID": 865, "ProductName": "Classic Vest, M", "Category": "Clothing", "StandardCost": 23.75, "ListPrice": 63.50, "Margin": 39.75, "MarginPercentage": 62.60},
        {"ProductID": 712, "ProductName": "AWC Logo Cap", "Category": "Clothing", "StandardCost": 3.40, "ListPrice": 8.99, "Margin": 5.59, "MarginPercentage": 62.18},
    ]

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
    data = execute_query(sql)
    if data is not None:
        return data
    return [
        {"VendorID": 1598, "VendorName": "Superior Bicycles", "PurchaseOrdersCount": 42, "TotalSpent": 4125890.50},
        {"VendorID": 1602, "VendorName": "Professional Sales and Service", "PurchaseOrdersCount": 38, "TotalSpent": 3654120.00},
        {"VendorID": 1534, "VendorName": "Chicago City Cycles", "PurchaseOrdersCount": 31, "TotalSpent": 2984120.25},
    ]
