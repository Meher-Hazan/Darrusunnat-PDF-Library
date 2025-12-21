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

# --- 📢 CHANNEL MAPPING (Channel Name = Category Name) ---
# Books from these channels will be categorized under these specific names
EXTRA_CHANNELS = {
    -1002165064274: 'ফুরফুরা শরীফ লাইব্রেরি',
    -1002586470798: 'হোমিওপ্যাথিক চিকিৎসা',
    -1002605692104: 'সিরাতুন্নবী (সা.)',
    -1002691091110: 'ইলমে তাসাওউফ',
    -1002524811470: 'তাফসীরুল কুরআন',
    -1002641268515: 'ইসলাম ও বিজ্ঞান',
    -1002581644796: 'সালাত (নামায)',
    -1002529113609: 'ফিতনা ও কিয়ামত',
    -1002613122395: 'হাদিসে রাসুল (সা.)',
    -1002511418534: 'নারী ও পর্দা',
    -1002685255937: 'সাওম (রোযা)',
    -1002619728556: 'আকিদা',
    -1002506980140: 'ফাতাওয়া ও মাসায়েল',
    -1002653136384: 'দরূদ শরীফ',
    -1002972117271: 'আরবি ভাষা ও সাহিত্য',
}

DATA_FILE = 'books_data.json'
IMAGES_DIR = 'images'

if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

# --- 🧠 AI KNOWLEDGE BASE (Fallback for Main Channel) ---
AI_KNOWLEDGE = {
    'bukhari': 'ইমাম বুখারী (রহ.)', 'muslim': 'ইমাম মুসলিম (রহ.)',
    'ariff azad': 'আরিফ আজাদ', 'mizanur': 'মিজানুর রহমান আজহারী',
    'iqbal': 'আল্লামা ইকবাল', 'paradoxical': 'আরিফ আজাদ',
    'taki': 'মুফতি তাকি উসমানী', 'shofi': 'মুফতি শফি উসমানী (রহ.)'
}

# Standard Categories (Used only for Main Channel now)
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
    'শিক্ষা ও ভাষা': ['learning', 'arabic', 'grammar', 'language', 'শিক্ষা', 'ভাষা', 'আরবি'],
    'দোয়া ও আমল': ['dua', 'zikr', 'azkar', 'munajat', 'দোয়া', 'জিকির', 'আমল'],
    'সমসাময়িক ও বিবিধ': ['contemporary', 'article', 'others', 'সমসাময়িক', 'প্রবন্ধ', 'বিবিধ']
}

def clean_text(text):
    if not text: return ""
    text = str(text)
    text = os.path.splitext(text)[0]
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
    print("--- 🤖 STARTING CHANNEL-AS-CATEGORY ROBOT ---")
    try:
        client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
        await client.start()
    except Exception as e:
        print(f"Login Error: {e}")
        return

    # 1. LOAD DB
    all_books = []
    seen_titles = set()
    existing_ids = set()

    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                all_books = json.load(f)
                for b in all_books: 
                    existing_ids.add(b['id'])
                    seen_titles.add(b['title'].lower().strip())
        except: pass

    # Scan Main Channel First (ID, ForcedName=None)
    channels_to_scan = [(MAIN_CHANNEL_ID, None)] 
    # Add Extra Channels (ID, ForcedName=ChannelName)
    for cid, name in EXTRA_CHANNELS.items():
        channels_to_scan.append((cid, name))

    # 2. SCANNING PROCESS
    new_count = 0
    
    for chat_id, channel_name in channels_to_scan:
        is_main = (chat_id == MAIN_CHANNEL_ID)
        print(f"📡 Scanning: {channel_name if channel_name else 'Main Channel'} ({chat_id})")
        
        try:
            clean_chan_id = str(chat_id).replace("-100", "")
            messages = await client.get_messages(chat_id, limit=100)
            pending_cover_path = None
            
            for message in reversed(messages):
                unique_id = int(f"{clean_chan_id}{message.id}")
                
                if unique_id in existing_ids:
                    pending_cover_path = None
                    continue

                # --- IMAGE HANDLING ---
                if message.photo:
                    try:
                        temp_filename = f"temp_{unique_id}.jpg"
                        temp_path = os.path.join(IMAGES_DIR, temp_filename)
                        await message.download_media(file=temp_path)
                        pending_cover_path = temp_path
                        print(f"   📸 Found cover in msg {message.id}")
                    except: pending_cover_path = None
                    continue

                # --- PDF HANDLING ---
                if message.document and message.document.mime_type == 'application/pdf':
                    raw_name = message.file.name if message.file else ""
                    if not raw_name and message.text: raw_name = message.text.split('\n')[0]
                    if not raw_name: 
                        pending_cover_path = None
                        continue
                    
                    title = clean_text(raw_name)
                    
                    # DEDUPLICATION: Skip if book exists in Main Channel
                    if not is_main and title.lower().strip() in seen_titles:
                        print(f"   ⚠️ Duplicate skipped: {title}")
                        if pending_cover_path and os.path.exists(pending_cover_path):
                            os.remove(pending_cover_path)
                        pending_cover_path = None
                        continue
                    
                    caption = message.text or ""
                    author = detect_writer_smart(title, caption)
                    
                    # CATEGORY LOGIC: If extra channel, use Channel Name. Else use AI.
                    if channel_name:
                        cat = channel_name
                    else:
                        cat = detect_category_smart(title + " " + caption)
                    
                    # COVER ASSIGNMENT
                    final_cover_rel_path = ""
                    if pending_cover_path and os.path.exists(pending_cover_path):
                        new_filename = f"{unique_id}.jpg"
                        new_path = os.path.join(IMAGES_DIR, new_filename)
                        try:
                            if os.path.exists(new_path): os.remove(new_path)
                            os.rename(pending_cover_path, new_path)
                            final_cover_rel_path = f"images/{new_filename}"
                        except: 
                            final_cover_rel_path = generate_cover(unique_id)
                    else:
                        final_cover_rel_path = generate_cover(unique_id)
                    
                    link = f"https://t.me/c/{clean_chan_id}/{message.id}"

                    book = {
                        "id": unique_id,
                        "title": title,
                        "author": author,
                        "category": cat, # This will now be the Channel Name
                        "link": link,
                        "image": final_cover_rel_path
                    }
                    
                    all_books.append(book)
                    existing_ids.add(unique_id)
                    seen_titles.add(title.lower().strip())
                    new_count += 1
                    print(f"   + Added: {title} -> {cat}")
                    pending_cover_path = None

        except Exception as e:
            print(f"Error scanning {chat_id}: {e}")

    # 3. SAVE & PUSH
    if new_count > 0:
        all_books.sort(key=lambda x: x['id'], reverse=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_books, f, indent=4, ensure_ascii=False)
        
        print(f"--- ✅ SUCCESS: Added {new_count} books ---")
        
        try:
            print("--- 🚀 PUSHING TO GITHUB ---")
            os.system('git config --global user.email "bot@library.com"')
            os.system('git config --global user.name "Smart Bot"')
            os.system('git add .')
            os.system('git commit -m "Auto: Added channel books"')
            os.system('git push')
        except: pass
    else:
        print("--- Database Up to Date ---")

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
