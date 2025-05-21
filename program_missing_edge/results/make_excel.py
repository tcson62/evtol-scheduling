import pandas as pd

# Sample data
data = {
    'Name': ['Alice', 'Bob', 'Charlie'],
    'Score': [85, 90, 95]
}

df = pd.DataFrame(data)

# Save to Excel
df.to_excel('output.xlsx', index=False)