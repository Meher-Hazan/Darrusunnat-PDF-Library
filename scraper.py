import os
import json
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# --- CONFIGURATION ---
API_ID = int(os.environ['API_ID'])
API_HASH = os.environ['API_HASH']
SESSION_STRING = os.environ['SESSION_STRING']
CHANNEL_ID = int(os.environ['CHANNEL_ID'])

DATA_FILE = 'books_data.json'
IMAGES_DIR = 'images'

if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

CATEGORIES = {
    'hadith': ['hadith', 'bukhari', 'muslim', 'হাদিস', 'বুখারী', 'মুসলিম'],
    'aqeedah': ['aqeedah', 'tawheed', 'iman', 'আকিদা', 'ঈমান', 'তাওহীদ'],
    'fiqh': ['fiqh', 'salah', 'namaz', 'zakat', 'ফিকহ', 'নামাজ', 'মাসায়েল'],
    'history': ['history', 'seerah', 'biography', 'ইতিহাস', 'সিরাত', 'জীবনী'],
    'quran': ['quran', 'tafsir', 'কুরআন', 'তাফসির']
}

async def main():
    print("--- Connecting to Telegram (User Mode) ---")
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.start()

    # 1. Load Existing Data
    books = []
    processed_ids = set()
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                books = json.load(f)
                processed_ids = {b['id'] for b in books}
        except: pass
    
    # 2. Scan Channel (Last 200 messages)
    print("Scanning last 200 messages for new books...")
    messages = await client.get_messages(CHANNEL_ID, limit=200)
    
    new_items = 0
    active_cover = ""

    # Process Oldest -> Newest
    for message in reversed(messages):
        
        # Capture Cover
        if message.photo:
            filename = f"{message.id}.jpg"
            file_path = os.path.join(IMAGES_DIR, filename)
            # Only download if missing
            if not os.path.exists(file_path):
                print(f"Downloading cover: {filename}")
                await message.download_media(file=file_path)
            active_cover = f"images/{filename}"
            continue

        # Capture PDF
        if message.document and message.document.mime_type == 'application/pdf':
            # Skip if we already have this exact message ID
            if message.id in processed_ids:
                # Still update active_cover logic based on what we have in DB
                existing = next((b for b in books if b['id'] == message.id), None)
                if existing and existing['image']: active_cover = existing['image']
                continue

            # New Book Found
            caption = message.text or ""
            file_name = message.file.name or ""
            title = caption.split('\n')[0] if caption else (file_name or f"Book #{message.id}")
            
            category = "General"
            check_text = (caption + " " + file_name).lower()
            for cat, keywords in CATEGORIES.items():
                if any(k in check_text for k in keywords):
                    category = cat.capitalize()
                    break

            clean_id = str(CHANNEL_ID).replace("-100", "")
            post_link = f"https://t.me/c/{clean_id}/{message.id}"

            new_book = {
                "id": message.id,
                "title": title,
                "author": "Darrusunnat Library",
                "category": category,
                "link": post_link,
                "image": active_cover
            }
            
            books.append(new_book)
            new_items += 1
            print(f" + Added: {title}")

    # 3. Save Data
    if new_items > 0:
        # Sort by ID descending (Latest first)
        books.sort(key=lambda x: x['id'], reverse=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(books, f, indent=4, ensure_ascii=False)
        print(f"--- SUCCESS: Added {new_items} new books ---")
    else:
        print("--- No new books found. Database up to date. ---")

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
