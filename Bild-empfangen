import serial
import time
from PIL import Image

# 1. UART-Konfiguration (muss mit dem Sender übereinstimmen)
lora_serial = serial.Serial(
    port='/dev/ttyS0', 
    baudrate=9600,
    timeout=1
)

# Speichern der empfangenen Bild-Chunks
received_chunks = {}
total_chunks = None
image_size_expected = 0 # Erwartete Größe des fertigen Bildes

print("Warte auf Bildpakete...")

while True:
    try:
        if lora_serial.in_waiting > 0:
            # LoRa-Daten lesen
            received_packet = lora_serial.readline().strip()
            
            if received_packet:
                # 2. Paket aufteilen und Metadaten extrahieren
                # Suchen Sie nach dem Trennzeichen für die Metadaten
                if b"CHUNK:" in received_packet:
                    meta_data_part, data_chunk = received_packet.split(b":", 3)[2:]
                    
                    # Metadaten parsen (z.B. "i/total_chunks")
                    try:
                        index, total = map(int, meta_data_part.split(b'/'))
                        
                        received_chunks[index] = data_chunk
                        total_chunks = total
                        
                        print(f"Empfangen: Paket {index + 1} von {total_chunks}")
                        
                    except ValueError:
                        print(f"Fehler beim Parsen der Metadaten: {meta_data_part.decode()}")
                
                # 3. Prüfen, ob alle Pakete empfangen wurden
                if total_chunks is not None and len(received_chunks) == total_chunks:
                    print("Alle Pakete empfangen. Setze Bild zusammen...")
                    
                    # 4. Bild zusammensetzen
                    sorted_chunks = [received_chunks[i] for i in range(total_chunks)]
                    full_image_data = b"".join(sorted_chunks)
                    
                    # 5. Bild speichern oder anzeigen
                    # Abhängig von der Bildkodierung (z.B. JPEG, PNG, Raw-Pixel)
                    with open("received_image.jpg", "wb") as f:
                        f.write(full_image_data)
                    print("Bild erfolgreich als received_image.jpg gespeichert!")
                    
                    # Beenden, wenn Bild fertig ist
                    break
        
        time.sleep(0.1)

    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")
        break

lora_serial.close()
