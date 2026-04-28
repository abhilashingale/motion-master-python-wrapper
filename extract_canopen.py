import re
import html
from pathlib import Path

# Read the HTML file
with open('safe_objects.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract all tables
table_pattern = r'<table class="table[^"]*"[^>]*>.*?</table>'
tables = re.findall(table_pattern, content, re.DOTALL)

all_rows = []

for table_idx, table_content in enumerate(tables):
    # Extract all row data
    row_pattern = r'<tr[^>]*>(.*?)</tr>'
    rows = re.findall(row_pattern, table_content, re.DOTALL)
    
    for row in rows:
        # Extract cells
        cell_pattern = r'<td[^>]*>(.*?)</td>|<th[^>]*>(.*?)</th>'
        cells = re.findall(cell_pattern, row, re.DOTALL)
        
        if cells:
            cleaned_cells = []
            for td_content, th_content in cells:
                cell_text = td_content if td_content else th_content
                # Remove HTML tags
                text = re.sub(r'<[^>]+>', '', cell_text)
                # Decode HTML entities
                text = html.unescape(text)
                # Clean whitespace
                text = ' '.join(text.split())
                if text:
                    cleaned_cells.append(text)
            
            if cleaned_cells and len(cleaned_cells) >= 1:
                all_rows.append(cleaned_cells)

# Print all rows
for i, row in enumerate(all_rows):
    print(f"Row {i}: {row}")

print(f"\nTotal rows: {len(all_rows)}")
