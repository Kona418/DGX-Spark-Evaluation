```markdown
# DGX Spark Model Evaluation

Dieses Repository enthält alle Skripte, generierten Medien, ComfyUI-Workflows und Ergebnisse einer Seminararbeit zur Evaluierung generativer KI-Modelle auf einem Nvidia DGX Spark System (GB10 SoC, 128 GB Unified Memory). Verglichen werden Bildgenerierungsmodelle (Flux.2 Dev vs. SDXL) und Videogenerierungsmodelle (LTX-2 vs. SVD).

## Ordnerstruktur

Das Projekt ist in modellspezifische Hauptordner unterteilt (`Flux2`, `SDXL`, `LTX_1sek`, `LTX_10sek`, `LTX_15sek`, `SVD`). Jeder dieser Ordner enthält:

* **`/output`**: Enthält die generierten Bild- oder Videodateien (`.png`, `.mp4`).
* **`hardware_log.csv`**: Die stündlich sekündlich geloggten Hardware-Metriken (`unified_mem_mb`, `power_w` etc.) des gesamten Durchlaufs.
* **`*_Workflow.json`**: Der spezifische ComfyUI-Workflow, um die Generierung mit fixen Seeds exakt reproduzieren zu können.
* **`evaluation_results.csv`**: Die durch das Evaluierungsskript berechneten und manuell erfassten Metriken für diesen Testdurchlauf.
* **`comfyui_run.log`**: Die Konsolenausgabe von ComfyUI während der Laufzeit, aus der die exakten Generierungszeiten (Latenz) extrahiert werden.


Zusätzlich gibt es den Ordner **`/Skripte`**, der das Streamlit-Evaluierungsskript (`main.py`) und die Abhängigkeiten (`requirements.txt`) enthält.

## Dateibenennung und Prompt-Mapping

Die generierten Dateien in den `/output`-Ordnern folgen einem festen Namensschema (z. B. `LTX2_10sek_05.mp4` oder `SDXL_12.png`). Die zweistellige Zahl am Ende des Dateinamens definiert den verwendeten Prompt. 

Das Medium `00` ist das **Priming-Medium**. Es dient ausschließlich dazu, das Modell initial in den VRAM zu laden (wie im Log erkennbar: *loaded completely; 4897.05 MB loaded*), und wird nicht quantitativ ausgewertet. Für die Testreihen wurden pro Prompt jeweils fünf Medien erzeugt:

* **00**: Priming (Vorladen des Modells)
* **01 - 05**: Prompt 1
* **06 - 10**: Prompt 2
* **11 - 15**: Prompt 3
* **16 - 20**: Prompt 4
* **21 - 25**: Prompt 5

Das Evaluierungsskript liest diese Dateiendung aus und ordnet das Medium automatisch dem korrekten Text- und Audio-Prompt für die Analyse zu.

## Prompts für die Evaluierung

### Bildgenerierung
* **Textwiedergabe (01-05):** A glowing neon sign in a dark rainy alleyway that clearly spells 'SPARK-2026' in bright pink letters.
* **Räumliche Komposition (06-10):** A small red apple resting on top of a stack of three books: a blue book at the bottom, a green book in the middle, and a yellow book at the top.
* **Feine Texturen (11-15):** Extreme macro photography of a chameleon's eye, showing the intricate hexagonal scale patterns and vivid green and orange colors.
* **Beleuchtung und Material (16-20):** A transparent crystal skull sitting on a mirror table, illuminated by a single harsh spotlight from the right, creating complex caustics and refractions.
* **Geometrische Komplexität (21-25):** An isometric view of a futuristic highly dense cyberpunk city with hundreds of flying cars, glowing skyscrapers, and intricate cable networks.

### Videogenerierung
* **Fluiddynamik (01-05):** A slow-motion shot of a massive ocean wave crashing against a jagged dark cliff, sending bright white sea spray high into the air.
* **Kamerabewegung (06-10):** A smooth drone tracking shot flying low over a lush green forest canopy towards a towering snow-capped mountain peak at sunset.
* **Objektpermanenz (11-15):** A shiny silver metallic sphere rolling perfectly straight along a checkered black and white floor under dim industrial lights.
* **Mikrobewegungen (16-20):** A close-up of an intricate brass pocket watch mechanism, with dozens of tiny gears interlocking and continuously rotating.
* **Dynamische Beleuchtung (21-25):** A dark room where a single glowing orb floats slowly from left to right, casting moving shadows behind a stationary marble bust.

### Videogenerierung mit Audio (nur für LTX-2 15sek)
* **Musikvideo (01-05):** A high-energy rock band playing on a neon-lit stage. The lead singer passionately sings into a vintage microphone while the guitarist shreds a solo. Quick camera cuts between the singer and the guitarist.
  * *Audio:* Fast-paced electric guitar riff accompanied by heavy drum beats and a powerful, melodic male rock vocal singing "We ignite the night".
* **Podcast (06-10):** Two people sitting in a modern, soundproofed studio with professional microphones and warm lighting. The woman on the left gestures with her hands while speaking, and the man on the right nods thoughtfully, taking a sip from a coffee mug.
  * *Audio:* Clear, close-mic studio audio. A female voice says, "The fascinating thing about this technology is how it scales," followed by a male voice responding, "Exactly, and the hardware limits are being pushed every day."
* **Laserschwert-Kampf (11-15):** Two sci-fi warriors engaged in a fast-paced duel using glowing energy swords in a dark, metallic corridor. Sparks fly as a red energy blade clashes with a blue energy blade. The warrior with the blue sword pushes the other back.
  * *Audio:* Loud humming and crackling sounds of energy blades clashing. A deep male voice shouts, "You cannot win this battle!", followed by the loud sizzle of the swords locking together.
* **Kochshow (16-20):** A cheerful chef in a white uniform standing in a bright, rustic kitchen. He vigorously chops fresh vegetables on a wooden cutting board, then scrapes them into a steaming pan on the stove, creating a burst of steam.
  * *Audio:* The rapid chopping sound of a knife on wood, followed by a loud sizzling sound. A male voice speaks clearly, saying, "Now we add the fresh peppers to get that perfect sizzle."
* **Formel 1 Rennen (21-25):** A fast panning shot of two formula racing cars speeding down a sunlit asphalt straightaway. The leading red car sharply takes a corner, kicking up a small cloud of tire smoke, while the second silver car attempts to overtake on the inside.
  * *Audio:* The extremely loud, high-pitched whining roar of high-speed racing engines passing by. An excited, fast-speaking male sports commentator yells, "He is going for the inside line, what a spectacular overtaking maneuver!"

## Metriken und Datengewinnung

### Hardware-Latenz (ComfyUI Logs)
Die exakten Durchlaufzeiten für die reine Inferenz (ohne den initialen Model-Load des Priming-Runs) werden direkt aus der ComfyUI-Konsolenausgabe (`Prompt executed in X.XX seconds`) extrahiert. Im Fall von SDXL liegt die Latenz (nach dem Priming von ~44s) konstant bei rund 9,75 Sekunden pro Bild.

### Hardware-Auslastung (CSV Logs)
Aus der `hardware_log.csv` werden via Peak-Analyse (Stromverbrauch > Schwellenwert) die Laufzeiten mit dem Systemverhalten abgeglichen.
* **Peak-VRAM:** Maximale Belegung des Unified Memory (z. B. ~13 GB bei SDXL).
* **Power Draw:** Maximaler und durchschnittlicher Stromverbrauch während der aktiven Denoising-Phase.

### Objektive Qualitätsmetriken (Skript)
* **CLIP-Score (Bild/Video):** Nutzt `openai/clip-vit-base-patch32`. Wandelt Text und Bild in Vektoren um und berechnet die semantische Übereinstimmung. Bei Videos wird der Durchschnitt aller Frames berechnet.
* **CLAP-Score (Audio):** Nutzt `laion/clap-htsat-unfused`. Berechnet die Cosine Similarity zwischen Textbeschreibung und extrahierter Tonspur.
* **CER (Character Error Rate):** Nutzt Tesseract OCR zur optischen Texterkennung. Misst die OCR-Fehlerquote (0.0 = fehlerfrei).
* **SSIM (Structural Similarity Index Measure):** Vergleicht Luminanz, Kontrast und Struktur direkt aufeinanderfolgender Video-Frames. Bewertet zeitliche Kohärenz.

### Subjektive Qualitätsmetriken (Skript, Skala 1-5)
* **Logik:** Physikalische und kontextuelle Plausibilität.
* **Prompt-Treue:** Visuelle Umsetzung aller spezifischen Prompt-Attribute.
* **Artefakte:** Visuelle Qualität und Fehlerfreiheit.
* **Ästhetik:** Bildkomposition, Beleuchtung und visueller Gesamteindruck.
* **AV-Synchronität:** Zeitliches Zusammenpassen von Bildereignissen und Ton (nur LTX-2 15sek).
* **Audioqualität:** Klarheit des Tons und Abwesenheit von Störgeräuschen (nur LTX-2 15sek).

## Installation und Ausführung der Evaluierung

Benötigtes Systempaket für OCR (Beispiel für Fedora Linux):
```bash
sudo dnf install tesseract
```

Python-Umgebung einrichten und Streamlit-App starten:
```bash
cd Skripte
pip install -r requirements.txt
streamlit run main.py
```

```