import os
import subprocess
import sys

def build_executable():
    """
    Builds a standalone executable using PyInstaller.
    """
    print("Iniciando la creación del ejecutable...")

    # PyInstaller command arguments
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name=Convertidor_AudioLibro_TextAloud",
        "--clean",
        "main.py"
    ]

    print("Ejecutando PyInstaller:", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("\n✅ ¡Ejecutable creado con éxito!")
        print(f"El archivo ejecutable se encuentra en la carpeta: {os.path.abspath('dist')}")
    else:
        print("\n❌ Error al crear el ejecutable:")
        print(result.stderr)
        sys.exit(1)

if __name__ == "__main__":
    build_executable()
