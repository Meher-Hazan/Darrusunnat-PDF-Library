import os
import json
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# --- CONFIGURATION ---
# The Robot loads these from GitHub Secrets
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
    print("--- Connecting as User (Cloud Session) ---")
    
    # Log in using the String Session (No phone/code needed!)
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
    
    print(f"Loaded {len(books)} existing books.")

    # 2. Scan Channel History
    # Since we are "User", we can scan EVERYTHING.
    # We scan from Newest -> Oldest, but only stop if we hit data we already know?
    # Actually, let's scan the last 100 messages every time to ensure we catch updates.
    
    print("Scanning last 100 messages...")
    messages = await client.get_messages(CHANNEL_ID, limit=100)
    
    new_items = []
    active_cover = ""

    # We process in REVERSE (Oldest -> Newest) to keep sequence correct
    for message in reversed(messages):
        
        # Capture Cover
        if message.photo:
            # Check if we already have this image to save bandwidth
            filename = f"{message.id}.jpg"
            file_path = os.path.join(IMAGES_DIR, filename)
            
            if not os.path.exists(file_path):
                print(f"Downloading new cover: {filename}")
                await message.download_media(file=file_path)
            
            active_cover = f"images/{filename}"
            continue

        # Capture PDF
        if message.document and message.document.mime_type == 'application/pdf':
            # If we already processed this book ID, skip logic but KEEP it in list
            # Actually, we need to rebuild the list to ensure data integrity
            
            if message.id in processed_ids:
                # We already have this book.
                # However, we must ensure 'active_cover' updates correctly for future books
                # Find the existing book entry to reuse its cover if needed
                existing = next((b for b in books if b['id'] == message.id), None)
                if existing and existing['image']:
                     active_cover = existing['image']
                continue

            # It is a NEW book
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
            new_items.append(title)
            print(f" + Found New Book: {title}")

    # 3. Save Updates
    if new_items:
        # Sort books by ID to keep them tidy
        books.sort(key=lambda x: x['id'], reverse=True)
        
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(books, f, indent=4, ensure_ascii=False)
        print(f"--- SUCCESS: Added {len(new_items)} new books ---")
    else:
        print("--- No new books found in last 100 messages ---")

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
