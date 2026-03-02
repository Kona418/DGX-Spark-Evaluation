import streamlit as st
import os
import pandas as pd
import cv2
import torch
import pytesseract
from PIL import Image
from jiwer import cer
from skimage.metrics import structural_similarity as ssim
from transformers import CLIPProcessor, CLIPModel

@st.cache_resource
def load_models():
    torch.set_num_threads(4)
    device = "cpu"
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32", torch_dtype=torch.float32)
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    return model, processor, device

clip_model, clip_processor, device = load_models()

@st.cache_data
def calc_clip_image(image_path, prompt):
    if not prompt: return None
    try:
        image = Image.open(image_path).convert("RGB").resize((224, 224))
        inputs = clip_processor(text=[prompt], images=image, return_tensors="pt").to(device)
        with torch.no_grad():
            return clip_model(**inputs).logits_per_image.item()
    except Exception as e:
        st.error(f"Systemfehler bei Bild-CLIP: {e}")
        return None

@st.cache_data(ttl=3600)
def calc_clip_video(video_path, prompt):
    if not prompt: return 0.0
    try:
        cap = cv2.VideoCapture(video_path)
        scores = []
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            
            small_frame = cv2.resize(frame, (224, 224))
            pil_image = Image.fromarray(cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB))
            inputs = clip_processor(text=[prompt], images=pil_image, return_tensors="pt").to(device)
            with torch.no_grad():
                scores.append(clip_model(**inputs).logits_per_image.item())
                
        cap.release()
        return sum(scores) / len(scores) if scores else 0.0
    except Exception as e:
        st.error(f"Systemfehler bei Video-CLIP: {e}")
        return None

def calc_ocr_cer(image_path, ref_text):
    if not ref_text: return None
    try:
        ext_text = pytesseract.image_to_string(Image.open(image_path)).strip()
        return cer(ref_text.lower(), ext_text.lower()) if ext_text else 1.0
    except Exception as e:
        st.error(f"Systemfehler bei OCR: {e}")
        return None

def calc_video_ssim(video_path):
    try:
        cap = cv2.VideoCapture(video_path)
        ret, prev = cap.read()
        if not ret: return None
        prev_gray = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
        scores = []
        while True:
            ret, curr = cap.read()
            if not ret: break
            curr_gray = cv2.cvtColor(curr, cv2.COLOR_BGR2GRAY)
            scores.append(ssim(prev_gray, curr_gray, data_range=curr_gray.max() - curr_gray.min()))
            prev_gray = curr_gray
        cap.release()
        return sum(scores) / len(scores) if scores else 0.0
    except Exception as e:
        st.error(f"Systemfehler bei SSIM: {e}")
        return None

st.set_page_config(layout="wide", page_title="Medien-Evaluation")

if 'file_list' not in st.session_state:
    st.session_state.file_list = []
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0
if 'folder_path' not in st.session_state:
    st.session_state.folder_path = ""
if 'last_prompt' not in st.session_state:
    st.session_state.last_prompt = ""
if 'last_ref_text' not in st.session_state:
    st.session_state.last_ref_text = ""
if 'last_logic' not in st.session_state:
    st.session_state.last_logic = 3
if 'last_artifacts' not in st.session_state:
    st.session_state.last_artifacts = 3
if 'last_prompt_treue' not in st.session_state:
    st.session_state.last_prompt_treue = 3
if 'last_aesthetic' not in st.session_state:
    st.session_state.last_aesthetic = 3

folder_path = st.text_input("Ordnerpfad:", value="./media")

def load_folder():
    if os.path.exists(folder_path):
        files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) 
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.mp4'))]
        st.session_state.file_list = sorted(files)
        st.session_state.current_idx = 0
        st.session_state.folder_path = folder_path
    else:
        st.error("Pfad nicht gefunden!")

if st.button("Ordner laden", type="primary", on_click=load_folder):
    pass

with st.expander("Interpretation der Scores und Metriken"):
    st.markdown("""
    **Objektive Metriken (automatisch berechnet):**
    * **CLIP-Score:** Misst die semantische Ähnlichkeit zwischen Text und Bild. Höher ist besser (typischerweise zwischen 20 und 40 bei diesem Modell).
    * **SSIM (nur Video):** Misst die strukturelle Ähnlichkeit aufeinanderfolgender Frames. Skala 0 bis 1. Ein Wert nahe 1 bedeutet hohe Stabilität (wenig Flimmern/Rauschen), exakt 1.0 bedeutet jedoch ein eingefrorenes Standbild ohne Bewegung.
    * **CER (nur Bild/OCR):** Character Error Rate. Skala 0 bis 1. Niedriger ist besser (0.0 = fehlerfrei, 1.0 = kompletter Buchstabensalat oder nichts erkannt).
    
    **Subjektive Metriken (manuelle Skala 1 bis 5, 5 ist immer das Beste):**
    * **Logik:** 1 = völlig absurd/physikalisch unmöglich, 5 = absolut schlüssig.
    * **Artefakte:** 1 = stark verpixelt/massive Glitches/verschmolzene Gliedmaßen, 5 = makellos/Fotoqualität.
    * **Prompt-Treue:** 1 = Thema komplett verfehlt, 5 = jedes geforderte Detail präzise abgebildet.
    * **Ästhetik:** 1 = amateurhaft/schlechte Komposition, 5 = cineastisch/hochprofessionell.
    """)

if st.session_state.file_list:
    idx = st.session_state.current_idx
    total = len(st.session_state.file_list)
    
    if idx >= total:
        st.success("Alle Dateien bewertet!")
    else:
        current_file = st.session_state.file_list[idx]
        is_video = current_file.lower().endswith('.mp4')
        
        st.progress((idx) / total)
        st.write(f"Datei {idx+1} von {total}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(os.path.basename(current_file))
            if is_video:
                st.video(current_file)
            else:
                st.image(current_file, width=600)
        
        with col2:
            prompt = st.text_area("CLIP Prompt", value=st.session_state.last_prompt)
            ref_text = st.text_input("Referenztext (OCR)", value=st.session_state.last_ref_text) if not is_video else ""
            
            st.write("Subjektive Bewertung (1 = mangelhaft, 5 = exzellent)")
            col_a, col_b = st.columns(2)
            with col_a:
                logic_score = st.radio("Logik", [1,2,3,4,5], index=st.session_state.last_logic-1, horizontal=True)
                prompt_treue = st.radio("Prompt-Treue", [1,2,3,4,5], index=st.session_state.last_prompt_treue-1, horizontal=True)
            with col_b:
                artifact_score = st.radio("Artefakte", [1,2,3,4,5], index=st.session_state.last_artifacts-1, horizontal=True)
                aesthetic_score = st.radio("Ästhetik", [1,2,3,4,5], index=st.session_state.last_aesthetic-1, horizontal=True)
        
        def save_and_next():
            st.session_state.last_prompt = prompt
            st.session_state.last_ref_text = ref_text
            st.session_state.last_logic = logic_score
            st.session_state.last_artifacts = artifact_score
            st.session_state.last_prompt_treue = prompt_treue
            st.session_state.last_aesthetic = aesthetic_score
            
            with st.spinner("Berechne Metriken..."):
                clip_val = calc_clip_video(current_file, prompt) if is_video else calc_clip_image(current_file, prompt)
                ssim_val = calc_video_ssim(current_file) if is_video else None
                cer_val = calc_ocr_cer(current_file, ref_text) if not is_video else None
                
                df = pd.DataFrame([{
                    "Dateiname": os.path.basename(current_file),
                    "Medium": "Video" if is_video else "Bild",
                    "CLIP_Score": clip_val,
                    "SSIM": ssim_val,
                    "CER": cer_val,
                    "Logik_Rating": logic_score,
                    "Artefakte_Rating": artifact_score,
                    "Prompt_Treue_Rating": prompt_treue,
                    "Aesthetik_Rating": aesthetic_score
                }])
                
                csv_path = os.path.join(st.session_state.folder_path, "evaluation_results.csv")
                df.to_csv(csv_path, mode='a', header=not os.path.exists(csv_path), index=False)
            
            st.session_state.current_idx += 1
        
        col_prev, col_skip, col_next = st.columns([1,1,2])
        if col_prev.button("Zurück"):
            st.session_state.current_idx = max(0, st.session_state.current_idx - 1)
            st.rerun()
        if col_skip.button("Überspringen"):
            st.session_state.current_idx += 1
            st.rerun()
        if col_next.button("Speichern & Nächste", type="primary"):
            save_and_next()
            st.rerun()