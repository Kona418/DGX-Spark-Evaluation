import cv2
import os
from pathlib import Path

def generate_thumbnails(video_folder):
    # Pfade definieren
    base_path = Path(video_folder)
    thumb_path = base_path / "thumbnails"
    
    # Erstelle den Ordner, falls er nicht existiert
    thumb_path.mkdir(exist_ok=True)
    
    # Unterstützte Videoformate
    video_extensions = [".mp4", ".avi", ".mov", ".mkv", ".webm"]
    
    video_files = [f for f in base_path.iterdir() if f.suffix.lower() in video_extensions]
    
    if not video_files:
        print(f"Keine Videos in {base_path} gefunden.")
        return

    print(f"Starte Generierung von {len(video_files)} Thumbnails...")

    for video_file in video_files:
        # Video laden
        cap = cv2.VideoCapture(str(video_file))
        
        # Ersten Frame lesen (oder Frame bei Sekunde 1)
        # cap.set(cv2.CAP_PROP_POS_MSEC, 1000) # Optional: 1 Sekunde Vorsprung
        success, frame = cap.read()
        
        if success:
            # Dateiname für Thumbnail (gleicher Name, Endung .png)
            thumb_name = video_file.stem + ".png"
            target_file = thumb_path / thumb_name
            
            # Speichern
            cv2.imwrite(str(target_file), frame)
            print(f"Erstellt: {thumb_name}")
        else:
            print(f"Fehler bei: {video_file.name}")
            
        cap.release()

    print("\nFertig! Die Thumbnails liegen im Unterordner 'thumbnails'.")

# Hier den Pfad zu deinem Video-Ordner anpassen
generate_thumbnails("../LTX_1sek/output")
generate_thumbnails("../LTX_10sek/output")
generate_thumbnails("../LTX_15sek/output")
generate_thumbnails("../SVD/output")