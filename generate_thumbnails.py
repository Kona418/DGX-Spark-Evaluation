import os
import glob
import subprocess
from pathlib import Path

# Paths to search
patterns = [
    'media/Images/DHBW_FLux2/output/*.png',
    'media/Images/Flux2/output/*.png',
    'media/Images/SVD/output/*.mp4',
    'media/Videos/DHBW_LTX2/output/*.mp4',
    'media/Videos/LTX_10sek/output/*.mp4',
    'media/Videos/LTX_15sek/output/*.mp4',
    'media/Videos/LTX_1sek/output/*.mp4',
    'media/Videos/SDXL/output/*.png'
]

def create_preview(file_path):
    # Determine the directory and the preview dir
    file_dir = os.path.dirname(file_path)
    preview_dir = os.path.join(os.path.dirname(file_dir), 'preview')
    
    if not os.path.exists(preview_dir):
        os.makedirs(preview_dir)
        
    filename = os.path.basename(file_path)
    name, ext = os.path.splitext(filename)
    
    # We output a .jpg for all previews
    out_path = os.path.join(preview_dir, name + '.jpg')
    
    if os.path.exists(out_path):
        # Already generated
        return out_path
        
    print(f"Generating preview for {file_path} -> {out_path}")
    
    if ext.lower() == '.mp4':
        # Extract first frame and scale down width to max 800px, quality 80%
        # -vframes 1 captures just the first frame
        # -scale down preserving aspect ratio
        # -q:v 5 controls jpeg quality (2-31, lower is better, 5-8 is good for preview)
        cmd = [
            'ffmpeg', '-y', '-i', file_path, 
            '-vframes', '1', 
            '-vf', 'scale=600:-1', 
            '-q:v', '5', 
            out_path
        ]
    else:
        # It's an image, just scale down
        cmd = [
            'ffmpeg', '-y', '-i', file_path, 
            '-vf', 'scale=600:-1', 
            '-q:v', '5', 
            out_path
        ]
        
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None
        
    return out_path

for p in patterns:
    files = sorted(glob.glob(p))
    for f in files:
        create_preview(f)

print("Preview generation completed.")
