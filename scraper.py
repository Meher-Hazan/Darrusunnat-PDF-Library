import os
import json
import asyncio
import random
from telethon import TelegramClient
from telethon.sessions import StringSession
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURATION ---
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
    'novel': ['novel', 'story', 'উপন্যাস', 'গল্প', 'সমগ্র']
}

# Colors for generated covers
COVER_COLORS = [
    (15, 76, 58), (22, 160, 133), (44, 62, 80), 
    (142, 68, 173), (192, 57, 43), (211, 84, 0), (127, 140, 141)
]

def generate_cover(book_id, title, author):
    """Generates a placeholder cover if none exists"""
    try:
        width, height = 400, 600
        color = random.choice(COVER_COLORS)
        img = Image.new('RGB', (width, height), color=color)
        d = ImageDraw.Draw(img)
        
        # Border
        d.rectangle([15, 15, width-15, height-15], outline="white", width=3)
        
        # Text (Basic positioning)
        # Note: PIL default font is tiny. For real production, we'd need a .ttf file.
        # This is a fallback to ensure we have *something*.
        d.text((width/2, height/3), "ISLAMIC LIBRARY", fill="gold", anchor="mm")
        
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

    # 1. Load Data
    books = []
    processed_ids = set()
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                books = json.load(f)
                processed_ids = {b['id'] for b in books}
        except: pass
    
    # 2. Scan History
    print("Scanning last 100 messages...")
    messages = await client.get_messages(CHANNEL_ID, limit=100)
    
    new_count = 0
    pending_cover = "" 
    
    for message in reversed(messages):
        
        # PHOTO
        if message.photo:
            filename = f"{message.id}.jpg"
            file_path = os.path.join(IMAGES_DIR, filename)
            if not os.path.exists(file_path):
                await message.download_media(file=file_path)
            pending_cover = f"images/{filename}"
            continue

        # PDF
        if message.document and message.document.mime_type == 'application/pdf':
            
            current_cover = pending_cover
            pending_cover = "" # Reset

            # --- AUTHOR & TITLE EXTRACTION ---
            # Priority: File Name. Fallback: Caption.
            raw_filename = message.file.name or ""
            clean_filename = os.path.splitext(raw_filename)[0] # Remove .pdf
            
            title = clean_filename
            author = ""

            # Attempt to split "Author - Title" or "Title - Author"
            # We assume the pattern: "Author Name - Book Title"
            if " - " in clean_filename:
                parts = clean_filename.split(" - ")
                if len(parts) >= 2:
                    author = parts[0].strip()
                    title = parts[1].strip()
            elif " | " in clean_filename:
                parts = clean_filename.split(" | ")
                if len(parts) >= 2:
                    author = parts[0].strip()
                    title = parts[1].strip()
            
            # Fallback title if extraction failed or file name is weird
            if not title and message.text:
                title = message.text.split('\n')[0]

            # Categorization
            category = "General"
            check_text = (title + " " + (message.text or "")).lower()
            for cat, keywords in CATEGORIES.items():
                if any(k in check_text for k in keywords):
                    category = cat.capitalize()
                    break

            # Image Generation Check
            if not current_cover:
                current_cover = generate_cover(message.id, title, author)

            # Check Duplicate
            if message.id in processed_ids:
                # Update logic if we want to refresh metadata
                # For now, we skip to save time, or update if cover was missing
                continue

            clean_id = str(CHANNEL_ID).replace("-100", "")
            post_link = f"https://t.me/c/{clean_id}/{message.id}"

            new_book = {
                "id": message.id,
                "title": title,
                "author": author, # NEW FIELD
                "category": category,
                "link": post_link,
                "image": current_cover
            }
            
            books.append(new_book)
            processed_ids.add(message.id)
            new_count += 1
            print(f" + Added: {title} (Author: {author})")

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
