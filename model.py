from PIL import Image, UnidentifiedImageError
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration
import streamlit as st
from gtts import gTTS
from deep_translator import GoogleTranslator
import io

# ==========================================
# DEVICE
# ==========================================

device = "cuda" if torch.cuda.is_available() else "cpu"

# ==========================================
# VALID IMAGE
# ==========================================

VALID_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".gif")

def is_valid_image(path):

    try:
        with Image.open(path) as img:
            img.verify()

        return True

    except (UnidentifiedImageError, OSError):
        return False


# ==========================================
# LOAD MODEL
# ==========================================


@st.cache_resource
def load_model():

    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")

    model = BlipForConditionalGeneration.from_pretrained(
        "Salesforce/blip-image-captioning-large",
    ).to(device)

    model.eval()

    return processor, model



processor, model = load_model()

# ==========================================
# CLEANING
# ==========================================


def clean_caption(text):

    text = text.lower()

    prefixes = ["this is", "there is", "there are", "a picture of"]

    for p in prefixes:
        if text.startswith(p):
            text = text.replace(p, "").strip()

    return text.capitalize()


# ==========================================
# GENERATE CAPTION
# ==========================================

def generate_caption(image):

    if isinstance(image, str):
        image = Image.open(image).convert("RGB")

    prompt = "a photo of"

    inputs = processor(images=image, text=prompt, return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            num_beams=8,
            max_length=55,
            min_length=15,
            repetition_penalty=1.2,
            length_penalty=0.9,
            no_repeat_ngram_size=2,
            early_stopping=True,
        )

    caption = processor.decode(outputs[0], skip_special_tokens=True)

    return clean_caption(caption)


# ==========================================
# TRANSLATION
# ==========================================


def translate_to_arabic(text):

    try:
        return GoogleTranslator(source="auto", target="ar").translate(text)

    except Exception as e:
        print("Translation error:", e)

        return text


# ==========================================
# TEXT TO SPEECH
# ==========================================

def text_to_speech(text):

    try:
        tts = gTTS(text=text, lang="ar")

        audio_buffer = io.BytesIO()

        tts.write_to_fp(audio_buffer)

        return audio_buffer.getvalue()

    except Exception as e:
        print("TTS error:", e)

        return None
