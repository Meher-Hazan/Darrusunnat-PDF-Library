import os
import json
import asyncio
import re
import random
from telethon import TelegramClient
from telethon.sessions import StringSession
from PIL import Image, ImageDraw

# --- SECRETS ---
if 'API_ID' not in os.environ or 'SESSION_STRING' not in os.environ:
    print("Error: Secrets missing.")
    exit(1)

API_ID = int(os.environ['API_ID'])
API_HASH = os.environ['API_HASH']
SESSION_STRING = os.environ['SESSION_STRING']
CHANNEL_ID = int(os.environ['CHANNEL_ID'])

DATA_FILE = 'books_data.json'
IMAGES_DIR = 'images'

if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

CATEGORIES = {
    'hadith': ['hadith', 'bukhari', 'muslim', 'হাদিস', 'বুখারী', 'মুসলিম', 'তিরমিযী'],
    'aqeedah': ['aqeedah', 'tawheed', 'iman', 'আকিদা', 'ঈমান', 'তাওহীদ'],
    'fiqh': ['fiqh', 'salah', 'namaz', 'zakat', 'ফিকহ', 'নামাজ', 'মাসায়েল', 'ফতোয়া'],
    'history': ['history', 'seerah', 'biography', 'ইতিহাস', 'সিরাত', 'জীবনী', 'খেলাফত'],
    'quran': ['quran', 'tafsir', 'কুরআন', 'তাফসির', 'সুরা'],
    'novel': ['novel', 'story', 'উপন্যাস', 'গল্প', 'সমগ্র', 'natok']
}

COVER_COLORS = [(15, 76, 58), (22, 160, 133), (44, 62, 80), (142, 68, 173), (127, 140, 141)]

def clean_title(text):
    """Smart Cleaner: Removes 01., 02-, _final, .pdf"""
    # 1. Remove extension
    text = os.path.splitext(text)[0]
    # 2. Remove starting numbers/symbols (e.g. "01. ", "02-", "#")
    text = re.sub(r'^[\d\.\-\_\#\s]+', '', text)
    # 3. Remove typical junk at end
    text = re.sub(r'(_final|_v\d|\(1\))$', '', text, flags=re.IGNORECASE)
    return text.strip()

def generate_cover(book_id):
    """Paint a generic cover if missing"""
    try:
        width, height = 400, 600
        color = random.choice(COVER_COLORS)
        img = Image.new('RGB', (width, height), color=color)
        d = ImageDraw.Draw(img)
        # Gold Border
        d.rectangle([20, 20, width-20, height-20], outline="#FFD700", width=5)
        # Save
        filename = f"{book_id}_gen.jpg"
        path = os.path.join(IMAGES_DIR, filename)
        img.save(path)
        return f"images/{filename}"
    except:
        return ""

async def main():
    print("--- Connecting to Telegram ---")
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.start()

    books = []
    processed_ids = set()
    
    # Load existing to prevent re-processing
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                books = json.load(f)
                processed_ids = {b['id'] for b in books}
        except: pass
    
    print("Scanning last 100 messages...")
    messages = await client.get_messages(CHANNEL_ID, limit=100)
    
    new_count = 0
    pending_cover = "" 
    
    # Process Oldest -> Newest to keep order
    for message in reversed(messages):
        
        # 1. Grab Cover
        if message.photo:
            filename = f"{message.id}.jpg"
            file_path = os.path.join(IMAGES_DIR, filename)
            if not os.path.exists(file_path):
                await message.download_media(file=file_path)
            pending_cover = f"images/{filename}"
            continue

        # 2. Grab Book
        if message.document and message.document.mime_type == 'application/pdf':
            current_cover = pending_cover
            pending_cover = "" # Reset immediately logic

            # Extract raw name from file attribute or text
            raw_name = ""
            if message.file and message.file.name:
                raw_name = message.file.name
            elif message.text:
                raw_name = message.text.split('\n')[0]
            else:
                raw_name = f"Book {message.id}"

            # --- SMART AUTHOR EXTRACTION ---
            # Looks for "Author - Title" format
            title = clean_title(raw_name)
            author = ""
            
            if " - " in raw_name:
                parts = raw_name.split(" - ")
                if len(parts) >= 2:
                    author = parts[0].strip() # Author is usually first
                    title = clean_title(parts[1])
            
            # Determine Category
            category = "General"
            check_text = (title + " " + (message.text or "")).lower()
            for cat, keywords in CATEGORIES.items():
                if any(k in check_text for k in keywords):
                    category = cat.capitalize()
                    break

            # If no cover, generate one
            if not current_cover:
                current_cover = generate_cover(message.id)

            # Skip duplicates
            if message.id in processed_ids:
                continue

            # Build Link
            clean_id = str(CHANNEL_ID).replace("-100", "")
            post_link = f"https://t.me/c/{clean_id}/{message.id}"

            books.append({
                "id": message.id,
                "title": title,
                "author": author,
                "category": category,
                "link": post_link,
                "image": current_cover
            })
            processed_ids.add(message.id)
            new_count += 1
            print(f" + Added: {title}")

    # 3. Save
    if new_count > 0:
        books.sort(key=lambda x: x['id'], reverse=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(books, f, indent=4, ensure_ascii=False)
        print(f"--- SUCCESS: Added {new_count} books ---")
    else:
        print("--- No new books ---")

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
