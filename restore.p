import os
import json
from telethon import TelegramClient

# --- CONFIGURATION ---
# REPLACE THESE WITH YOUR NUMBERS (Get from my.telegram.org)
API_ID = 2040  
API_HASH = 'b18441a1ff607e10a989891a5462e627'
CHANNEL_ID = -100123456789 # REPLACE WITH YOUR CHANNEL ID

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

# We use a NEW session name 'final_user_login' to force a fresh login
client = TelegramClient('final_user_login', API_ID, API_HASH)

async def main():
    print("--- MANDATORY USER LOGIN ---")
    print("This will ask for your Phone Number. This is required to download history.")
    
    # This command forces the phone prompt
    await client.start()

    print("Login Successful! Fetching messages...")
    
    # Get all messages
    messages = await client.get_messages(CHANNEL_ID, limit=None)
    
    books = []
    active_cover = ""

    print(f"Found {len(messages)} messages. Processing...")

    # Process Oldest -> Newest
    for message in reversed(messages):
        
        # 1. PHOTO
        if message.photo:
            filename = f"{message.id}.jpg"
            file_path = os.path.join(IMAGES_DIR, filename)
            await message.download_media(file=file_path)
            active_cover = f"images/{filename}"
            print(f"Downloaded Cover: {filename}")
            continue

        # 2. PDF
        if message.document and message.document.mime_type == 'application/pdf':
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
            print(f"Added Book: {title}")

    # Save
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(books, f, indent=4, ensure_ascii=False)
    
    print(f"--- COMPLETE: Saved {len(books)} books to database. ---")

if __name__ == '__main__':
    client.loop.run_until_complete(main())
