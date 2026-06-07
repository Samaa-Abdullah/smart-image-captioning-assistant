import streamlit as st
from PIL import Image, UnidentifiedImageError
from html import escape
import base64
import time

from model import generate_caption, translate_to_arabic, text_to_speech

# ====================================================
# PAGE CONFIG
# ====================================================

st.set_page_config(page_title="AI Visual Assistant", layout="centered")

# ====================================================
# ACCESSIBILITY STYLE
# ====================================================

st.markdown(
    """
<style>

html, body, [class*="css"] {
    font-size: 24px !important;
}

.stButton > button {
    width: 100%;
    height: 70px;
    font-size: 24px;
    border-radius: 15px;
}

.caption-box {
    background-color: #1e2230;
    padding: 25px;
    border-radius: 20px;
    margin-top: 20px;
}

.caption-label {
    font-size: 28px;
    font-weight: bold;
    margin-bottom: 15px;
    text-align: right;
    color: white;
}

.arabic-text {
    direction: rtl;
    text-align: right;
    font-size: 30px;
    line-height: 2;
    font-weight: bold;
    color: white;
    letter-spacing: 1px;
}

</style>
""",
    unsafe_allow_html=True,
)

# ====================================================
# AUDIO PLAYER
# ====================================================


def autoplay_audio(audio_bytes, autoplay=True):

    if audio_bytes is None:
        return

    b64 = base64.b64encode(audio_bytes).decode()

    audio_id = f"audio_{time.time()}"

    if autoplay:
        audio_html = f"""
        <audio id="{audio_id}" autoplay controls>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """

    else:
        audio_html = f"""
        <audio id="{audio_id}" controls>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>

        <script>
        var audio = document.getElementById("{audio_id}");
        audio.play();
        </script>
        """

    st.markdown(audio_html, unsafe_allow_html=True)


# ====================================================
# SPEAK FUNCTION
# ====================================================


def speak(text, wait_time=2):

    audio = text_to_speech(text)

    autoplay_audio(audio)

    time.sleep(wait_time)


# ====================================================
# TITLE
# ====================================================

st.title(" AI Visual Assistant")


# ====================================================
# WELCOME MESSAGE
# ====================================================

if "welcome_played" not in st.session_state:
    speak("مرحبًا، اختر صورة لتحليلها", wait_time=3)

    st.session_state.welcome_played = True

# ====================================================
# FILE UPLOADER
# ====================================================

uploaded_file = st.file_uploader(
    "اختر صورة لتحليلها", type=["jpg", "jpeg", "png", "webp"]
)

if uploaded_file is None:
    st.session_state.pop("caption_ar", None)
    st.session_state.pop("caption_en", None)
    st.session_state.pop("final_audio", None)
    st.session_state.pop("last_uploaded", None)

# ====================================================
# MAIN FLOW
# ====================================================

if uploaded_file is not None:
    # منع إعادة التشغيل المتكرر للصوت
    uploaded_file_name = uploaded_file.name

    if st.session_state.get("last_uploaded") != uploaded_file_name:
        st.session_state.last_uploaded = uploaded_file_name

        try:
            # -------------------------------------------------
            # IMAGE UPLOADED MESSAGE
            # -------------------------------------------------

            speak("تم رفع الصورة بنجاح", wait_time=3)

            # -------------------------------------------------
            # OPEN IMAGE
            # -------------------------------------------------

            image = Image.open(uploaded_file).convert("RGB")

            # st.image(
            # image,
            # caption="Uploaded Image",
            # use_container_width=True
            # )

            # -------------------------------------------------
            # PROCESSING MESSAGE
            # -------------------------------------------------

            speak("جاري تحليل الصورة، برجاء الانتظار", wait_time=3)

            # -------------------------------------------------
            # IMAGE ANALYSIS
            # -------------------------------------------------

            with st.spinner("Analyzing image..."):
                caption_en = generate_caption(image)

                caption_ar = translate_to_arabic(caption_en)

            # -------------------------------------------------
            # FALLBACK
            # -------------------------------------------------

            if not caption_ar or len(caption_ar.strip()) < 3:
                caption_ar = "تعذر وصف الصورة"

            # -------------------------------------------------
            # DESCRIPTION INTRO
            # -------------------------------------------------

            speak("وصف الصورة", wait_time=2)

            # -------------------------------------------------
            # SAVE RESULTS
            # -------------------------------------------------

            st.session_state.caption_ar = caption_ar
            st.session_state.caption_en = caption_en
            st.session_state.final_audio = text_to_speech(caption_ar)

        # =====================================================
        # INVALID IMAGE
        # =====================================================

        except UnidentifiedImageError:
            # حذف البيانات القديمة
            st.session_state.pop("caption_ar", None)
            st.session_state.pop("caption_en", None)
            st.session_state.pop("final_audio", None)

            st.session_state.audio_played = False

            speak("الصورة غير صالحة", wait_time=2)

            st.error("الصورة غير صالحة أو تالفة")

        # =====================================================
        # GENERAL ERROR
        # =====================================================

        except Exception as e:
            speak("حدث خطأ أثناء معالجة الصورة", wait_time=2)

            st.error(str(e))

# ====================================================
# SHOW RESULTS
# ====================================================

if "caption_ar" in st.session_state:
    st.markdown("## الوصف العربي")

    st.markdown(
        f"""
        <div style="
            direction: rtl;
            text-align: right;
            font-size: 32px;
            line-height: 2;
            font-weight: bold;
            margin-top: 20px;
        ">
            {escape(st.session_state.caption_ar)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -------------------------------------------------
    # FINAL DESCRIPTION AUDIO
    # -------------------------------------------------

    autoplay_audio(st.session_state.final_audio)

    # -------------------------------------------------
    # REPEAT BUTTON
    # -------------------------------------------------

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🔊 إعادة قراءة الوصف"):
        autoplay_audio(st.session_state.final_audio, autoplay=False)

    # -------------------------------------------------
    # ENGLISH DESCRIPTION
    # -------------------------------------------------

    with st.expander("English Description"):
        st.write(st.session_state.caption_en)
