import os
import json
import asyncio
import re
import random
from telethon import TelegramClient
from telethon.sessions import StringSession
from PIL import Image, ImageDraw

# --- CONFIGURATION ---
API_ID = int(os.environ.get('API_ID', 0))
API_HASH = os.environ.get('API_HASH', '')
SESSION_STRING = os.environ.get('SESSION_STRING', '')
CHANNEL_ID = int(os.environ.get('CHANNEL_ID', 0))

DATA_FILE = 'books_data.json'
IMAGES_DIR = 'images'

if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

# --- 🧠 LAYER 1: DIRECT KNOWLEDGE BASE ---
# The robot checks this list FIRST. If it finds these words, it knows the writer instantly.
AI_KNOWLEDGE = {
    # HADITH & TAFSIR
    'bukhari': 'ইমাম বুখারী (রহ.)',
    'muslim': 'ইমাম মুসলিম (রহ.)',
    'tirmidhi': 'ইমাম তিরমিযী (রহ.)',
    'nasai': 'ইমাম নাসাঈ (রহ.)',
    'abu daud': 'ইমাম আবু দাউদ (রহ.)',
    'ibn majah': 'ইমাম ইবনে মাজাহ (রহ.)',
    'ryadus': 'ইমাম নববী (রহ.)',
    'riyadus': 'ইমাম নববী (রহ.)',
    'mishkat': 'ওয়ালীউদ্দীন আল-খাতীব (রহ.)',
    'ibn kathir': 'হাফেজ ইবনে কাসীর (রহ.)',
    'jalalain': 'জালালুদ্দিন সুয়ুতী (রহ.)',
    'mareful': 'মুফতি শফি উসমানী (রহ.)',
    'fi zilalil': 'সাইয়েদ কুতুব (রহ.)',
    'tafhimul': 'সাইয়েদ আবুল আ\'লা মওদুদী (রহ.)',
    
    # POPULAR WRITERS
    'ariff azad': 'আরিফ আজাদ',
    'paradoxical': 'আরিফ আজাদ',
    'bela furabar': 'আরিফ আজাদ',
    'mizanur rahman': 'মিজানুর রহমান আজহারী',
    'azhari': 'মিজানুর রহমান আজহারী',
    'ahmadullah': 'শায়খ আহমাদুল্লাহ',
    'nasiruddin': 'নাসিরুদ্দিন আলবানী (রহ.)',
    'albani': 'নাসিরুদ্দিন আলবানী (রহ.)',
    'zakariya': 'শায়খ জাকারিয়া (রহ.)',
    'iqbal': 'আল্লামা ইকবাল',
    'rahe belayat': 'ড. খন্দকার আব্দুল্লাহ জাহাঙ্গীর',
    'jannat': 'ড. খন্দকার আব্দুল্লাহ জাহাঙ্গীর',
    'himu': 'হুমায়ূন আহমেদ',
    'misir ali': 'হুমায়ূন আহমেদ',
    'sharat': 'শরৎচন্দ্র চট্টোপাধ্যায়',
    'rabindra': 'রবীন্দ্রনাথ ঠাকুর'
}

# --- 🧠 LAYER 2: HONORIFICS (Smart Guessing) ---
# If the robot sees these titles in a name, it assumes it is a writer.
HONORIFICS = [
    'dr.', 'dr ', 'prof.', 'sheikh', 'shaykh', 'imam', 'mufti', 'maulana', 
    'moulana', 'allama', 'hafez', 'qari', 'ustadh', 'writer', 'author',
    'ড.', 'অধ্যাপক', 'শায়খ', 'ইমাম', 'মুফতি', 'মাওলানা', 'আল্লামা', 'হাফেজ'
]

# --- CATEGORY RULES ---
CATEGORIES = {
    'hadith': ['hadith', 'bukhari', 'muslim', 'হাদিস', 'বুখারী', 'মুসলিম', 'তিরমিযী', 'সুনান'],
    'aqeedah': ['aqeedah', 'tawheed', 'iman', 'shirk', 'আকিদা', 'ঈমান', 'তাওহীদ', 'শিরক'],
    'fiqh': ['fiqh', 'salah', 'namaz', 'zakat', 'hajj', 'ফিকহ', 'নামাজ', 'রোজা', 'ফতোয়া', 'মাসায়েল'],
    'history': ['history', 'seerah', 'biography', 'battle', 'ইতিহাস', 'সিরাত', 'জীবনী', 'যুদ্ধ', 'খেলাফত'],
    'quran': ['quran', 'tafsir', 'tajweed', 'ayat', 'কুরআন', 'তাফসির', 'তাজবীদ', 'সুরা'],
    'novel': ['novel', 'story', 'উপন্যাস', 'গল্প', 'কাহিনি', 'ভ্রমণ', 'সমগ্র', 'নাটক'],
    'dua': ['dua', 'zikr', 'azkar', 'munajat', 'দোয়া', 'জিকির', 'আমল', 'মুনাজাত']
}

def clean_text(text):
    """Deep cleaning of filenames"""
    if not text: return ""
    text = str(text)
    text = os.path.splitext(text)[0] # Remove .pdf
    # Remove things like "01. ", "02-", "[PDF]", website links
    text = re.sub(r'^[\d\.\-\_\(\)\[\]\s]+', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'www\.[a-zA-Z0-9-]+\.[a-z]+', '', text)
    return text.strip()

def detect_writer_smart(title, raw_text=""):
    """
    THE SUPER BRAIN 🧠
    1. Checks Knowledge Base.
    2. Checks Pattern Matching (Separators).
    3. Checks Honorifics.
    """
    search_text = (title + " " + raw_text).lower()
    
    # 1. Check AI Knowledge Base
    for keyword, writer in AI_KNOWLEDGE.items():
        if keyword in search_text:
            return writer

    # 2. Try Pattern Matching (Splitting by ' - ' or ' | ')
    # Looks for: "Book Name - Writer Name"
    separators = [r'\s+-\s+', r'\s+\|\s+', r'\s+–\s+', r'\s+by\s+', r'\s+_\s+']
    for sep in separators:
        parts = re.split(sep, title, 1)
        if len(parts) == 2:
            part1 = parts[0].strip()
            part2 = parts[1].strip()
            
            # Sub-logic: Which part is the writer?
            # If Part 2 has an honorific, it's the writer.
            if any(h in part2.lower() for h in HONORIFICS):
                return part2
            # If Part 1 has an honorific, it's the writer (Rare: "Imam Bukhari - Sahih")
            if any(h in part1.lower() for h in HONORIFICS):
                return part1
            
            # If no honorific, assume Part 2 is writer if it's short enough
            if len(part2) < 40 and not re.search(r'\d', part2):
                return part2

    return "অজ্ঞাত" # Bangla for Unknown

def detect_category(text):
    text = text.lower()
    for cat, keywords in CATEGORIES.items():
        if any(k in text for k in keywords):
            return cat.capitalize()
    return "General"

def generate_cover(book_id):
    try:
        width, height = 400, 600
        color = (15, 76, 58)
        img = Image.new('RGB', (width, height), color=color)
        d = ImageDraw.Draw(img)
        d.rectangle([20, 20, width-20, height-20], outline="#FFD700", width=5)
        filename = f"{book_id}_gen.jpg"
        path = os.path.join(IMAGES_DIR, filename)
        img.save(path)
        return f"images/{filename}"
    except:
        return ""

async def main():
    print("--- 🤖 STARTING INTELLIGENT ROBOT ---")
    
    try:
        client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
        await client.start()
    except Exception as e:
        print(f"Login Error: {e}")
        return

    # 1. LOAD EXISTING DATABASE
    all_books = []
    existing_ids = set()
    
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                all_books = json.load(f)
                for b in all_books:
                    existing_ids.add(b['id'])
        except: pass

    # 2. SCAN FOR NEW BOOKS (Last 200)
    print("Scanning Telegram for NEW books...")
    messages = await client.get_messages(CHANNEL_ID, limit=200)
    new_books_count = 0
    
    for message in reversed(messages):
        if message.id in existing_ids: continue

        if message.document and message.document.mime_type == 'application/pdf':
            # Get Name
            raw_name = ""
            if message.file and message.file.name: raw_name = message.file.name
            elif message.text: raw_name = message.text.split('\n')[0]
            
            if not raw_name: continue
            
            title = clean_text(raw_name)
            caption = message.text or ""
            
            # Intelligent Detection
            author = detect_writer_smart(title, caption)
            category = detect_category(title + " " + caption)
            
            # Cover
            cover_path = generate_cover(message.id)
            
            # Link
            clean_chan_id = str(CHANNEL_ID).replace("-100", "")
            link = f"https://t.me/c/{clean_chan_id}/{message.id}"

            book = {
                "id": message.id,
                "title": title,
                "author": author,
                "category": category,
                "link": link,
                "image": cover_path
            }
            
            all_books.append(book)
            existing_ids.add(message.id)
            new_books_count += 1
            print(f" + New: {title} | {author}")

    # 3. RE-SCAN OLD BOOKS (The Fix)
    # The robot now checks every single book in your database to see if it can fix "Unknown" authors
    print("Re-scanning OLD books for missing authors...")
    fixed_count = 0
    
    for book in all_books:
        # If author is missing, empty, or 'Unknown'/'অজ্ঞাত'
        if not book.get('author') or book['author'] in ["অজ্ঞাত", "Unknown", "", "অজ্ঞাত লেখক"]:
            
            # Try to detect again using the smart logic on the title
            new_author = detect_writer_smart(book['title'])
            
            if new_author != "অজ্ঞাত":
                book['author'] = new_author
                fixed_count += 1
                # Also clean the title (remove the author name from title if it was found there)
                # This keeps titles clean: "Sajid - Arif Azad" -> Title: "Sajid", Author: "Arif Azad"
                if new_author in book['title']:
                    book['title'] = book['title'].replace(new_author, "").replace("-", "").replace("|", "").strip()
                
                print(f" 🛠 Fixed: {book['title']} | ✍️ {new_author}")

    # 4. SAVE EVERYTHING
    if new_books_count > 0 or fixed_count > 0:
        all_books.sort(key=lambda x: x['id'], reverse=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_books, f, indent=4, ensure_ascii=False)
        print(f"--- ✅ DONE: Added {new_books_count} new, Fixed {fixed_count} old ---")
    else:
        print("--- Database up to date ---")

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
