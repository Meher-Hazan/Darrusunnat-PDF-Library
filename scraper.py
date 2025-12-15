import os
import json
import asyncio
import re
import random
import shutil
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

# --- 🧠 BRAIN 1: WRITER KNOWLEDGE BASE ---
AI_KNOWLEDGE = {
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
    'rabindra': 'রবীন্দ্রনাথ ঠাকুর',
    'shofi': 'মুফতি শফি উসমানী (রহ.)',
    'taki': 'মুফতি তাকি উসমানী',
    'moududi': 'সাইয়েদ আবুল আ\'লা মওদুদী',
    'yusuf': 'ইউসুফ আল কারযাভী',
    'zaker': 'ড. জাকির নায়েক',
    'zakir': 'ড. জাকির নায়েক'
}

HONORIFICS = [
    'dr.', 'dr ', 'prof.', 'sheikh', 'shaykh', 'imam', 'mufti', 'maulana', 
    'moulana', 'allama', 'hafez', 'qari', 'ustadh', 'writer', 'author',
    'ড.', 'অধ্যাপক', 'শায়খ', 'ইমাম', 'মুফতি', 'মাওলানা', 'আল্লামা', 'হাফেজ'
]

# --- 📚 BRAIN 2: SUPER CATEGORIES ---
CATEGORIES = {
    'তাফসির ও কুরআন': ['quran', 'tafsir', 'tajweed', 'ayat', 'surah', 'tilawat', 'tafseer', 'tafsirul', 'কুরআন', 'কোরআন', 'তাফসির', 'তাফসীর', 'তাজবীদ', 'সুরা', 'আয়াত', 'ইবনে কাসির', 'জালালাইন', 'তাফহীমুল', 'মারেফুল'],
    'হাদিস ও সুন্নাহ': ['hadith', 'bukhari', 'muslim', 'tirmidhi', 'sunan', 'sahih', 'nasai', 'abu daud', 'ibn majah', 'mishkat', 'হাদিস', 'হাদীস', 'বুখারী', 'মুসলিম', 'তিরমিযী', 'সুনান', 'সহীহ', 'আবু দাউদ', 'রিয়াদুস', 'মিশকাত', 'শামায়েলে'],
    'আকিদা ও বিশ্বাস': ['aqeedah', 'tawheed', 'iman', 'shirk', 'kufr', 'bidat', 'sunnah', 'faith', 'আকিদা', 'আকাইদ', 'ঈমান', 'তাওহীদ', 'শিরক', 'কুফর', 'বিদআত', 'সুন্নাত', 'বিশ্বাস', 'পরকাল', 'জান্নাত', 'জাহান্নাম', 'কবর', 'হাশর'],
    'ফিকহ ও ফতোয়া': ['fiqh', 'fatwa', 'masala', 'salah', 'namaz', 'zakat', 'hajj', 'sawm', 'rules', 'ফিকহ', 'ফতোয়া', 'মাসায়েল', 'নামাজ', 'সালাত', 'রোজা', 'হজ', 'যাকাত', 'ওযু', 'গোসল', 'তাহারাত', 'হালাল', 'হারাম', 'বিধান'],
    'ইতিহাস ও ঐতিহ্য': ['history', 'battle', 'war', 'khilafat', 'ottoman', 'crusade', 'civilization', 'ইতিহাস', 'ঐতিহ্য', 'যুদ্ধ', 'জিহাদ', 'খেলাফত', 'খিলাফত', 'ক্রুসেড', 'অটোমান', 'উসমানীয়', 'মোগল', 'ভারতবর্ষ', 'স্পেন', 'বিজয়'],
    'সিরাত ও জীবনী': ['seerah', 'biography', 'sirat', 'prophet', 'sahaba', 'tabeyi', 'life', 'সিরাত', 'নবী', 'রাসূল', 'জীবনী', 'সাহাবা', 'সাহাবী', 'তাবেঈ', 'মনীষী', 'স্মৃতিকথা', 'আত্মজীবনী', 'সীরাত', 'জীবনালেখ্য'],
    'আত্মশুদ্ধি ও তাসাউফ': ['tasawwuf', 'sufism', 'tazkiyah', 'atma', 'qalb', 'spirituality', 'আত্মশুদ্ধি', 'তাসাউফ', 'সুফিবাদ', 'অন্তর', 'কলব', 'নফস', 'ইহসান', 'জুহুদ', 'আত্মা', 'মনন', 'চরিত্র'],
    'পারিবারিক ও দাম্পত্য': ['marriage', 'wedding', 'family', 'parenting', 'husband', 'wife', 'child', 'বিয়ে', 'বিবাহ', 'দাম্পত্য', 'পরিবার', 'সংসার', 'স্বামী', 'স্ত্রী', 'সন্তান', 'প্যারেন্টিং'],
    'নারী ও পর্দা': ['women', 'nari', 'hijab', 'porda', 'sister', 'muslimah', 'নারী', 'মহিলা', 'পর্দা', 'হিজাব', 'নিসাব', 'মা', 'বোন'],
    'রাজনীতি ও রাষ্ট্র': ['politics', 'siyasat', 'state', 'democracy', 'socialism', 'secularism', 'movement', 'রাজনীতি', 'রাষ্ট্র', 'ইসলামি আন্দোলন', 'গণতন্ত্র', 'সমাজতন্ত্র', 'মতবাদ', 'নেতৃত্ব', 'শাষন', 'বিচার'],
    'দাওয়াত ও তাবলীগ': ['dawah', 'tabligh', 'mission', 'preaching', 'দাওয়াত', 'তাবলীগ', 'মিশন', 'প্রচার', 'দ্বীন', 'আমন্ত্রণ'],
    'বিজ্ঞান ও ইসলাম': ['science', 'medical', 'creation', 'universe', 'technology', 'বিজ্ঞান', 'মেডিকেল', 'সৃষ্টিতত্ত্ব', 'মহাকাশ', 'প্রযুক্তি', 'স্বাস্থ্য', 'চিকিৎসা'],
    'উপন্যাস ও সাহিত্য': ['novel', 'story', 'literature', 'poem', 'fiction', 'thriller', 'উপন্যাস', 'গল্প', 'কাহিনি', 'কবিতা', 'সাহিত্য', 'ভ্রমণ', 'সমগ্র', 'নাটক', 'থ্রিলার', 'রহস্য'],
    'দোয়া ও আমল': ['dua', 'zikr', 'azkar', 'munajat', 'ruqyah', 'wazifa', 'amal', 'দোয়া', 'জিকির', 'আমল', 'মুনাজাত', 'রুকাইয়া', 'অজিফা', 'দোআ', 'জিকর'],
    'শিক্ষা ও ভাষা': ['learning', 'arabic', 'grammar', 'nahu', 'sarf', 'language', 'education', 'শিক্ষা', 'ভাষা', 'আরবি', 'ব্যাকরণ', 'নাহু', 'সরফ', 'অভিধান', 'ডিকশনারি', 'পড়া', 'লেখা'],
    'ম্যাগাজিন ও সাময়িকী': ['magazine', 'journal', 'article', 'monthly', 'weekly', 'ম্যাগাজিন', 'সাময়িকী', 'পত্রিকা', 'সংখ্যা', 'মান্থলি'],
    'খুতবা ও বয়ান': ['khutbah', 'lecture', 'waz', 'speech', 'boyan', 'খুতবা', 'বয়ান', 'ওয়াজ', 'বক্তৃতা', 'আলোচনা'],
    'সমসাময়িক ও বিবিধ': ['contemporary', 'article', 'thesis', 'others', 'debate', 'atheism', 'সমসাময়িক', 'প্রবন্ধ', 'নিবন্ধ', 'বিবিধ', 'অন্যান্য', 'নাস্তিকতা', 'সংশয়', 'জবাব', 'তর্ক']
}

def clean_text(text):
    if not text: return ""
    text = str(text)
    text = os.path.splitext(text)[0]
    text = re.sub(r'^[\d\.\-\_\(\)\[\]\s]+', '', text) # Remove leading numbers/junk
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    return text.strip()

def get_base_title(text):
    """Simplifies title for volume matching (removes Vol 1, Part 2, etc)"""
    text = clean_text(text)
    # Remove "Vol X", "Khondo X", numbers at end
    text = re.sub(r'(vol|part|khondo|khanda|খন্ড|খণ্ড)[\s\.]*\d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\d+$', '', text)
    return text.strip()

def detect_writer_smart(title, raw_text=""):
    search_text = (title + " " + raw_text).lower()
    for keyword, writer in AI_KNOWLEDGE.items():
        if keyword in search_text: return writer

    separators = [r'\s+-\s+', r'\s+\|\s+', r'\s+–\s+', r'\s+by\s+', r'\s+_\s+']
    for sep in separators:
        parts = re.split(sep, title, 1)
        if len(parts) == 2:
            part1 = parts[0].strip()
            part2 = parts[1].strip()
            if any(h in part2.lower() for h in HONORIFICS): return part2
            if any(h in part1.lower() for h in HONORIFICS): return part1
            if len(part2) < 40 and not re.search(r'\d', part2): return part2
    return "অজ্ঞাত"

def detect_category_smart(text):
    text = text.lower()
    for cat_name, keywords in CATEGORIES.items():
        if any(k in text for k in keywords):
            return cat_name
    return "অন্যান্য (General)"

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
    except: return ""

async def main():
    print("--- 🤖 STARTING ULTIMATE SCRAPER ---")
    
    try:
        client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
        await client.start()
    except Exception as e:
        print(f"Login Error: {e}")
        return

    # 1. LOAD DB
    all_books = []
    existing_ids = set()
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                all_books = json.load(f)
                for b in all_books: existing_ids.add(b['id'])
        except: pass

    # 2. SCAN NEW (Order: Oldest -> Newest to handle "Image then PDF" flow)
    print("Scanning Telegram for NEW books...")
    messages = await client.get_messages(CHANNEL_ID, limit=200)
    
    new_books_count = 0
    pending_cover = None # Stores path of the last seen image
    
    for message in reversed(messages): # Processing chronologically
        
        # LOGIC: Image Handling
        if message.photo:
            try:
                # Download photo temporarily
                path = await message.download_media(file=os.path.join(IMAGES_DIR, f"{message.id}.jpg"))
                pending_cover = path
            except:
                pending_cover = None
            continue # Move to next message (looking for PDF)

        if message.id in existing_ids: 
            pending_cover = None # Reset if we already have this book
            continue

        if message.document and message.document.mime_type == 'application/pdf':
            # Found a PDF!
            raw_name = ""
            if message.file and message.file.name: raw_name = message.file.name
            elif message.text: raw_name = message.text.split('\n')[0]
            
            if not raw_name: 
                pending_cover = None
                continue
            
            title = clean_text(raw_name)
            caption = message.text or ""
            
            # Smart Detection
            author = detect_writer_smart(title, caption)
            category = detect_category_smart(title + " " + caption)
            
            # --- COVER LOGIC ---
            final_cover_path = ""
            
            # 1. Check if we have a pending cover from previous message
            if pending_cover and os.path.exists(pending_cover):
                final_cover_path = f"images/{message.id}.jpg"
                # Rename the pending cover to match the book ID
                # (The download saved it as photo_ID.jpg, we want book_ID.jpg)
                # Actually, simply reusing the downloaded file is fine if we rename it
                target_path = os.path.join(IMAGES_DIR, f"{message.id}.jpg")
                if pending_cover != target_path:
                    shutil.move(pending_cover, target_path)
                final_cover_path = f"images/{message.id}.jpg"
                print(f" 📸 Used Uploaded Cover for: {title}")
            
            # 2. Volume Logic (Check if same book exists)
            if not final_cover_path:
                base = get_base_title(title)
                # Look in existing database
                for b in all_books:
                    if get_base_title(b['title']) == base and b.get('image') and 'gen.jpg' not in b['image']:
                        final_cover_path = b['image']
                        print(f" 📚 Found Volume Match for: {title}")
                        break
            
            # 3. Generate Fallback
            if not final_cover_path:
                final_cover_path = generate_cover(message.id)

            # Build Link
            clean_chan_id = str(CHANNEL_ID).replace("-100", "")
            link = f"https://t.me/c/{clean_chan_id}/{message.id}"

            book = { "id": message.id, "title": title, "author": author, "category": category, "link": link, "image": final_cover_path }
            all_books.append(book)
            existing_ids.add(message.id)
            new_books_count += 1
            
            # Reset pending cover after using it
            pending_cover = None

    # 3. RE-SORT OLD BOOKS (Maintenance)
    print("Self-repairing OLD books...")
    fixed_count = 0
    for book in all_books:
        # Check Image
        if not book.get('image'):
            book['image'] = generate_cover(book['id'])
        
        # Check Category
        new_cat = detect_category_smart(book['title'] + " " + (book.get('author') or ""))
        if new_cat != book.get('category') and new_cat != "অন্যান্য (General)":
            book['category'] = new_cat
            fixed_count += 1
            
        # Check Author
        if book.get('author') in ["অজ্ঞাত", "Unknown", "", None]:
            new_auth = detect_writer_smart(book['title'])
            if new_auth != "অজ্ঞাত": book['author'] = new_auth

    # 4. SAVE & PUSH
    if new_books_count > 0 or fixed_count > 0:
        all_books.sort(key=lambda x: x['id'], reverse=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_books, f, indent=4, ensure_ascii=False)
        
        print(f"--- ✅ SUCCESS: Added {new_books_count}, Fixed {fixed_count} ---")
        
        # AUTO PUSH
        try:
            print("--- 🚀 PUSHING TO GITHUB ---")
            os.system('git config --global user.email "bot@library.com"')
            os.system('git config --global user.name "Auto Bot"')
            os.system('git add .')
            os.system('git commit -m "Auto Update: Added books & images"')
            os.system('git push')
            print("--- ✅ DONE ---")
        except Exception as e:
            print(f"Git Error: {e}")
    else:
        print("--- Database Up to Date ---")

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
