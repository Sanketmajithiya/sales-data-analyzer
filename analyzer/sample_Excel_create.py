import os
import pandas as pd
from datetime import datetime, timedelta
import random

# Sample data
products = ['Car', 'Bike', 'Truck']
names = ['Shyam', 'Anita', 'Rahul', 'Preeti', 'John', 'Sara']
data = []

for _ in range(50):
    product = random.choice(products)
    name = random.choice(names)
    sales = round(random.uniform(100, 1000), 2)
    date = datetime.now() - timedelta(days=random.randint(0, 365))
    data.append({
        'Name': name,
        'Product Name': product,
        'Sales': sales,
        'Date': date.date()
    })

df = pd.DataFrame(data)

# Base filename
base_filename = "sample_sales_data.xlsx"
filename = base_filename
count = 1

# Agar file exist karti ho toh naya naam banao
while os.path.exists(filename):
    filename = f"sample_sales_data_{count}.xlsx"
    count += 1

# File save karo
with pd.ExcelWriter(filename, engine='xlsxwriter', datetime_format='yyyy-mm-dd') as writer:
    df.to_excel(writer, index=False)

print(f"File saved as: {filename}")

# CSV ke liye bhi same approach
base_csv = "sample_sales_data.csv"
csv_filename = base_csv
csv_count = 1

while os.path.exists(csv_filename):
    csv_filename = f"sample_sales_data_{csv_count}.csv"
    csv_count += 1

df.to_csv(csv_filename, index=False)
print(f"CSV file saved as: {csv_filename}")
