import asyncio
import edge_tts
from typing import Dict, List, Tuple

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


async def _generate_audio_single_async(text: str, output_mp3_path: str, voice: str = DEFAULT_VOICE, rate: str = "+0%", sema: asyncio.Semaphore = None):
    """
    Asynchronously generates an MP3 audio file from text using edge-tts.
    """
    if not text.strip():
        return

    if sema:
        async with sema:
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            await communicate.save(output_mp3_path)
    else:
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        await communicate.save(output_mp3_path)


def generate_audio_from_text(text: str, output_mp3_path: str, voice: str = DEFAULT_VOICE, rate: str = "+0%"):
    """
    Synchronous wrapper for single text audio generation.
    """
    if not text.strip():
        return
    asyncio.run(_generate_audio_single_async(text, output_mp3_path, voice=voice, rate=rate))


async def _generate_batch_audio_async(
    items: List[Tuple[str, str]],  # List of (text, output_mp3_path)
    voice: str = DEFAULT_VOICE,
    rate: str = "+0%",
    max_concurrency: int = 4,
    progress_callback = None
):
    """
    Asynchronously generates MP3 audio files in parallel with concurrency limit.
    """
    if not items:
        return

    sema = asyncio.Semaphore(max_concurrency)
    completed_count = 0
    total_count = len(items)

    async def worker(text, output_path):
        nonlocal completed_count
        await _generate_audio_single_async(text, output_path, voice=voice, rate=rate, sema=sema)
        completed_count += 1
        if progress_callback:
            progress_callback(completed_count, total_count)

    tasks = [asyncio.create_task(worker(text, path)) for text, path in items if text.strip()]
    if tasks:
        await asyncio.gather(*tasks)


def generate_batch_audio(
    items: List[Tuple[str, str]],
    voice: str = DEFAULT_VOICE,
    rate: str = "+0%",
    max_concurrency: int = 4,
    progress_callback = None
):
    """
    Synchronous wrapper to generate a batch of MP3 audio files concurrently.
    """
    if not items:
        return
    asyncio.run(_generate_batch_audio_async(
        items,
        voice=voice,
        rate=rate,
        max_concurrency=max_concurrency,
        progress_callback=progress_callback
    ))


def get_available_voices() -> Dict[str, str]:
    return SPANISH_VOICES
