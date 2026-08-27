import os
import sys
import subprocess
from typing import List, Dict, Optional

try:
    import winreg
except ImportError:
    winreg = None

TEXTALOUD_EXECUTABLE_NAMES = ["TACommand.exe", "TextAloud.exe"]
DEFAULT_PROGRAM_FILES_PATHS = [
    r"C:\Program Files (x86)\NextUp.com\TextAloud",
    r"C:\Program Files\NextUp.com\TextAloud",
    r"C:\Program Files (x86)\TextAloud",
    r"C:\Program Files\TextAloud",
]


def find_textaloud_executable() -> Optional[str]:
    """
    Attempts to locate TACommand.exe or TextAloud.exe on Windows.
    Checks Windows Registry and standard installation paths.
    """
    if sys.platform != "win32":
        return None

    # 1. Check Windows Registry if available
    if winreg:
        registry_keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\NextUp.com\TextAloud"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\NextUp.com\TextAloud"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\NextUp.com\TextAloud"),
        ]

        for root_key, key_path in registry_keys:
            try:
                with winreg.OpenKey(root_key, key_path) as key:
                    install_dir, _ = winreg.QueryValueEx(key, "Path")
                    if install_dir:
                        for exe_name in TEXTALOUD_EXECUTABLE_NAMES:
                            full_path = os.path.join(install_dir, exe_name)
                            if os.path.isfile(full_path):
                                return full_path
            except (OSError, FileNotFoundError):
                continue

    # 2. Check standard directory paths
    for base_path in DEFAULT_PROGRAM_FILES_PATHS:
        for exe_name in TEXTALOUD_EXECUTABLE_NAMES:
            full_path = os.path.join(base_path, exe_name)
            if os.path.isfile(full_path):
                return full_path

    return None


def get_installed_sapi5_voices() -> List[str]:
    """
    Lists SAPI5 voices installed on Windows (used by TextAloud).
    """
    voices = []
    if sys.platform != "win32" or not winreg:
        return voices

    sapi_keys = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Speech\Voices\Tokens"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Speech\Voices\Tokens"),
    ]

    for root_key, key_path in sapi_keys:
        try:
            with winreg.OpenKey(root_key, key_path) as key:
                i = 0
                while True:
                    try:
                        token_name = winreg.EnumKey(key, i)
                        i += 1
                        with winreg.OpenKey(key, token_name) as token_key:
                            try:
                                voice_name, _ = winreg.QueryValueEx(token_key, "")
                            except OSError:
                                voice_name = token_name
                            if voice_name and voice_name not in voices:
                                voices.append(voice_name)
                    except OSError:
                        break
        except (OSError, FileNotFoundError):
            continue

    return voices


def generate_audio_with_textaloud(
    text: str,
    output_audio_path: str,
    ta_executable_path: Optional[str] = None,
    voice_name: Optional[str] = None
) -> bool:
    """
    Generates an audio file from text using TextAloud CLI (TACommand.exe).
    Usage syntax for TACommand:
    TACommand.exe -file "input_txt_path" -output "output_mp3_path" [-voice "Voice Name"]
    """
    exe_path = ta_executable_path or find_textaloud_executable()
    if not exe_path or not os.path.isfile(exe_path):
        raise FileNotFoundError(
            "No se encontró el ejecutable de TextAloud (TACommand.exe). "
            "Por favor verifica que TextAloud esté instalado o especifica la ruta manualmente."
        )

    temp_txt_path = output_audio_path + ".tmp.txt"
    with open(temp_txt_path, "w", encoding="utf-8") as f:
        f.write(text)

    try:
        cmd = [exe_path, "-file", temp_txt_path, "-output", output_audio_path]
        if voice_name:
            cmd.extend(["-voice", voice_name])

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    finally:
        if os.path.exists(temp_txt_path):
            try:
                os.remove(temp_txt_path)
            except OSError:
                pass
