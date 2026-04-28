import re
import html

# Read the HTML file
with open('safe_objects.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract all tables
table_pattern = r'<table class="table[^"]*"[^>]*>.*?</table>'
tables = re.findall(table_pattern, content, re.DOTALL)

canopen_objects = []

for table_content in tables:
    # Extract all row data
    row_pattern = r'<tr[^>]*>(.*?)</tr>'
    rows = re.findall(row_pattern, table_content, re.DOTALL)
    
    for row in rows:
        # Extract cells
        cell_pattern = r'<td[^>]*>(.*?)</td>|<th[^>]*>(.*?)</th>'
        cells = re.findall(cell_pattern, row, re.DOTALL)
        
        if cells and len(cells) >= 2:
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
            
            if len(cleaned_cells) >= 2:
                index_info = cleaned_cells[0]
                name = cleaned_cells[1]
                
                # Skip header rows
                if index_info.lower() == 'index' or name.lower() == 'name':
                    continue
                
                # Skip "empty" rows without index
                if not index_info or index_info == '':
                    continue
                
                # Parse index and subindex
                if ':' in index_info:
                    parts = index_info.split(':')
                    index = parts[0]
                    subindex = parts[1]
                else:
                    index = index_info
                    subindex = ''
                
                canopen_objects.append({
                    'index': index,
                    'subindex': subindex,
                    'name': name
                })

# Output as CSV
print("Index (Hex),SubIndex (Hex),Object Name/Description,Data Type")
for obj in canopen_objects:
    print(f'"{obj["index"]}","{obj["subindex"]}","{obj["name"]}","N/A"')

print(f"\n# Total entries: {len(canopen_objects)}")
