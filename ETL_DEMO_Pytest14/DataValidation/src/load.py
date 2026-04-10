import csv
import os

def load_data(data, filename="reports/loaded_data.csv"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    if not data:
        print("No data to load.")
        return

    headers = data[0].keys()

    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)

    print(f"✅ Data loaded successfully to {filename}")
