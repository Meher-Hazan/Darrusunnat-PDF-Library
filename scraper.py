import os
import json
import asyncio
import re
import shutil
from telethon import TelegramClient
from telethon.sessions import StringSession
from PIL import Image, ImageDraw

# --- CONFIGURATION ---
API_ID = int(os.environ.get('API_ID', 0))
API_HASH = os.environ.get('API_HASH', '')
SESSION_STRING = os.environ.get('SESSION_STRING', '')
MAIN_CHANNEL_ID = int(os.environ.get('CHANNEL_ID', 0))

# --- 📢 CONFIGURE EXTRA CHANNELS HERE ---
# Logic: 'Channel ID': 'Forced Category Name'
# If you set category to None, it will use AI to guess.
EXTRA_CHANNELS = {
    -1002165064274: 'অন্যান্য (General)', # ফুরফুরা শরীফ - adjust category if needed
    -1002586470798: 'বিজ্ঞান ও ইসলাম', # হোমিওপ্যাথিক চিকিৎসা - Science/Medical
    -1002605692104: 'সিরাত ও জীবনী', # সিরাতুন্নবী
    -1002691091110: 'আত্মশুদ্ধি ও তাসাউফ', # ইলমে তাসাওউফ
    -1002524811470: 'তাফসীর ও কুরআন', # তাফসীরুল কুরআন
    -1002641268515: 'বিজ্ঞান ও ইসলাম', # ইসলাম ও বিজ্ঞান
    -1002581644796: 'ফিকহ ও ফতোয়া', # সালাত (নামায) - Fiqh/Salah
    -1002529113609: 'আকিদা ও বিশ্বাস', # ফিতনা, কিয়ামত... - Aqeedah
    -1002613122395: 'হাদিস ও সুন্নাহ', # হাদিসে রাসুল
    -1002511418534: 'নারী ও পর্দা', # নারী, বিবাহ...
    -1002685255937: 'ফিকহ ও ফতোয়া', # সাওম (রোযা) - Fiqh
    -1002619728556: 'আকিদা ও বিশ্বাস', # আকিদা
    -1002506980140: 'ফিকহ ও ফতোয়া', # ফাতাওয়া, মাসায়েল...
    -1002653136384: 'দোয়া ও আমল', # দরূদ শরীফ - Dua/Amal
    -1002972117271: 'শিক্ষা ও ভাষা', # আরবি ভাষা ও সাহিত্য
}

DATA_FILE = 'books_data.json'
IMAGES_DIR = 'images'

if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

# --- 🧠 AI KNOWLEDGE BASE ---
AI_KNOWLEDGE = {
    'bukhari': 'ইমাম বুখারী (রহ.)', 'muslim': 'ইমাম মুসলিম (রহ.)',
    'ariff azad': 'আরিফ আজাদ', 'mizanur': 'মিজানুর রহমান আজহারী',
    'iqbal': 'আল্লামা ইকবাল', 'paradoxical': 'আরিফ আজাদ',
    'taki': 'মুফতি তাকি উসমানী', 'shofi': 'মুফতি শফি উসমানী (রহ.)'
}
HONORIFICS = ['dr.', 'prof.', 'sheikh', 'shaykh', 'imam', 'mufti', 'maulana']

CATEGORIES = {
    'তাফসির ও কুরআন': ['quran', 'tafsir', 'tajweed', 'ayat', 'surah', 'কুরআন', 'তাফসির'],
    'হাদিস ও সুন্নাহ': ['hadith', 'bukhari', 'muslim', 'tirmidhi', 'sunan', 'sahih', 'হাদিস', 'বুখারী'],
    'আকিদা ও বিশ্বাস': ['aqeedah', 'tawheed', 'iman', 'shirk', 'kufr', 'bidat', 'আকিদা', 'ঈমান'],
    'ফিকহ ও ফতোয়া': ['fiqh', 'fatwa', 'masala', 'salah', 'namaz', 'zakat', 'ফিকহ', 'ফতোয়া'],
    'ইতিহাস ও ঐতিহ্য': ['history', 'battle', 'war', 'khilafat', 'ottoman', 'ইতিহাস', 'ঐতিহ্য'],
    'সিরাত ও জীবনী': ['seerah', 'biography', 'sirat', 'prophet', 'sahaba', 'সিরাত', 'নবী', 'জীবনী'],
    'আত্মশুদ্ধি ও তাসাউফ': ['tasawwuf', 'sufism', 'tazkiyah', 'atma', 'আত্মশুদ্ধি', 'তাসাউফ', 'অন্তর'],
    'পারিবারিক ও দাম্পত্য': ['marriage', 'family', 'parenting', 'husband', 'wife', 'বিয়ে', 'দাম্পত্য', 'পরিবার'],
    'নারী ও পর্দা': ['women', 'nari', 'hijab', 'porda', 'নারী', 'মহিলা', 'পর্দা'],
    'রাজনীতি ও রাষ্ট্র': ['politics', 'state', 'democracy', 'রাজনীতি', 'রাষ্ট্র', 'গণতন্ত্র'],
    'দাওয়াত ও তাবলীগ': ['dawah', 'tabligh', 'mission', 'দাওয়াত', 'তাবলীগ', 'মিশন'],
    'বিজ্ঞান ও ইসলাম': ['science', 'medical', 'creation', 'বিজ্ঞান', 'মেডিকেল', 'সৃষ্টিতত্ত্ব'],
    'উপন্যাস ও সাহিত্য': ['novel', 'story', 'literature', 'poem', 'উপন্যাস', 'গল্প', 'কাহিনি', 'কবিতা'],
    'দোয়া ও আমল': ['dua', 'zikr', 'azkar', 'munajat', 'দোয়া', 'জিকির', 'আমল'],
    'সমসাময়িক ও বিবিধ': ['contemporary', 'article', 'others', 'সমসাময়িক', 'প্রবন্ধ', 'বিবিধ']
}

def clean_text(text):
    if not text: return ""
    text = str(text)
    text = os.path.splitext(text)[0]
    # Removes starting numbers like "01. " but KEEPS volume info at the end
    text = re.sub(r'^[\d\.\-\_\(\)\[\]\s]+', '', text)
    return text.strip()

def detect_writer_smart(title, raw_text=""):
    search = (title + " " + raw_text).lower()
    for k, v in AI_KNOWLEDGE.items():
        if k in search: return v
    if " - " in title: 
        parts = title.split(" - ")
        if len(parts) > 1: return parts[-1].strip()
    return "অজ্ঞাত"

def detect_category_smart(text):
    text = text.lower()
    for cat_name, keywords in CATEGORIES.items():
        if any(k in text for k in keywords): return cat_name
    return "অন্যান্য (General)"

def generate_cover(book_id):
    try:
        width, height = 400, 600
        color = (20, 90, 72)
        img = Image.new('RGB', (width, height), color=color)
        d = ImageDraw.Draw(img)
        d.rectangle([20, 20, width-20, height-20], outline="#FFD700", width=5)
        path = os.path.join(IMAGES_DIR, f"{book_id}_gen.jpg")
        img.save(path)
        return f"images/{book_id}_gen.jpg"
    except: return ""

async def main():
    print("--- 🤖 STARTING SMART MERGE ROBOT ---")
    try:
        client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
        await client.start()
    except Exception as e:
        print(f"Login Error: {e}")
        return

    # 1. LOAD DB & PREPARE FOR DEDUPLICATION
    all_books = []
    # We use this set to remember titles we have already processed
    seen_titles = set()
    existing_ids = set()

    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                all_books = json.load(f)
                for b in all_books: 
                    existing_ids.add(b['id'])
                    # Add existing books to seen list so we don't add them again
                    seen_titles.add(b['title'].lower().strip())
        except: pass

    # List of all channels to scan (Main + Extras)
    # Format: (Channel_ID, Forced_Category_Name_Or_None)
    channels_to_scan = [(MAIN_CHANNEL_ID, None)] 
    for cid, cat in EXTRA_CHANNELS.items():
        channels_to_scan.append((cid, cat))

    # 2. SCANNING PROCESS
    new_count = 0
    
    for chat_id, forced_category in channels_to_scan:
        is_main = (chat_id == MAIN_CHANNEL_ID)
        print(f"📡 Scanning Channel ID: {chat_id} (Main: {is_main})")
        
        try:
            clean_chan_id = str(chat_id).replace("-100", "")
            messages = await client.get_messages(chat_id, limit=100)
            pending_cover = None
            
            for message in reversed(messages):
                # Generate a unique ID: ChannelID + MessageID
                unique_id = int(f"{clean_chan_id}{message.id}")
                
                # Check if this specific file ID exists
                if unique_id in existing_ids:
                    pending_cover = None
                    continue

                # Handle Image (Context Aware)
                if message.photo:
                    try:
                        path = await message.download_media(file=os.path.join(IMAGES_DIR, f"{unique_id}.jpg"))
                        pending_cover = path
                    except: pending_cover = None
                    continue

                # Handle PDF
                if message.document and message.document.mime_type == 'application/pdf':
                    raw_name = message.file.name if message.file else ""
                    if not raw_name and message.text: raw_name = message.text.split('\n')[0]
                    if not raw_name: 
                        pending_cover = None
                        continue
                    
                    title = clean_text(raw_name)
                    
                    # --- 🛑 DEDUPLICATION LOGIC ---
                    # Check if we already have this book title in our library
                    # BUT ONLY skip if it's from an EXTRA channel.
                    # We always trust the Main Channel.
                    if not is_main and title.lower().strip() in seen_titles:
                        print(f"   ⚠️ Duplicate ignored: {title}")
                        pending_cover = None
                        continue
                    
                    caption = message.text or ""
                    author = detect_writer_smart(title, caption)
                    
                    # Category Logic: Use forced category if provided, else detect
                    if forced_category:
                        cat = forced_category
                    else:
                        cat = detect_category_smart(title + " " + caption)
                    
                    # Cover Logic
                    final_cover = ""
                    if pending_cover:
                        final_cover = f"images/{unique_id}.jpg"
                    else:
                        final_cover = generate_cover(unique_id)
                    
                    link = f"https://t.me/c/{clean_chan_id}/{message.id}"

                    book = {
                        "id": unique_id,
                        "title": title,
                        "author": author,
                        "category": cat,
                        "link": link,
                        "image": final_cover
                    }
                    
                    all_books.append(book)
                    existing_ids.add(unique_id)
                    seen_titles.add(title.lower().strip()) # Mark as seen
                    new_count += 1
                    print(f"   + Added: {title} -> {cat}")
                    pending_cover = None

        except Exception as e:
            print(f"Error scanning {chat_id}: {e}")

    # 3. SAVE & PUSH
    if new_count > 0:
        all_books.sort(key=lambda x: x['id'], reverse=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_books, f, indent=4, ensure_ascii=False)
        
        print(f"--- ✅ SUCCESS: Added {new_count} new books ---")
        
        try:
            print("--- 🚀 PUSHING TO GITHUB ---")
            os.system('git config --global user.email "bot@library.com"')
            os.system('git config --global user.name "Smart Bot"')
            os.system('git add .')
            os.system('git commit -m "Auto: Smart merge update"')
            os.system('git push')
        except: pass
    else:
        print("--- Database Up to Date ---")

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())