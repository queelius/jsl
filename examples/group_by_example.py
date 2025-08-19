#!/usr/bin/env python3
"""
Example demonstrating the group-by function in JSL.

group-by takes a key function and a collection, and returns a dictionary
where keys are the results of applying the key function to each item,
and values are lists of items that produced that key.
"""

from jsl.runner import JSLRunner
import json


def main():
    runner = JSLRunner()
    
    # Sample data: sales records
    sales_data = [
        {"id": 1, "product": "Widget", "category": "tools", "price": 29.99, 
         "quantity": 5, "date": "2024-01-15", "region": "North"},
        {"id": 2, "product": "Gadget", "category": "electronics", "price": 99.99,
         "quantity": 2, "date": "2024-01-15", "region": "South"},
        {"id": 3, "product": "Doohickey", "category": "tools", "price": 19.99,
         "quantity": 10, "date": "2024-01-16", "region": "North"},
        {"id": 4, "product": "Thingamajig", "category": "electronics", "price": 149.99,
         "quantity": 1, "date": "2024-01-16", "region": "East"},
        {"id": 5, "product": "Whatsit", "category": "tools", "price": 39.99,
         "quantity": 3, "date": "2024-01-17", "region": "North"},
        {"id": 6, "product": "Gizmo", "category": "electronics", "price": 79.99,
         "quantity": 4, "date": "2024-01-17", "region": "West"},
    ]
    
    # Load the data
    runner.execute(["def", "sales", ["@", sales_data]])
    
    print("Sales Data Analysis Using group-by")
    print("=" * 50)
    
    # 1. Group by category
    print("\n1. Sales grouped by category:")
    result = runner.execute([
        "group-by",
        ["lambda", ["x"], ["get", "x", "@category"]],
        "sales"
    ])
    
    for category, items in result.items():
        total_items = len(items)
        total_quantity = sum(item["quantity"] for item in items)
        total_revenue = sum(item["price"] * item["quantity"] for item in items)
        print(f"  {category}:")
        print(f"    - {total_items} different products")
        print(f"    - {total_quantity} units sold")
        print(f"    - ${total_revenue:.2f} total revenue")
    
    # 2. Group by region
    print("\n2. Sales grouped by region:")
    result = runner.execute([
        "group-by",
        ["lambda", ["x"], ["get", "x", "@region"]],
        "sales"
    ])
    
    for region, items in result.items():
        products = [item["product"] for item in items]
        total = sum(item["price"] * item["quantity"] for item in items)
        print(f"  {region}: {products} (${total:.2f})")
    
    # 3. Group by date
    print("\n3. Sales grouped by date:")
    result = runner.execute([
        "group-by",
        ["lambda", ["x"], ["get", "x", "@date"]],
        "sales"
    ])
    
    for date, items in result.items():
        count = len(items)
        revenue = sum(item["price"] * item["quantity"] for item in items)
        print(f"  {date}: {count} sales, ${revenue:.2f} revenue")
    
    # 4. Group by price range (computed key)
    print("\n4. Sales grouped by price range:")
    runner.execute(["def", "price-tier", ["lambda", ["x"],
        ["if", ["<", ["get", "x", "@price"], 30], "@budget",
            ["if", ["<", ["get", "x", "@price"], 80], "@mid-range", "@premium"]]]])
    
    result = runner.execute(["group-by", "price-tier", "sales"])
    
    for tier, items in result.items():
        products = [f"{item['product']} (${item['price']})" for item in items]
        print(f"  {tier}: {', '.join(products)}")
    
    # 5. Complex grouping: category + high/low volume
    print("\n5. Sales grouped by category and volume:")
    runner.execute(["def", "category-volume", ["lambda", ["x"],
        ["str-concat",
            ["get", "x", "@category"],
            "@-",
            ["if", [">", ["get", "x", "@quantity"], 3], "@high-volume", "@low-volume"]]]])
    
    result = runner.execute(["group-by", "category-volume", "sales"])
    
    for key, items in sorted(result.items()):
        products = [f"{item['product']} ({item['quantity']} units)" for item in items]
        print(f"  {key}: {', '.join(products)}")
    
    # 6. Combining with where and transform
    print("\n6. High-value sales by region (where + group-by):")
    
    # First filter for high-value sales (price * quantity > 100)
    runner.execute(["def", "total-value", ["lambda", ["x"],
        ["*", ["get", "x", "@price"], ["get", "x", "@quantity"]]]])
    
    runner.execute(["def", "high-value-sales", [
        "where", "sales",
        [">", ["*", "price", "quantity"], 100]
    ]])
    
    # Then group by region
    result = runner.execute([
        "group-by",
        ["lambda", ["x"], ["get", "x", "@region"]],
        "high-value-sales"
    ])
    
    for region, items in result.items():
        sales_details = []
        for item in items:
            value = item["price"] * item["quantity"]
            sales_details.append(f"{item['product']} (${value:.2f})")
        print(f"  {region}: {', '.join(sales_details)}")
    
    # 7. Statistical analysis per group
    print("\n7. Average price per category:")
    category_groups = runner.execute([
        "group-by",
        ["lambda", ["x"], ["get", "x", "@category"]],
        "sales"
    ])
    
    for category, items in category_groups.items():
        runner.execute(["def", "cat-items", ["@", items]])
        prices = runner.execute(["pluck", "cat-items", "@price"])
        avg_price = runner.execute(["/", 
            ["reduce", "+", ["@", prices], 0],
            ["length", ["@", prices]]
        ])
        print(f"  {category}: ${avg_price:.2f} average price")


if __name__ == "__main__":
    main()