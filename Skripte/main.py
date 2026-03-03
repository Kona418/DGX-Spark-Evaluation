import streamlit as st
import os
import pandas as pd
import cv2
import torch
import pytesseract
import librosa
from PIL import Image
from jiwer import cer
from skimage.metrics import structural_similarity as ssim
from transformers import AutoModel, ClapModel, ClapProcessor
import torch.nn.functional as F
from concurrent.futures import ThreadPoolExecutor
from streamlit.runtime.scriptrunner import add_script_run_ctx
from moviepy.editor import VideoFileClip

@st.cache_resource
def load_models():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    jina_model = AutoModel.from_pretrained("jinaai/jina-clip-v1", trust_remote_code=True, torch_dtype=torch.float32).to(device)
    
    clap_model = ClapModel.from_pretrained("laion/clap-htsat-unfused").to(device)
    clap_processor = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
    
    return jina_model, clap_model, clap_processor, device

jina_model, clap_model, clap_processor, device = load_models()

def check_and_extract_audio(video_path):
    try:
        clip = VideoFileClip(video_path)
        if clip.audio is not None:
            audio_path = video_path.replace('.mp4', '_temp.wav')
            clip.audio.write_audiofile(audio_path, logger=None)
            clip.close()
            return True, audio_path
        clip.close()
        return False, None
    except:
        return False, None

@st.cache_data
def calc_clip_image(image_path, prompt):
    if not prompt: return None
    try:
        image = Image.open(image_path).convert("RGB")
        text_features = jina_model.encode_text([prompt])
        image_features = jina_model.encode_image([image])
        return F.cosine_similarity(text_features, image_features).item()
    except Exception as e:
        print(f"Fehler bei Bild-CLIP: {e}")
        return None

@st.cache_data(ttl=3600)
def calc_clip_video(video_path, prompt):
    if not prompt: return 0.0
    try:
        text_features = jina_model.encode_text([prompt])
        cap = cv2.VideoCapture(video_path)
        scores = []
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            small_frame = cv2.resize(frame, (224, 224))
            pil_image = Image.fromarray(cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB))
            image_features = jina_model.encode_image([pil_image])
            scores.append(F.cosine_similarity(text_features, image_features).item())
        cap.release()
        return sum(scores) / len(scores) if scores else 0.0
    except Exception as e:
        print(f"Fehler bei Video-CLIP: {e}")
        return None

@st.cache_data
def calc_clap_audio(audio_path, prompt):
    if not audio_path or not prompt: return None
    try:
        audio_sample, sr = librosa.load(audio_path, sr=48000)
        inputs = clap_processor(audios=audio_sample, text=prompt, return_tensors="pt", padding=True, sampling_rate=48000).to(device)
        with torch.no_grad():
            outputs = clap_model(**inputs)
        return outputs.logits_per_audio[0][0].item()
    except Exception as e:
        print(f"Fehler bei CLAP: {e}")
        return None

def calc_ocr_cer(image_path, ref_text):
    if not ref_text: return None
    try:
        ext_text = pytesseract.image_to_string(Image.open(image_path)).strip()
        return cer(ref_text.lower(), ext_text.lower()) if ext_text else 1.0
    except Exception as e:
        print(f"Fehler bei OCR: {e}")
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
        print(f"Fehler bei SSIM: {e}")
        return None

st.set_page_config(layout="wide")

if 'file_list' not in st.session_state: st.session_state.file_list = []
if 'current_idx' not in st.session_state: st.session_state.current_idx = 0
if 'folder_path' not in st.session_state: st.session_state.folder_path = ""
if 'prompt_default' not in st.session_state: st.session_state.prompt_default = ""
if 'audio_prompt_default' not in st.session_state: st.session_state.audio_prompt_default = ""
if 'ref_default' not in st.session_state: st.session_state.ref_default = ""

folder_path = st.text_input("Ordnerpfad:", value="./media")

if st.button("Ordner laden", type="primary"):
    if os.path.exists(folder_path):
        files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) 
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.mp4'))]
        st.session_state.file_list = sorted(files)
        st.session_state.current_idx = 0
        st.session_state.folder_path = folder_path
        st.rerun()

if st.session_state.file_list:
    idx = st.session_state.current_idx
    total = len(st.session_state.file_list)
    
    if idx >= total:
        st.success("Alle Dateien bewertet.")
    else:
        current_file = st.session_state.file_list[idx]
        is_video = current_file.lower().endswith('.mp4')
        has_audio, audio_path = check_and_extract_audio(current_file) if is_video else (False, None)
        
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
            prompt_val = st.text_area("Visueller Prompt (CLIP)", value=st.session_state.prompt_default, key=f"prompt_{idx}")
            
            if has_audio:
                audio_prompt_val = text_area("Audio Prompt (CLAP)", value=st.session_state.audio_prompt_default, key=f"aprompt_{idx}")
            else:
                audio_prompt_val = ""
                
            if not is_video:
                ref_val = st.text_input("Referenztext (OCR)", value=st.session_state.ref_default, key=f"ref_{idx}")
            else:
                ref_val = ""
            
            col_a, col_b = st.columns(2)
            with col_a:
                logic_score = st.radio("Logik (1-5)", [1,2,3,4,5], index=2, horizontal=True, key=f"log_{idx}")
                prompt_treue = st.radio("Prompt-Treue (1-5)", [1,2,3,4,5], index=2, horizontal=True, key=f"pt_{idx}")
                if has_audio:
                    sync_score = st.radio("AV-Synchronität (1-5)", [1,2,3,4,5], index=2, horizontal=True, key=f"sync_{idx}")
            with col_b:
                artifact_score = st.radio("Artefakte (1-5)", [1,2,3,4,5], index=2, horizontal=True, key=f"art_{idx}")
                aesthetic_score = st.radio("Ästhetik (1-5)", [1,2,3,4,5], index=2, horizontal=True, key=f"aes_{idx}")
                if has_audio:
                    audio_qual_score = st.radio("Audioqualität (1-5)", [1,2,3,4,5], index=2, horizontal=True, key=f"aqual_{idx}")
        
        col_prev, col_skip, col_next = st.columns([1,1,2])
        
        if col_prev.button("Zurück"):
            st.session_state.current_idx = max(0, st.session_state.current_idx - 1)
            st.rerun()
        if col_skip.button("Überspringen"):
            st.session_state.current_idx += 1
            st.rerun()
            
        if col_next.button("Speichern & Nächste", type="primary"):
            st.session_state.prompt_default = prompt_val
            st.session_state.audio_prompt_default = audio_prompt_val
            st.session_state.ref_default = ref_val
            
            with st.spinner("Berechne Metriken..."):
                with ThreadPoolExecutor(max_workers=3) as executor:
                    if is_video:
                        future_clip = executor.submit(calc_clip_video, current_file, prompt_val)
                        future_ssim = executor.submit(calc_video_ssim, current_file)
                        future_clap = executor.submit(calc_clap_audio, audio_path, audio_prompt_val) if has_audio else executor.submit(lambda: None)
                        future_cer = executor.submit(lambda: None)
                    else:
                        future_clip = executor.submit(calc_clip_image, current_file, prompt_val)
                        future_ssim = executor.submit(lambda: None)
                        future_clap = executor.submit(lambda: None)
                        future_cer = executor.submit(calc_ocr_cer, current_file, ref_val)
                    
                    for t in executor._threads: add_script_run_ctx(t)

                    clip_res = future_clip.result()
                    ssim_res = future_ssim.result()
                    clap_res = future_clap.result()
                    cer_res = future_cer.result()
                
                if has_audio and os.path.exists(audio_path):
                    os.remove(audio_path)
                
                df = pd.DataFrame([{
                    "Dateiname": os.path.basename(current_file),
                    "Medium": "Video" if is_video else "Bild",
                    "CLIP_Score": clip_res,
                    "CLAP_Score": clap_res,
                    "SSIM": ssim_res,
                    "CER": cer_res,
                    "Logik_Rating": logic_score,
                    "Artefakte_Rating": artifact_score,
                    "Prompt_Treue_Rating": prompt_treue,
                    "Aesthetik_Rating": aesthetic_score,
                    "AV_Sync_Rating": sync_score if has_audio else None,
                    "Audioqualitaet_Rating": audio_qual_score if has_audio else None
                }])
                
                csv_path = os.path.join(st.session_state.folder_path, "evaluation_results.csv")
                df.to_csv(csv_path, mode='a', header=not os.path.exists(csv_path), index=False)
            
            st.session_state.current_idx += 1
            st.rerun()