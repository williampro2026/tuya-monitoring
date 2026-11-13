import os
import json
import time
from tuya_connector import TuyaOpenPulsar, TuyaPulsarMessage

# 1. Ambil kunci rahasia dari Environment Variable Render
ACCESS_ID = os.environ.get("ACCESS_ID", "f8f5dyjasxsxn8mepag")
ACCESS_SECRET = os.environ.get("ACCESS_SECRET", "c60366518a15486eab49fb51a376e704")
PULSAR_URL = os.environ.get("PULSAR_URL", "pulsar+ssl://mqe-sg.iotbing.com:7285/")
MQ_ENV = os.environ.get("MQ_ENV", "TEST")

# 2. Fungsi saat data masuk
def pesan_masuk(msg: TuyaPulsarMessage):
    print(f"📥 Data masuk: {msg.payload}")
    try:
        data_json = json.loads(msg.payload)
        if 'data' in data_json and 'properties' in data_json['data']:
            for item in data_json['data']['properties']:
                code = item['code']
                value = item['value']
                
                if code == 'water_tempture_c':
                    print(f"🌡️ Suhu: {value} °C")
                elif code == 'PH_Number':
                    ph_asli = value / 100.0
                    print(f"🧪 pH: {ph_asli}")
                elif code == 'ORP_Number':
                    print(f"⚡ ORP: {value} mV")
    except Exception as e:
        print(f"Error memproses data: {e}")

# 3. Jalankan koneksi
print("⏳ Memulai Kurir Tuya...")

try:
    open_pulsar = TuyaOpenPulsar(ACCESS_ID, ACCESS_SECRET, PULSAR_URL, env=MQ_ENV)
    open_pulsar.start(pesan_masuk)
    print("✅ Kurir siap! Menunggu data dari sensor...")
    
    # Looping agar program tidak mati
    while True:
        time.sleep(1)
except Exception as e:
    print(f"❌ Gagal terhubung: {e}")
