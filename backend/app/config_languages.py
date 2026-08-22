LANGUAGES = {
    "te": "Telugu",
    "hi": "Hindi",
    "ta": "Tamil",
    "kn": "Kannada",
    "ml": "Malayalam",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "or": "Odia",
    "as": "Assamese",
    "ur": "Urdu",
    "en": "English",
}

def get_language_name(code: str) -> str:
    # Sarvam might return hi-IN, normalize it
    code = code.split("-")[0].lower()
    return LANGUAGES.get(code, "English")
