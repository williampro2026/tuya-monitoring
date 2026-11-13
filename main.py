import os
import json
import time
import paho.mqtt.client as mqtt
from tuya_connector import TuyaOpenPulsar, TuyaPulsarMessage

# --- 1. TUYA CONFIGURATION ---
ACCESS_ID = os.environ.get("ACCESS_ID", "f8f5dyjasxsxn8mepag")
ACCESS_SECRET = os.environ.get("ACCESS_SECRET", "c60366518a15486eab49fb51a376e704")
PULSAR_URL = os.environ.get("PULSAR_URL", "pulsar+ssl://mqe-sg.iotbing.com:7285/")
MQ_ENV = os.environ.get("MQ_ENV", "TEST")

# --- 2. EMQX CONFIGURATION ---
# GANTI DENGAN DATA DARI DASHBOARD EMQX ANDA
EMQX_HOST = os.environ.get("EMQX_HOST", "cloud-intl.emqx.com") # Sesuaikan Host EMQX Anda
EMQX_PORT = int(os.environ.get("EMQX_PORT", 1883))
EMQX_USER = os.environ.get("EMQX_USER", "username_emqx_anda")  
EMQX_PASS = os.environ.get("EMQX_PASS", "password_emqx_anda")  
EMQX_TOPIC = "tuya/ph_sensor/status" 

# --- Inisialisasi MQTT Client (EMQX) ---
mqtt_client = mqtt.Client("TuyaPH_Bridge")
mqtt_client.username_pw_set(EMQX_USER, EMQX_PASS)

try:
    print("⏳ Connecting to EMQX Cloud...")
    mqtt_client.connect(EMQX_HOST, EMQX_PORT, 60)
    mqtt_client.loop_start() 
    print("✅ Connected to EMQX!")
except Exception as e:
    print(f"❌ Failed to connect to EMQX: {e}")

# --- 3. REAL-TIME MESSAGE CALLBACK ---
def message_received(msg: TuyaPulsarMessage):
    try:
        data_json = json.loads(msg.payload)
        
        if 'payload' in data_json and 'data' in data_json['payload']:
            biz_data = data_json['payload']['data'].get('bizData', {})
            
            if 'properties' in biz_data:
                dev_id = biz_data.get('devId', 'unknown')
                
                val_ph = None
                val_orp = None
                val_temp = None
                
                for item in biz_data['properties']:
                    code = item['code']
                    value = item['value']
                    
                    if code in ['PH_Number', 'ph_current']:
                        val_ph = value / 100.0 if value > 14 else value
                        print(f"🧪 [pH] Received: {val_ph}")
                        
                    elif code in ['ORP_Number', 'orp_current']:
                        val_orp = value
                        print(f"⚡ [ORP] Received: {val_orp} mV")
                        
                    elif code in ['water_tempture_c', 'temp_current']:
                        val_temp = value / 10.0 if value > 100 else value
                        print(f"🌡️ [Temperature] Received: {val_temp} °C")
                
                # Send to EMQX
                if val_ph is not None or val_orp is not None or val_temp is not None:
                    payload_emqx = {
                        "device_id": dev_id,
                        "timestamp": int(time.time())
                    }
                    
                    if val_ph is not None: payload_emqx["ph"] = val_ph
                    if val_orp is not None: payload_emqx["orp"] = val_orp
                    if val_temp is not None: payload_emqx["temperature"] = val_temp
                    
                    json_emqx = json.dumps(payload_emqx)
                    mqtt_client.publish(EMQX_TOPIC, json_emqx, qos=1)
                    print(f"🚀 Data sent to EMQX: {json_emqx}")
                    
    except Exception as e:
        print(f"Error processing data: {e}")

# --- 4. START TUYA PULSAR ---
print("⏳ Starting Tuya Courier (Pulsar)...")
try:
    open_pulsar = TuyaOpenPulsar(ACCESS_ID, ACCESS_SECRET, PULSAR_URL, env=MQ_ENV)
    # Perhatikan: fungsi yang dipanggil sekarang adalah 'message_received'
    open_pulsar.start(message_received) 
    print("✅ Waiting for real-time data from pH device...")
    
    while True:
        time.sleep(1)
except Exception as e:
    print(f"❌ Failed to connect to Tuya: {e}")
