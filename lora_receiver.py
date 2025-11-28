import serial
import time
from PIL import Image

# UART-Konfiguration (muss mit dem Sender übereinstimmen)
lora_serial = serial.Serial(
    port='/dev/ttyS0', 
    baudrate=9600,
    timeout=1
)

# Speichern der empfangenen Bild-Chunks
received_chunks = {}
total_chunks = None
image_size_expected = 0

print("Warte auf Bildpakete...")

while True:
    try:
        if lora_serial.in_waiting > 0:
            # LoRa-Daten lesen
            received_packet = lora_serial.readline().strip()
            
            if received_packet:
                print(f"Rohpaket empfangen: {received_packet[:50]}...")  # Debug-Ausgabe
                
                # START-Nachricht verarbeiten
                if received_packet.startswith(b"START:"):
                    try:
                        parts = received_packet.split(b":")
                        image_size_expected = int(parts[1])
                        total_chunks = int(parts[2])
                        print(f"START empfangen: Erwarte {total_chunks} Pakete mit insgesamt {image_size_expected} Bytes")
                        received_chunks = {}  # Zurücksetzen für neues Bild
                    except (IndexError, ValueError) as e:
                        print(f"Fehler beim Parsen der START-Nachricht: {e}")
                
                # CHUNK-Nachricht verarbeiten
                elif b"CHUNK:" in received_packet:
                    try:
                        # Paket aufteilen: CHUNK:i/total:DATEN
                        # Finde die Position des zweiten Doppelpunkts
                        first_colon = received_packet.find(b":")
                        second_colon = received_packet.find(b":", first_colon + 1)
                        
                        if first_colon != -1 and second_colon != -1:
                            # Extrahiere Metadaten zwischen den beiden Doppelpunkten
                            meta_data = received_packet[first_colon + 1:second_colon]
                            # Extrahiere die eigentlichen Daten nach dem zweiten Doppelpunkt
                            data_chunk = received_packet[second_colon + 1:]
                            
                            # Parse Index und Total
                            index, total = map(int, meta_data.split(b'/'))
                            
                            received_chunks[index] = data_chunk
                            total_chunks = total
                            
                            print(f"✓ Empfangen: Paket {index + 1} von {total_chunks} ({len(data_chunk)} Bytes)")
                        else:
                            print("Fehler: Konnte Doppelpunkte nicht finden")
                            
                    except (ValueError, IndexError) as e:
                        print(f"Fehler beim Parsen des CHUNK-Pakets: {e}")
                
                # ENDE-Nachricht verarbeiten
                elif received_packet.startswith(b"ENDE_BILDUPLOAD"):
                    print("ENDE-Nachricht empfangen")
                    
                    # Prüfen, ob alle Pakete empfangen wurden
                    if total_chunks is not None and len(received_chunks) == total_chunks:
                        print("Alle Pakete empfangen. Setze Bild zusammen...")
                        
                        # Bild zusammensetzen
                        sorted_chunks = [received_chunks[i] for i in range(total_chunks)]
                        full_image_data = b"".join(sorted_chunks)
                        
                        print(f"Zusammengesetzt: {len(full_image_data)} Bytes (erwartet: {image_size_expected})")
                        
                        # Bild speichern
                        with open("received_image.jpg", "wb") as f:
                            f.write(full_image_data)
                        print("✓ Bild erfolgreich als received_image.jpg gespeichert!")
                        
                        # Optional: Bild anzeigen
                        try:
                            img = Image.open("received_image.jpg")
                            print(f"Bildgröße: {img.size}")
                            # img.show()  # Auskommentieren, wenn X11 verfügbar
                        except Exception as e:
                            print(f"Hinweis: Bild gespeichert, aber konnte nicht geladen werden: {e}")
                        
                        # Zurücksetzen für nächstes Bild
                        received_chunks = {}
                        total_chunks = None
                        image_size_expected = 0
                    else:
                        print(f"WARNUNG: Nur {len(received_chunks)} von {total_chunks} Paketen empfangen!")
        
        time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nProgramm beendet durch Benutzer")
        break
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")
        import traceback
        traceback.print_exc()

lora_serial.close()
print("Serielle Verbindung geschlossen")
