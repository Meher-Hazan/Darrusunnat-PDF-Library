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
    'dua': ['dua', 'zikr', 'দোআ', 'জিকির', 'আমল']
}

# Distinct colors for generated covers (Islamic Palette)
COVER_COLORS = [
    (15, 76, 58),   # Emerald
    (22, 160, 133), # Teal
    (44, 62, 80),   # Midnight Blue
    (142, 68, 173), # Royal Purple
    (192, 57, 43),  # Deep Red
    (211, 84, 0),   # Pumpkin
    (127, 140, 141) # Grey
]

def generate_cover(book_id, title, category):
    """Creates a unique cover image for books without photos"""
    try:
        # 1. Setup Canvas (Portrait Aspect Ratio)
        width, height = 400, 600
        color = random.choice(COVER_COLORS)
        img = Image.new('RGB', (width, height), color=color)
        d = ImageDraw.Draw(img)

        # 2. Draw Border
        border_w = 15
        d.rectangle([border_w, border_w, width-border_w, height-border_w], outline="white", width=3)

        # 3. Add Pattern (Simple circles)
        for i in range(0, width, 40):
            d.ellipse([i, 0, i+20, 20], fill=(255,255,255, 30))
            d.ellipse([i, height-20, i+20, height], fill=(255,255,255, 30))

        # 4. Add Text (We use default font as custom fonts are tricky on servers)
        # We wrap text manually since default font is small/basic
        # Ideally, we would load a .ttf file, but default is safer for now.
        
        # Center Title roughly
        # Note: Default PIL font is small. This is a fallback "Artistic" representation.
        # Ideally we place the Category in center
        
        d.text((width/2, height/3), category.upper(), fill="white", anchor="mm")
        d.text((width/2, height/2), "DARRUSUNNAT", fill="gold", anchor="mm")
        
        # Save
        filename = f"{book_id}_gen.jpg"
        path = os.path.join(IMAGES_DIR, filename)
        img.save(path)
        return f"images/{filename}"
    except Exception as e:
        print(f"Could not generate cover: {e}")
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
    pending_cover_path = "" 
    
    for message in reversed(messages):
        
        # SCENARIO A: PHOTO
        if message.photo:
            filename = f"{message.id}.jpg"
            file_path = os.path.join(IMAGES_DIR, filename)
            if not os.path.exists(file_path):
                print(f"Downloading cover: {filename}")
                await message.download_media(file=file_path)
            pending_cover_path = f"images/{filename}"
            continue

        # SCENARIO B: PDF
        if message.document and message.document.mime_type == 'application/pdf':
            
            current_cover = pending_cover_path
            pending_cover_path = "" # Reset immediately

            # Extract Info
            caption = message.text or ""
            file_name = message.file.name or ""
            title = caption.split('\n')[0] if caption else (file_name or f"Book #{message.id}")
            
            # Determine Category
            category = "General"
            check_text = (caption + " " + file_name).lower()
            for cat, keywords in CATEGORIES.items():
                if any(k in check_text for k in keywords):
                    category = cat.capitalize()
                    break

            # If no cover found from Telegram, GENERATE ONE!
            if not current_cover:
                print(f"Generating Art Cover for: {title}")
                current_cover = generate_cover(message.id, title, category)

            # Check Duplicates
            if message.id in processed_ids:
                # Update existing if it doesn't have an image
                existing = next((b for b in books if b['id'] == message.id), None)
                if existing and not existing.get('image'):
                    existing['image'] = current_cover
                    new_count += 1
                continue

            clean_id = str(CHANNEL_ID).replace("-100", "")
            post_link = f"https://t.me/c/{clean_id}/{message.id}"

            new_book = {
                "id": message.id,
                "title": title,
                "author": "Darrusunnat Library",
                "category": category,
                "link": post_link,
                "image": current_cover
            }
            
            books.append(new_book)
            processed_ids.add(message.id)
            new_count += 1
            print(f" + Added: {title}")

    # 3. Save
    if new_count > 0:
        books.sort(key=lambda x: x['id'], reverse=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(books, f, indent=4, ensure_ascii=False)
        print(f"--- SUCCESS: Updated {new_count} items ---")
    else:
        print("--- No new items found ---")

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
