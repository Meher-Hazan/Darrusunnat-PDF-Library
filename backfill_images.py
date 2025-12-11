import pandas as pd
import os
import time
from telethon.sync import TelegramClient

# --- CONFIG ---
# ⚠️ REPLACE THESE WITH YOUR KEYS ⚠️
API_ID = 29962027          
API_HASH = '53add75259c7f9f39fed3f84769212cd'
CHANNEL = 'SobBoiErPdf'
CSV_FILE = 'database.csv'

# Login (This will ask for your number/code only once)
client = TelegramClient('anon', API_ID, API_HASH)
client.start()

print("Reading database...")
# Read CSV (No header: 0=Title, 1=Link, 2=ImgPath)
df = pd.read_csv(CSV_FILE, header=None, names=['Title', 'Link', 'ImgPath'])

print(f"Found {len(df)} books. Checking for missing covers...")

os.makedirs('images', exist_ok=True)
download_count = 0

for index, row in df.iterrows():
    img_path = str(row['ImgPath']).strip()
    
    # Only download if we don't have it yet
    if not os.path.exists(img_path):
        try:
            # Extract Message ID from Link (e.g., .../37891 -> 37891)
            msg_id = int(row['Link'].split('/')[-1])
            
            # We assume the picture is in the message BEFORE the PDF (msg_id - 1)
            # Fetch the message
            msg = client.get_messages(CHANNEL, ids=msg_id - 1)
            
            if msg and msg.photo:
                print(f"[Downloading] {row['Title'][:20]}...")
                client.download_media(msg.photo, file=img_path)
                download_count += 1
                
                # Sleep briefly to avoid Telegram "FloodWait" ban
                if download_count % 10 == 0:
                    time.sleep(2)
            else:
                print(f"[Skipping] No photo found for ID {msg_id}")
                
        except Exception as e:
            print(f"Error on {row['Title']}: {e}")

print("Done! All images downloaded.")
client.disconnect()
