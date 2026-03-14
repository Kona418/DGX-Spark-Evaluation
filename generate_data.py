import os
import json
import glob

# Descriptive names for categories
IMAGE_CATEGORIES = [
    "Priming",
    "Neon Sign",
    "Book Stack",
    "Chameleon Eye",
    "Crystal Skull",
    "Cyberpunk City"
]

VIDEO_CATEGORIES = [
    "Priming",
    "Ocean Wave",
    "Drone Forest",
    "Metallic Sphere",
    "Pocket Watch",
    "Floating Orb"
]

AUDIO_VIDEO_CATEGORIES = [
    "Priming",
    "Rock Band",
    "Podcast",
    "Lightsaber Duel",
    "Cooking Show",
    "Formula 1"
]

IMAGE_PROMPTS = [
    "A surreal, cinematic wide shot of a massive, derelict brutalist concrete atrium that is heavily overgrown by a dense, lush jungle. The entire floor is flooded with perfectly still, glassy water, creating a flawless mirror reflection of the crumbling concrete architecture and massive tropical trees reaching towards large breaks in the high glass ceiling overhead. Sunlight filters through the canopy and the broken roof, creating dramatic god rays and dappled light patterns on the water surface, wet vines, and mossy concrete structures. Post-apocalyptic aesthetic, extreme detail.",
    "A glowing neon sign in a dark rainy alleyway that clearly spells 'SPARK-2026' in bright pink letters.",
    "A small red apple resting on top of a stack of three books: a blue book at the bottom, a green book in the middle, and a yellow book at the top.",
    "Extreme macro photography of a chameleon's eye, showing the intricate hexagonal scale patterns and vivid green and orange colors.",
    "A transparent crystal skull sitting on a mirror table, illuminated by a single harsh spotlight from the right, creating complex caustics and refractions.",
    "An isometric view of a futuristic highly dense cyberpunk city with hundreds of flying cars, glowing skyscrapers, and intricate cable networks."
]

VIDEO_PROMPTS = [
    "A continuous slow, low-angle tracking shot moving forward through a dense, foggy cyberpunk city alleyway at night. Neon signs flicker intensely in the rain, and the wet asphalt perfectly reflects the blue and pink lights. A single flying vehicle slowly passes overhead from left to right.",
    "A slow-motion shot of a massive ocean wave crashing against a jagged dark cliff, sending bright white sea spray high into the air.",
    "A smooth drone tracking shot flying low over a lush green forest canopy towards a towering snow-capped mountain peak at sunset.",
    "A shiny silver metallic sphere rolling perfectly straight along a checkered black and white floor under dim industrial lights.",
    "A close-up of an intricate brass pocket watch mechanism, with dozens of tiny gears interlocking and continuously rotating.",
    "A dark room where a single glowing orb floats slowly from left to right, casting moving shadows behind a stationary marble bust."
]

AUDIO_VIDEO_PROMPTS = [
    VIDEO_PROMPTS[0], 
    "A high-energy rock band playing on a neon-lit stage. The lead singer passionately sings into a vintage microphone while the guitarist shreds a solo. Quick camera cuts between the singer and the guitarist. Audio: Fast-paced electric guitar riff accompanied by heavy drum beats and a powerful, melodic male rock vocal singing \"We ignite the night\".",
    "Two people sitting in a modern, soundproofed studio with professional microphones and warm lighting. The woman on the left gestures with her hands while speaking, and the man on the right nods thoughtfully, taking a sip from a coffee mug. Audio: Clear, close-mic studio audio. A female voice says, \"The fascinating thing about this technology is how it scales,\" followed by a male voice responding, \"Exactly, and the hardware limits are being pushed every day.\"",
    "Two sci-fi warriors engaged in a fast-paced duel using glowing energy swords in a dark, metallic corridor. Sparks fly as a red energy blade clashes with a blue energy blade. The warrior with the blue sword pushes the other back. Audio: Loud humming and crackling sounds of energy blades clashing. A deep male voice shouts, \"You cannot win this battle!\", followed by the loud sizzle of the swords locking together.",
    "A cheerful chef in a white uniform standing in a bright, rustic kitchen. He vigorously chops fresh vegetables on a wooden cutting board, then scrapes them into a steaming pan on the stove, creating a burst of steam. Audio: The rapid chopping sound of a knife on wood, followed by a loud sizzling sound. A male voice speaks clearly, saying, \"Now we add the fresh peppers to get that perfect sizzle.\"",
    "A fast panning shot of two formula racing cars speeding down a sunlit asphalt straightaway. The leading red car sharply takes a corner, kicking up a small cloud of tire smoke, while the second silver car attempts to overtake on the inside. Audio: The extremely loud, high-pitched whining roar of high-speed racing engines passing by. An excited, fast-speaking male sports commentator yells, \"He is going for the inside line, what a spectacular overtaking maneuver!\""
]

DHBW_IMAGE_PROMPT = """A high-definition, photorealistic architectural photo of the DHBW building from a direct frontal perspective on a bright, sunny day.

Architecture and Details:
Left side: Modern white stucco facade. A large tree trunk heavily frames the far left edge, with lush foliage above. A far-left paved path features a pedestrian crossing sign, a walking woman, and parked bicycles. A covered entrance with steps has a small, proportionately scaled DHBW logo mounted above it (red/grey geometric element, red 'DHBW' text, grey 'Duale Hochschule Baden-Württemberg' sub-text). 
Center: A multi-story vertical glass curtain wall with visible internal structures and a tall flagpole to its left.
Right side: White facade with twelve clear, square windows in a 2x6 grid. Directly beneath specific clear windows are small, colored horizontal panel bars. Upper row panel colors (L-R): None, Orange, Red, Blue-grey, None, Blue-grey. Lower row panel colors (L-R): None, Orange, Red, Blue-grey, Orange, Blue-grey.
Ground level: Dark grey glass café frontage with white handwritten text on the glass. Outdoor seating with metal tables.
Foreground: A low concrete retaining wall. Cobblestone paving in front of the entrance. The lower asphalt street slopes visibly downwards towards the right and features three dark wooden bollards.

Style: Crisp, detailed architectural photography. Bright lighting, well-defined shadows, and authentic textures for stucco, glass, metal, and wood."""

DHBW_VIDEO_PROMPT = """A high-definition, photorealistic architectural video of the DHBW building from a direct, central frontal perspective on a bright, sunny day. The camera remains static and centered on the building.

Architecture and Details:
Left side: Modern white stucco facade. A large tree trunk heavily frames the far left edge, with lush foliage gently moving above. A far-left paved path features a pedestrian crossing sign. A covered entrance with steps has a small, proportionately scaled DHBW logo mounted above it (red/grey geometric element, red 'DHBW' text, grey 'Duale Hochschule Baden-Württemberg' sub-text).
Center: A multi-story vertical glass curtain wall with visible internal structures and a tall flagpole to its left.
Right side: White facade with twelve clear, square windows in a 2x6 grid. Directly beneath specific clear windows are small, colored horizontal panel bars. Upper row panel colors (L-R): None, Orange, Red, Blue-grey, None, Blue-grey. Lower row panel colors (L-R): None, Orange, Red, Blue-grey, Orange, Blue-grey.
Ground level: Dark grey glass café frontage with white handwritten text on the glass. Outdoor seating with metal tables.
Foreground: A low concrete retaining wall. Cobblestone paving in front of the entrance. The lower asphalt street slopes visibly downwards towards the right and features three dark wooden bollards.

Action and Subjects:
Groups of students are standing in front of the building and talking. Several students are walking by. A few students ride past on bicycles. One specific student approaches a parked bicycle, mounts it, and rides away.

Style: Crisp, detailed architectural video. Bright lighting, well-defined shadows, and authentic textures for stucco, glass, metal, and wood. Minimal camera movement to preserve structural accuracy.

Audio:
Ambient soundscape featuring distinct bird chirping, the sound of wind blowing, and occasional bicycle bells ringing. No voices and no dialogue."""

data = []

def determine_details(model, category_idx, source, is_audio=False, is_priming=False):
    if is_priming:
        if model in ['Flux2', 'SDXL']:
            return IMAGE_PROMPTS[0], "Priming"
        else:
            return VIDEO_PROMPTS[0], "Priming"
    if source == 'DHBW':
        if model in ['Flux2', 'SDXL']:
            return DHBW_IMAGE_PROMPT, "DHBW Architektur"
        else:
            return DHBW_VIDEO_PROMPT, "DHBW Architektur"
    
    if is_audio:
        prompt_text = AUDIO_VIDEO_PROMPTS[category_idx] if category_idx < len(AUDIO_VIDEO_PROMPTS) else AUDIO_VIDEO_PROMPTS[-1]
        cat_name = AUDIO_VIDEO_CATEGORIES[category_idx] if category_idx < len(AUDIO_VIDEO_CATEGORIES) else f"Audio Cat {category_idx}"
        return prompt_text, cat_name

    if model in ['Flux2', 'SDXL']:
        prompt_text = IMAGE_PROMPTS[category_idx] if category_idx < len(IMAGE_PROMPTS) else IMAGE_PROMPTS[-1]
        cat_name = IMAGE_CATEGORIES[category_idx] if category_idx < len(IMAGE_CATEGORIES) else f"Image Cat {category_idx}"
        return prompt_text, cat_name
    else:
        prompt_text = VIDEO_PROMPTS[category_idx] if category_idx < len(VIDEO_PROMPTS) else VIDEO_PROMPTS[-1]
        cat_name = VIDEO_CATEGORIES[category_idx] if category_idx < len(VIDEO_CATEGORIES) else f"Video Cat {category_idx}"
        return prompt_text, cat_name

# Collect files
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

for pattern in patterns:
    files = sorted(glob.glob(pattern))
    for i, file_path in enumerate(files):
        # Calculate seed: sequence is 99 (priming) then 42, 43, 44, 45, 46 for runs
        seed = 99 if i == 0 else 42 + ((i - 1) % 5)

        if 'DHBW_FLux2' in file_path:
            model, source, mtype, duration, category_idx = 'Flux2', 'DHBW', 'image', None, 'DHBW'
        elif 'Flux2' in file_path:
            category_idx = 0 if i == 0 else ((i - 1) // 5 + 1)
            model, source, mtype, duration = 'Flux2', 'Seminar', 'image', None
        elif 'SVD' in file_path:
            category_idx = 0 if i == 0 else ((i - 1) // 5 + 1)
            model, source, mtype, duration = 'SVD', 'Seminar', 'video', '1'
        elif 'DHBW_LTX2' in file_path:
            model, source, mtype, duration, category_idx = 'LTX2', 'DHBW', 'video', '10', 'DHBW'
        elif 'LTX_10sek' in file_path:
            category_idx = 0 if i == 0 else ((i - 1) // 5 + 1)
            model, source, mtype, duration = 'LTX2', 'Seminar', 'video', '10'
        elif 'LTX_15sek' in file_path:
            category_idx = 0 if i == 0 else ((i - 1) // 5 + 1)
            model, source, mtype, duration = 'LTX2', 'Seminar', 'video', '15'
        elif 'LTX_1sek' in file_path:
            category_idx = 0 if i == 0 else ((i - 1) // 5 + 1)
            model, source, mtype, duration = 'LTX2', 'Seminar', 'video', '1'
        elif 'SDXL' in file_path:
            category_idx = 0 if i == 0 else ((i - 1) // 5 + 1)
            model, source, mtype, duration = 'SDXL', 'Seminar', 'image', None

        is_audio = (duration == '15')
        c_idx_int = 0 if category_idx == 'DHBW' else int(category_idx)
        
        prompt_text, cat_name = determine_details(model, c_idx_int, source, is_audio, seed == 99)
        
        # Determine thumbnail path
        file_dir = os.path.dirname(file_path)
        preview_dir = os.path.join(os.path.dirname(file_dir), 'preview')
        name, _ = os.path.splitext(os.path.basename(file_path))
        potential_thumb = os.path.join(preview_dir, name + '.jpg')
        if os.path.exists(potential_thumb):
            thumb_path = potential_thumb
        else:
            thumb_path = file_path
        
        data.append({
            'file': file_path,
            'thumb': thumb_path,
            'type': mtype,
            'model': model,
            'duration': duration,
            'category': cat_name,
            'seed': seed,
            'prompt': prompt_text
        })

with open('assets/js/data.js', 'w') as f:
    f.write("const mediaData = " + json.dumps(data, indent=2) + ";\n")

print(f"Refreshed {len(data)} entries with full prompts, seeds, and names in data.js")
