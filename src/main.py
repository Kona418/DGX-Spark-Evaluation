import streamlit as st
import os
import pandas as pd
import cv2
import torch
import pytesseract
import librosa
import re
from PIL import Image
from jiwer import cer
from skimage.metrics import structural_similarity as ssim
from transformers import CLIPProcessor, CLIPModel, ClapModel, ClapProcessor
from concurrent.futures import ThreadPoolExecutor
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
from moviepy import VideoFileClip

IMAGE_PROMPTS = [
    {"visual_prompt": "A glowing neon sign in a dark rainy alleyway that clearly spells 'SPARK-2026' in bright pink letters.", "ocr_ref": "SPARK-2026"},
    {"visual_prompt": "A small red apple resting on top of a stack of three books: a blue book at the bottom, a green book in the middle, and a yellow book at the top.", "ocr_ref": ""},
    {"visual_prompt": "Extreme macro photography of a chameleon's eye, showing the intricate hexagonal scale patterns and vivid green and orange colors.", "ocr_ref": ""},
    {"visual_prompt": "A transparent crystal skull sitting on a mirror table, illuminated by a single harsh spotlight from the right, creating complex caustics and refractions.", "ocr_ref": ""},
    {"visual_prompt": "An isometric view of a futuristic highly dense cyberpunk city with hundreds of flying cars, glowing skyscrapers, and intricate cable networks.", "ocr_ref": ""}
]

VIDEO_PROMPTS = [
    {"visual_prompt": "A slow-motion shot of a massive ocean wave crashing against a jagged dark cliff, sending bright white sea spray high into the air.", "audio_prompt": ""},
    {"visual_prompt": "A smooth drone tracking shot flying low over a lush green forest canopy towards a towering snow-capped mountain peak at sunset.", "audio_prompt": ""},
    {"visual_prompt": "A shiny silver metallic sphere rolling perfectly straight along a checkered black and white floor under dim industrial lights.", "audio_prompt": ""},
    {"visual_prompt": "A close-up of an intricate brass pocket watch mechanism, with dozens of tiny gears interlocking and continuously rotating.", "audio_prompt": ""},
    {"visual_prompt": "A dark room where a single glowing orb floats slowly from left to right, casting moving shadows behind a stationary marble bust.", "audio_prompt": ""}
]

AUDIO_PROMPTS = [
    {"visual_prompt": "A high-energy rock band playing on a neon-lit stage. The lead singer passionately sings into a vintage microphone while the guitarist shreds a solo. Quick camera cuts between the singer and the guitarist.", "audio_prompt": "Fast-paced electric guitar riff accompanied by heavy drum beats and a powerful, melodic male rock vocal singing \"We ignite the night\"."},
    {"visual_prompt": "Two people sitting in a modern, soundproofed studio with professional microphones and warm lighting. The woman on the left gestures with her hands while speaking, and the man on the right nods thoughtfully, taking a sip from a coffee mug.", "audio_prompt": "Clear, close-mic studio audio. A female voice says, \"The fascinating thing about this technology is how it scales,\" followed by a male voice responding, \"Exactly, and the hardware limits are being pushed every day.\""},
    {"visual_prompt": "Two sci-fi warriors engaged in a fast-paced duel using glowing energy swords in a dark, metallic corridor. Sparks fly as a red energy blade clashes with a blue energy blade. The warrior with the blue sword pushes the other back.", "audio_prompt": "Loud humming and crackling sounds of energy blades clashing. A deep male voice shouts, \"You cannot win this battle!\", followed by the loud sizzle of the swords locking together."},
    {"visual_prompt": "A cheerful chef in a white uniform standing in a bright, rustic kitchen. He vigorously chops fresh vegetables on a wooden cutting board, then scrapes them into a steaming pan on the stove, creating a burst of steam.", "audio_prompt": "The rapid chopping sound of a knife on wood, followed by a loud sizzling sound. A male voice speaks clearly, saying, \"Now we add the fresh peppers to get that perfect sizzle.\""},
    {"visual_prompt": "A fast panning shot of two formula racing cars speeding down a sunlit asphalt straightaway. The leading red car sharply takes a corner, kicking up a small cloud of tire smoke, while the second silver car attempts to overtake on the inside.", "audio_prompt": "The extremely loud, high-pitched whining roar of high-speed racing engines passing by. An excited, fast-speaking male sports commentator yells, \"He is going for the inside line, what a spectacular overtaking maneuver!\""}
]

def get_prompt_config(filename, is_video, is_audio_mode):
    match = re.search(r'_(\d{2})\.\w+$', filename)
    if not match:
        return {"visual_prompt": "", "audio_prompt": "", "ocr_ref": ""}
    
    num = int(match.group(1))
    idx = (num - 1) // 5 
    
    if not is_video:
        if 0 <= idx < len(IMAGE_PROMPTS):
            return {"visual_prompt": IMAGE_PROMPTS[idx]["visual_prompt"], "audio_prompt": "", "ocr_ref": IMAGE_PROMPTS[idx]["ocr_ref"]}
    else:
        if is_audio_mode:
            if 0 <= idx < len(AUDIO_PROMPTS):
                return {"visual_prompt": AUDIO_PROMPTS[idx]["visual_prompt"], "audio_prompt": AUDIO_PROMPTS[idx]["audio_prompt"], "ocr_ref": ""}
        else:
            if 0 <= idx < len(VIDEO_PROMPTS):
                return {"visual_prompt": VIDEO_PROMPTS[idx]["visual_prompt"], "audio_prompt": "", "ocr_ref": ""}
                
    return {"visual_prompt": "", "audio_prompt": "", "ocr_ref": ""}

@st.cache_resource
def load_models():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32", torch_dtype=torch.float32).to(device)
    clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    
    clap_model = ClapModel.from_pretrained("laion/clap-htsat-unfused").to(device)
    clap_processor = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
    
    return clip_model, clip_processor, clap_model, clap_processor, device

clip_model, clip_processor, clap_model, clap_processor, device = load_models()

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
        inputs = clip_processor(text=[prompt], images=image, return_tensors="pt", truncation=True, max_length=77).to(device)
        with torch.no_grad():
            return clip_model(**inputs).logits_per_image.item()
    except Exception as e:
        print(f"Fehler bei Bild-CLIP: {e}")
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
            inputs = clip_processor(text=[prompt], images=pil_image, return_tensors="pt", truncation=True, max_length=77).to(device)
            with torch.no_grad():
                scores.append(clip_model(**inputs).logits_per_image.item())
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
        inputs = clap_processor(audio=audio_sample, text=prompt, return_tensors="pt", padding=True, sampling_rate=48000).to(device)
        with torch.no_grad():
            outputs = clap_model(**inputs)
        return outputs.logits_per_audio[0][0].item()
    except Exception as e:
        print(f"Fehler bei CLAP: {e}")
        return None

def calc_ocr_cer(image_path, ref_text):
    if not ref_text: return None
    try:
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        inverted = cv2.bitwise_not(gray)
        ext_text = pytesseract.image_to_string(inverted).strip()
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

folder_path = st.text_input("Ordnerpfad:", value="./media")
is_audio_mode = st.checkbox("Audio-Auswertung (Video mit Ton) aktivieren")

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
        file_name = os.path.basename(current_file)
        is_video = current_file.lower().endswith('.mp4')
        has_audio, audio_path = check_and_extract_audio(current_file) if is_video else (False, None)
        
        cfg = get_prompt_config(file_name, is_video, is_audio_mode)
        
        st.progress((idx) / total)
        st.write(f"Datei {idx+1} von {total}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(file_name)
            if is_video:
                st.video(current_file)
            else:
                st.image(current_file, width=600)
        
        with col2:
            prompt_val = st.text_area("Visueller Prompt (CLIP)", value=cfg["visual_prompt"], key=f"prompt_{idx}")
            
            if prompt_val:
                token_count = len(clip_processor.tokenizer(prompt_val)["input_ids"])
                if token_count > 77:
                    st.warning(f"Warnung: Der Prompt hat {token_count} Tokens. Das Limit von 77 ist überschritten. Der Text wird bei der Berechnung abgeschnitten.")
            
            if has_audio or is_audio_mode:
                audio_prompt_val = st.text_area("Audio Prompt (CLAP)", value=cfg["audio_prompt"], key=f"aprompt_{idx}")
            else:
                audio_prompt_val = ""
                
            if not is_video:
                ref_val = st.text_input("Referenztext (OCR)", value=cfg["ocr_ref"], key=f"ref_{idx}")
            else:
                ref_val = ""
            
            st.write("Subjektive Bewertung (1 = mangelhaft, 5 = exzellent)")
            col_a, col_b = st.columns(2)
            with col_a:
                logic_score = st.radio("Logik", [1,2,3,4,5], index=2, horizontal=True, key=f"log_{idx}")
                prompt_treue = st.radio("Prompt-Treue", [1,2,3,4,5], index=2, horizontal=True, key=f"pt_{idx}")
                if has_audio or is_audio_mode:
                    sync_score = st.radio("AV-Synchronität", [1,2,3,4,5], index=2, horizontal=True, key=f"sync_{idx}")
            with col_b:
                artifact_score = st.radio("Artefakte", [1,2,3,4,5], index=2, horizontal=True, key=f"art_{idx}")
                aesthetic_score = st.radio("Ästhetik", [1,2,3,4,5], index=2, horizontal=True, key=f"aes_{idx}")
                if has_audio or is_audio_mode:
                    audio_qual_score = st.radio("Audioqualität", [1,2,3,4,5], index=2, horizontal=True, key=f"aqual_{idx}")
        
        col_prev, col_skip, col_next = st.columns([1,1,2])
        
        if col_prev.button("Zurück"):
            st.session_state.current_idx = max(0, st.session_state.current_idx - 1)
            st.rerun()
        if col_skip.button("Überspringen"):
            st.session_state.current_idx += 1
            st.rerun()
            
        if col_next.button("Speichern & Nächste", type="primary"):
            ctx = get_script_run_ctx()
            
            def run_in_thread(func, *args):
                add_script_run_ctx(ctx=ctx)
                return func(*args)

            with st.spinner("Berechne Metriken..."):
                with ThreadPoolExecutor(max_workers=3) as executor:
                    if is_video:
                        future_clip = executor.submit(run_in_thread, calc_clip_video, current_file, prompt_val)
                        future_ssim = executor.submit(run_in_thread, calc_video_ssim, current_file)
                        future_clap = executor.submit(run_in_thread, calc_clap_audio, audio_path, audio_prompt_val) if has_audio else executor.submit(lambda: None)
                        future_cer = executor.submit(lambda: None)
                    else:
                        future_clip = executor.submit(run_in_thread, calc_clip_image, current_file, prompt_val)
                        future_ssim = executor.submit(lambda: None)
                        future_clap = executor.submit(lambda: None)
                        future_cer = executor.submit(run_in_thread, calc_ocr_cer, current_file, ref_val)
                    
                    clip_res = future_clip.result()
                    ssim_res = future_ssim.result()
                    clap_res = future_clap.result()
                    cer_res = future_cer.result()
                
                if has_audio and audio_path and os.path.exists(audio_path):
                    os.remove(audio_path)
                
                df = pd.DataFrame([{
                    "Dateiname": file_name,
                    "Medium": "Video" if is_video else "Bild",
                    "CLIP_Score": clip_res,
                    "CLAP_Score": clap_res,
                    "SSIM": ssim_res,
                    "CER": cer_res,
                    "Logik_Rating": logic_score,
                    "Artefakte_Rating": artifact_score,
                    "Prompt_Treue_Rating": prompt_treue,
                    "Aesthetik_Rating": aesthetic_score,
                    "AV_Sync_Rating": sync_score if (has_audio or is_audio_mode) else None,
                    "Audioqualitaet_Rating": audio_qual_score if (has_audio or is_audio_mode) else None
                }])
                
                csv_path = os.path.join(st.session_state.folder_path, "evaluation_results.csv")
                df.to_csv(csv_path, mode='a', header=not os.path.exists(csv_path), index=False)
            
            st.session_state.current_idx += 1
            st.rerun()