import pandas as pd
import os

# 1. Read the CSV File
print("Reading database.csv...")
try:
    # Attempt to read with standard UTF-8
    df = pd.read_csv('database.csv', header=None, names=['Title', 'Link', 'ImgPath'])
except Exception as e:
    print(f"Error reading CSV: {e}")
    # Fallback: create dummy data if CSV fails
    df = pd.DataFrame([['Example Book', 'https://t.me/', 'https://via.placeholder.com/150']], columns=['Title', 'Link', 'ImgPath'])

print(f"Found {len(df)} books in database.")

# 2. HTML Template (Design)
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Darrusunnat PDF Library</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #f4f4f9; padding: 20px; text-align: center; }}
        .header {{ margin-bottom: 30px; }}
        .search-box {{ padding: 12px; width: 80%; max-width: 400px; font-size: 16px; border: 1px solid #ccc; border-radius: 25px; outline: none; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 20px; padding: 10px; }}
        .card {{ background: white; padding: 10px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: transform 0.2s; }}
        .card:hover {{ transform: translateY(-5px); }}
        .card img {{ width: 100%; height: 220px; object-fit: cover; border-radius: 5px; }}
        .title {{ font-size: 14px; margin: 10px 0; font-weight: bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .btn {{ display: block; background: #0088cc; color: white; padding: 8px; text-decoration: none; border-radius: 5px; font-size: 14px; }}
        .hidden {{ display: none; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📚 Darrusunnat Library</h1>
        <p>Total Books: {len(df)}</p>
        <input type="text" id="search" class="search-box" placeholder="Search books..." onkeyup="filterBooks()">
    </div>

    <div class="grid" id="bookGrid">
"""

# 3. Add Books to HTML
for index, row in df.iterrows():
    # Use placeholder if image is missing
    img_src = row['ImgPath'] if pd.notna(row['ImgPath']) else "https://via.placeholder.com/150?text=No+Cover"
    # Fix local paths if they don't exist yet
    if not img_src.startswith("http"):
        # We assume images are in root/images/
        pass 
    
    html_content += f"""
        <div class="card">
            <img src="{img_src}" onerror="this.src='https://via.placeholder.com/150?text=No+Image'">
            <div class="title" title="{row['Title']}">{row['Title']}</div>
            <a href="{row['Link']}" class="btn" target="_blank">Download</a>
        </div>
    """

html_content += """
    </div>

    <script>
        function filterBooks() {
            let input = document.getElementById('search').value.toLowerCase();
            let cards = document.getElementsByClassName('card');
            for (let i = 0; i < cards.length; i++) {
                let title = cards[i].getElementsByClassName('title')[0].innerText.toLowerCase();
                cards[i].style.display = title.includes(input) ? "" : "none";
            }
        }
    </script>
</body>
</html>
"""

# 4. Save the file
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("Success! index.html created.")
