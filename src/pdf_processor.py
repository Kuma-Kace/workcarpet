import os
import re
from typing import List, Tuple, Dict, Optional
import pypdf

from src.text_cleaner import clean_text_for_textaloud, remove_headers_footers_and_page_numbers
from src.audio_generator import generate_batch_audio, DEFAULT_VOICE
from src.textaloud_integration import generate_audio_with_textaloud, find_textaloud_executable

# Regex patterns for chapter headers
CHAPTER_PATTERNS = [
    r'^(cap[íi]tulo\s+[\dIVXLCDM]+.*)$',
    r'^(chapter\s+[\dIVXLCDM]+.*)$',
    r'^(pr[óo]logo.*)$',
    r'^(ep[íi]logo.*)$',
    r'^(introducci[óo]n.*)$',
    r'^(prefacio.*)$',
    r'^(secci[óo]n\s+[\dIVXLCDM]+.*)$',
    r'^([\dIVXLCDM]+\b\s*[-–—:]?\s*[A-ZÁÉÍÓÚÑ].*)$',
    r'^([★*✦♦❖§~=─-]{3,})$',  # Decorative symbols representing chapter breaks
]

def sanitize_filename(filename: str) -> str:
    """
    Sanitizes title strings to create safe filenames.
    Removes invalid characters and inverted question/exclamation marks.
    """
    s = re.sub(r'[\\/*?:"<>|¿¡]', "", filename)
    s = re.sub(r'\s+', '_', s.strip())
    return s[:60] if s else "Capitulo"


def extract_pages_from_pdf(pdf_path: str) -> List[str]:
    """
    Extracts raw text from each page of a PDF file using pypdf.
    """
    reader = pypdf.PdfReader(pdf_path)
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)
    return pages


def detect_chapters(full_text: str) -> List[Tuple[str, str]]:
    """
    Splits full text into chapters based on header patterns or decorative symbols.
    Returns list of tuples: (chapter_title, chapter_content)
    """
    lines = full_text.split('\n')
    chapters = []
    current_title = "Inicio / Introducción"
    current_lines = []

    combined_pattern = re.compile('|'.join(CHAPTER_PATTERNS), re.IGNORECASE)

    for line in lines:
        stripped = line.strip()
        match = combined_pattern.match(stripped) if stripped else None

        if match:
            if current_lines:
                content = '\n'.join(current_lines).strip()
                if content:
                    chapters.append((current_title, content))
                current_lines = []

            if re.match(r'^([★*✦♦❖§~=─-]{3,})$', stripped):
                current_title = f"Capítulo {len(chapters) + 1}"
            else:
                current_title = stripped.strip()
        else:
            current_lines.append(line)

    if current_lines:
        content = '\n'.join(current_lines).strip()
        if content:
            chapters.append((current_title, content))

    if not chapters:
        chapters = [("Libro Completo", full_text)]

    return chapters


def process_pdf_to_audiobook_txt(
    pdf_path: str,
    output_base_dir: str = "output",
    split_chapters: bool = True,
    fix_hyphens: bool = True,
    clean_dialogues: bool = True,
    merge_paragraphs: bool = True,
    remove_headers_footers: bool = True,
    generate_audio: bool = False,
    tts_engine: str = "edge_tts",  # "edge_tts" or "textaloud"
    voice_id: str = DEFAULT_VOICE,
    ta_exe_path: Optional[str] = None,
    max_audio_concurrency: int = 4,
    progress_callback = None
) -> Dict[str, List[str]]:
    """
    Main pipeline to process a PDF file and produce cleaned .txt and optional .mp3 files.
    Supports both Edge-TTS and TextAloud engines.
    """
    if progress_callback:
        progress_callback("Leyendo archivo PDF...", 10)

    raw_pages = extract_pages_from_pdf(pdf_path)
    if not raw_pages or not "".join(raw_pages).strip():
        raise ValueError("No se pudo extraer texto del PDF (el archivo podría ser solo imágenes o estar protegido).")

    if progress_callback:
        progress_callback("Eliminando encabezados, pies de página y números de página...", 25)

    if remove_headers_footers:
        cleaned_pages = remove_headers_footers_and_page_numbers(raw_pages)
    else:
        cleaned_pages = raw_pages

    full_text = "\n\n".join(cleaned_pages)

    if progress_callback:
        progress_callback("Detectando y separando capítulos...", 40)

    if split_chapters:
        raw_chapters = detect_chapters(full_text)
    else:
        raw_chapters = [("Libro Completo", full_text)]

    if progress_callback:
        progress_callback("Limpiando y formateando texto...", 55)

    book_name = os.path.splitext(os.path.basename(pdf_path))[0]
    safe_book_folder_name = sanitize_filename(book_name)
    book_output_dir = os.path.join(output_base_dir, safe_book_folder_name)
    os.makedirs(book_output_dir, exist_ok=True)

    created_txt_files = []
    audio_tasks = []

    for idx, (title, content) in enumerate(raw_chapters, 1):
        cleaned_content = clean_text_for_textaloud(
            content,
            fix_hyphens=fix_hyphens,
            clean_dialogues=clean_dialogues,
            merge_paragraphs=merge_paragraphs
        )

        if split_chapters:
            title_clean = sanitize_filename(title)
            base_filename = f"{idx:02d}_{title_clean}"
            txt_filepath = os.path.join(book_output_dir, f"{base_filename}.txt")
            with open(txt_filepath, 'w', encoding='utf-8') as f:
                f.write(f"{title}\n\n{cleaned_content}\n")
        else:
            base_filename = f"{safe_book_folder_name}_completo"
            txt_filepath = os.path.join(book_output_dir, f"{base_filename}.txt")
            with open(txt_filepath, 'w', encoding='utf-8') as f:
                f.write(cleaned_content + "\n")

        created_txt_files.append(txt_filepath)

        if generate_audio:
            mp3_filepath = os.path.join(book_output_dir, f"{base_filename}.mp3")
            read_text = f"{title}.\n\n{cleaned_content}"
            audio_tasks.append((read_text, mp3_filepath))

    created_audio_files = []
    if generate_audio and audio_tasks:
        total_audio_tasks = len(audio_tasks)

        if tts_engine == "textaloud":
            if progress_callback:
                progress_callback(f"Generando audio con TextAloud ({total_audio_tasks} capítulos)...", 60)

            for idx, (read_text, mp3_path) in enumerate(audio_tasks, 1):
                if progress_callback:
                    pct = 60 + int((idx / total_audio_tasks) * 38)
                    progress_callback(f"Generando audio TextAloud ({idx}/{total_audio_tasks})...", pct)

                generate_audio_with_textaloud(
                    text=read_text,
                    output_audio_path=mp3_path,
                    ta_executable_path=ta_exe_path,
                    voice_name=voice_id
                )
                created_audio_files.append(mp3_path)
        else:
            def batch_progress(done, total):
                if progress_callback:
                    pct = 60 + int((done / total) * 38)
                    progress_callback(f"Generando audio neuronal ({done}/{total} capítulos)...", pct)

            if progress_callback:
                progress_callback(f"Iniciando síntesis de audio en paralelo ({total_audio_tasks} capítulos)...", 60)

            generate_batch_audio(
                items=audio_tasks,
                voice=voice_id,
                max_concurrency=max_audio_concurrency,
                progress_callback=batch_progress
            )
            created_audio_files = [path for _, path in audio_tasks]

    if progress_callback:
        progress_callback("¡Proceso completado!", 100)

    return {
        "folder": book_output_dir,
        "files": created_txt_files + created_audio_files,
        "txt_files": created_txt_files,
        "audio_files": created_audio_files
    }
