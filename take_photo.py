import time
import serial
from picamera2 import Picamera2
from PIL import Image
import io

# --- LoRa-Konstanten ---
# Passen Sie diese an die Konfiguration Ihres HAT an
LORA_PORT = '/dev/ttyS0'
LORA_BAUDRATE = 9600
MAX_PAYLOAD_SIZE = 200  # Effektive max. Datenmenge pro LoRa-Paket (inkl. Metadaten)

def setup_lora_serial():
    """Initialisiert die serielle Schnittstelle für das LoRa HAT."""
    try:
        lora_serial = serial.Serial(
            port=LORA_PORT, 
            baudrate=LORA_BAUDRATE,
            timeout=1
        )
        print(f"LoRa-Schnittstelle auf {LORA_PORT} geöffnet.")
        return lora_serial
    except serial.SerialException as e:
        print(f"FEHLER: Kann serielle Schnittstelle nicht öffnen: {e}")
        return None

def compress_and_get_bytes(input_filename):
    """
    Komprimiert das Bild extrem und gibt die Daten als Byte-Array zurück.
    
    HINWEIS: Für LoRa ist die Komprimierung entscheidend!
    Das Bild wird hier auf 100x100 Pixel und sehr niedrige Qualität reduziert.
    """
    try:
        img = Image.open(input_filename)
        
        # Stark verkleinern (z.B. auf 100x100 Pixel)
        # LoRa kann keine großen Bilder übertragen.
        img = img.resize((100, 100)) 
        
        # In einen Bytes-Puffer schreiben (mit niedriger JPEG-Qualität)
        byte_arr = io.BytesIO()
        # Quality=20 ist eine sehr aggressive Komprimierung
        img.save(byte_arr, format='JPEG', quality=20) 
        
        print(f"Bildgröße nach Komprimierung: {len(byte_arr.getvalue())} Bytes.")
        return byte_arr.getvalue()
        
    except Exception as e:
        print(f"Fehler bei der Bildverarbeitung: {e}")
        return None

def send_data_via_lora(lora_serial, data):
    """
    Teilt die Bilddaten in LoRa-Pakete auf und sendet sie nacheinander.
    """
    if not lora_serial or not data:
        print("Senden fehlgeschlagen: Serielle Schnittstelle nicht bereit oder keine Daten.")
        return

    total_chunks = (len(data) + MAX_PAYLOAD_SIZE - 1) // MAX_PAYLOAD_SIZE
    print(f"Beginne Senden von {total_chunks} Paketen...")

    # Zuerst Metadaten senden (Gesamtgröße und Anzahl)
    # Beispiel-Protokoll: START:<Gesamt-Bytes>:<Total-Pakete>
    start_message = f"START:{len(data)}:{total_chunks}:".encode('utf-8')
    lora_serial.write(start_message)
    time.sleep(1) # Kurze Pause nach dem Senden der Startnachricht

    # Sende alle Datenpakete
    for i in range(total_chunks):
        start = i * MAX_PAYLOAD_SIZE
        end = min((i + 1) * MAX_PAYLOAD_SIZE, len(data))
        chunk = data[start:end]
        
        # Metadaten für das Paket: CHUNK:<Index>/<Total>
        metadata = f"CHUNK:{i}/{total_chunks}:".encode('utf-8')
        packet = metadata + chunk
        
        # Senden über UART an das LoRa HAT
        lora_serial.write(packet)
        print(f"-> Gesendet: Paket {i+1} von {total_chunks} ({len(packet)} Bytes)")
        
        # WICHTIG: LoRa benötigt eine Wartezeit zwischen den Paketen (Duty Cycle)
        time.sleep(2) 

    # Abschlussmeldung senden
    lora_serial.write(b"ENDE_BILDUPLOAD")
    print("Senden abgeschlossen.")


def main():
    # 1. Kamera initialisieren und Foto aufnehmen
    picam2 = Picamera2()
    camera_config = picam2.create_still_configuration()
    picam2.configure(camera_config)
    picam2.start()
    time.sleep(2)
    
    # Temporärer Dateiname
    temp_filename = "/tmp/lora_temp_foto.jpg"
    picam2.capture_file(temp_filename)
    print(f"Foto aufgenommen und temporär gespeichert: {temp_filename}")
    picam2.stop()
    
    # 2. Bild komprimieren und als Byte-Array laden
    image_bytes = compress_and_get_bytes(temp_filename)
    
    if image_bytes is None:
        return
        
    # 3. LoRa-Schnittstelle initialisieren
    lora_serial = setup_lora_serial()
    
    if lora_serial:
        # 4. Daten paketieren und senden
        send_data_via_lora(lora_serial, image_bytes)
        lora_serial.close()
    
    # Aufräumen (optional)
    # import os
    # os.remove(temp_filename)

if __name__ == "__main__":
    main()
