import asyncio
import edge_tts
from typing import Dict, List

# Default recommended high quality Spanish voices
SPANISH_VOICES = {
    "Álvaro (España - Masculino)": "es-ES-AlvaroNeural",
    "Elvira (España - Femenino)": "es-ES-ElviraNeural",
    "Jorge (México - Masculino)": "es-MX-JorgeNeural",
    "Dalia (México - Femenino)": "es-MX-DaliaNeural",
    "Gonzalo (Argentina - Masculino)": "es-AR-GonzaloNeural",
    "Elena (Argentina - Femenino)": "es-AR-ElenaNeural",
    "Salomé (Colombia - Femenino)": "es-CO-SalomeNeural",
    "Gonzalo (Chile - Masculino)": "es-CL-GonzaloNeural",
}

DEFAULT_VOICE = "es-ES-AlvaroNeural"


async def _generate_audio_async(text: str, output_mp3_path: str, voice: str = DEFAULT_VOICE, rate: str = "+0%"):
    """
    Asynchronously generates an MP3 audio file from text using edge-tts.
    """
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_mp3_path)


def generate_audio_from_text(text: str, output_mp3_path: str, voice: str = DEFAULT_VOICE, rate: str = "+0%"):
    """
    Synchronous wrapper to generate MP3 audio from text.
    """
    if not text.strip():
        return
    asyncio.run(_generate_audio_async(text, output_mp3_path, voice=voice, rate=rate))


def get_available_voices() -> Dict[str, str]:
    """
    Returns dictionary mapping display name to voice ID.
    """
    return SPANISH_VOICES
