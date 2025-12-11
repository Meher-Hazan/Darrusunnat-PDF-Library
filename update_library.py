import os
import pandas as pd
import json
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

# --- CONFIG ---
try:
    API_ID = int(os.environ.get("TG_API_ID"))
except:
    print("API_ID missing, using dummy for testing")
    API_ID = 0

API_HASH = os.environ.get("TG_API_HASH")
SESSION = os.environ.get("TG_SESSION")
CHANNEL = "SobBoiErPdf"
CSV_FILE = "database.csv"
IMG_FOLDER = "images"

# --- PREMIUM HTML TEMPLATE ---
# This uses JSON injection for high performance (No lag with 10k books)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Darrusunnat Library | Premium Collection</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #2563eb;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text: #1e293b;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-hover: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 0;
            overflow-y: scroll;
        }

        /* HERO HEADER */
        .hero {
            background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
            color: white;
            padding: 60px 20px 80px;
            text-align: center;
            border-bottom-left-radius: 30px;
            border-bottom-right-radius: 30px;
            box-shadow: 0 10px 30px rgba(37, 99, 235, 0.2);
            position: relative;
            z-index: 10;
        }

        .hero h1 { margin: 0; font-size: 2.5rem; font-weight: 800; letter-spacing: -1px; }
        .hero p { opacity: 0.9; margin-top: 10px; font-size: 1.1rem; }

        /* SEARCH BAR (Floating) */
        .search-container {
            margin-top: -30px;
            display: flex;
            justify-content: center;
            padding: 0 20px;
        }
        
        .search-box {
            background: white;
            width: 100%;
            max-width: 600px;
            padding: 18px 25px;
            border-radius: 50px;
            border: none;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            font-size: 18px;
            font-family: inherit;
            transition: all 0.3s ease;
            outline: none;
        }
        
        .search-box:focus { transform: scale(1.02); box-shadow: 0 15px 30px rgba(37, 99, 235, 0.2); }

        /* GRID LAYOUT */
        .container { max-width: 1200px; margin: 40px auto; padding: 0 20px; }
        .stats { text-align: center; color: #64748b; margin-bottom: 20px; font-size: 0.9rem; }

        .book-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
            gap: 25px;
        }

        /* CARD DESIGN */
        .book-card {
            background: var(--card-bg);
            border-radius: 16px;
            overflow: hidden;
            box-shadow: var(--shadow);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            display: flex;
            flex-direction: column;
            animation: fadeIn 0.5s ease-out forwards;
            opacity: 0; /* Hidden initially for animation */
        }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

        .book-card:hover {
            transform: translateY(-8px);
            box-shadow: var(--shadow-hover);
        }

        .img-wrapper {
            position: relative;
            padding-top: 140%; /* 5:7 Aspect Ratio */
            background: #e2e8f0;
            overflow: hidden;
        }

        .img-wrapper img {
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            object-fit: cover;
            transition: transform 0.5s ease;
        }

        .book-card:hover .img-wrapper img { transform: scale(1.05); }

        .card-content { padding: 15px; flex-grow: 1; display: flex; flex-direction: column; justify-content: space-between; }
        
        .book-title {
            font-size: 0.95rem;
            font-weight: 600;
            color: var(--text);
            margin: 0 0 10px 0;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            line-height: 1.4;
        }

        .download-btn {
            display: block;
            width: 100%;
            padding: 10px 0;
            text-align: center;
            background: #eff6ff;
            color: var(--primary);
            font-weight: 600;
            font-size: 0.85rem;
            border-radius: 8px;
            text-decoration: none;
            transition: background 0.2s;
        }

        .download-btn:hover { background: var(--primary); color: white; }
        
        /* LOADING SPINNER */
        .loader { text-align: center; padding: 40px; display: none; }
        .spinner { border: 4px solid #f3f3f3; border-top: 4px solid var(--primary); border-radius: 50%; width: 30px; height: 30px; animation: spin 1s linear infinite; display: inline-block; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

    </style>
</head>
<body>

    <div class="hero">
        <h1>Darrusunnat Library</h1>
        <p>Premium PDF Collection • Updated Daily</p>
    </div>

    <div class="search-container">
        <input type="text" id="searchInput" class="search-box" placeholder="Search 10,000+ books..." autocomplete="off">
    </div>

    <div class="container">
        <div class="stats" id="statsText">Loading Library...</div>
        <div class="book-grid" id="grid"></div>
        <div class="loader" id="loader"><div class="spinner"></div></div>
    </div>

    <script>
        // DATA INJECTION (Python puts the JSON here)
        const DB = __BOOKS_JSON__; 
        
        const grid = document.getElementById('grid');
        const loader = document.getElementById('loader');
        const searchInput = document.getElementById('searchInput');
        const statsText = document.getElementById('statsText');
        
        let visibleCount = 0;
        const BATCH_SIZE = 40; // Render 40 at a time for speed
        let filteredDB = DB; // Initially, filtered list is the full list

        // 1. Initialize
        function init() {
            statsText.innerText = `${DB.length.toLocaleString()} books available`;
            renderNextBatch();
        }

        // 2. Render Card Function
        function createCard(book) {
            const div = document.createElement('div');
            div.className = 'book-card';
            // Use placeholder if img is missing/broken, but rely on lazy loading
            const imgUrl = book.img && book.img.length > 5 ? book.img : 'https://via.placeholder.com/200x300?text=PDF';
            
            div.innerHTML = `
                <div class="img-wrapper">
                    <img src="${imgUrl}" loading="lazy" alt="Cover">
                </div>
                <div class="card-content">
                    <div class="book-title">${book.title}</div>
                    <a href="${book.link}" target="_blank" class="download-btn">Download</a>
                </div>
            `;
            return div;
        }

        // 3. Render Batch (Infinite Scroll Logic)
        function renderNextBatch() {
            const fragment = document.createDocumentFragment();
            const end = Math.min(visibleCount + BATCH_SIZE, filteredDB.length);
            
            for (let i = visibleCount; i < end; i++) {
                fragment.appendChild(createCard(filteredDB[i]));
            }
            
            grid.appendChild(fragment);
            visibleCount = end;
            
            // Hide loader if we showed everything
            if (visibleCount >= filteredDB.length) {
                loader.style.display = 'none';
            }
        }

        // 4. Search Function (Debounced)
        let timeout = null;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                const q = e.target.value.toLowerCase();
                
                // Filter the array
                filteredDB = DB.filter(b => b.title.toLowerCase().includes(q));
                
                // Reset Grid
                grid.innerHTML = '';
                visibleCount = 0;
                statsText.innerText = `Found ${filteredDB.length} books`;
                
                // Render first batch of results
                renderNextBatch();
            }, 300);
        });

        // 5. Infinite Scroll Event
        window.addEventListener('scroll', () => {
            if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 500) {
                if (visibleCount < filteredDB.length) {
                    renderNextBatch();
                }
            }
        });

        // Start
        init();
    </script>
</body>
</html>
"""

def main():
    print("Starting Premium Update...")
    os.makedirs(IMG_FOLDER, exist_ok=True)

    # 1. Load Database
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE, header=None, names=["Title", "Link", "ImgPath"])
    else:
        df = pd.DataFrame(columns=["Title", "Link", "ImgPath"])
    
    # 2. Check for updates (Fast Mode)
    last_id = 0
    if not df.empty:
        df['MsgID'] = df['Link'].apply(lambda x: int(x.split('/')[-1]) if isinstance(x, str) and 't.me' in x else 0)
        last_id = df['MsgID'].max()
    
    print(f"Checking updates since ID: {last_id}")

    try:
        with TelegramClient(StringSession(SESSION), API_ID, API_HASH) as client:
            new_books = []
            messages = client.get_messages(CHANNEL, limit=100, min_id=last_id)
            
            for msg in messages:
                if msg.file and msg.file.name and msg.file.name.lower().endswith('.pdf'):
                    title = msg.file.name.replace('.pdf', '')
                    link = f"https://t.me/{CHANNEL}/{msg.id}"
                    img_path = f"{IMG_FOLDER}/{msg.id}.jpg"
                    
                    # Download Cover
                    prev_msg = client.get_messages(CHANNEL, ids=msg.id - 1)
                    if prev_msg and prev_msg.photo:
                        client.download_media(prev_msg.photo, file=img_path)
                    
                    new_books.append({"Title": title, "Link": link, "ImgPath": img_path})

            if new_books:
                print(f"Adding {len(new_books)} new books...")
                new_df = pd.DataFrame(new_books)
                df = pd.concat([new_df, df.drop(columns=['MsgID'], errors='ignore')], ignore_index=True)
                df.to_csv(CSV_FILE, index=False, header=False)
    except Exception as e:
        print(f"Skipping Telegram update (Error or Key missing): {e}")

    # 3. Generate JSON Data
    # Convert DataFrame to list of dicts for JS
    books_list = []
    for _, row in df.iterrows():
        # Clean data
        img = row['ImgPath'] if pd.notna(row['ImgPath']) else ""
        title = str(row['Title']).replace('"', '')
        books_list.append({"title": title, "link": row['Link'], "img": img})
    
    # Inject JSON into HTML
    json_data = json.dumps(books_list)
    final_html = HTML_TEMPLATE.replace('__BOOKS_JSON__', json_data)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)
            
    print("Premium Website Generated!")

if __name__ == "__main__":
    main()
