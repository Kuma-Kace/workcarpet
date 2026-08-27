import os
import sys
import threading
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from src.pdf_processor import process_pdf_to_audiobook_txt
from src.audio_generator import SPANISH_VOICES, DEFAULT_VOICE
from src.textaloud_integration import find_textaloud_executable, get_installed_sapi5_voices


class AudiobookConverterGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Convertidor de PDF a AudioTexto y Audiolibro")
        self.geometry("740x720")
        self.minsize(640, 600)

        # Apply a clean theme
        self.style = ttk.Style(self)
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        self.pdf_file_path = tk.StringVar()
        self.output_dir_path = tk.StringVar(value=os.path.abspath("output"))

        # Processing options
        self.split_chapters_var = tk.BooleanVar(value=True)
        self.fix_hyphens_var = tk.BooleanVar(value=True)
        self.clean_dialogues_var = tk.BooleanVar(value=True)
        self.merge_paragraphs_var = tk.BooleanVar(value=True)
        self.remove_headers_var = tk.BooleanVar(value=True)

        # Audio options
        self.generate_audio_var = tk.BooleanVar(value=False)
        self.tts_engine_var = tk.StringVar(value="edge_tts")  # "edge_tts" or "textaloud"
        self.selected_voice_display = tk.StringVar(value=list(SPANISH_VOICES.keys())[0])

        # TextAloud options
        detected_ta = find_textaloud_executable() or ""
        self.textaloud_path_var = tk.StringVar(value=detected_ta)
        self.ta_sapi_voices = get_installed_sapi5_voices()

        self.event_queue = queue.Queue()

        self._create_widgets()
        self._check_queue()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="15 15 15 15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(
            main_frame,
            text="Convertidor de PDF a AudioTexto y Audiolibro",
            font=("Helvetica", 14, "bold")
        )
        title_label.pack(anchor=tk.W, pady=(0, 5))

        desc_label = ttk.Label(
            main_frame,
            text="Limpia guiones de diálogo, sangrías y encabezados. Genera .txt y audiolibros .mp3 mediante Voces Neuronales o integración directa con TextAloud.",
            font=("Helvetica", 9),
            wraplength=680
        )
        desc_label.pack(anchor=tk.W, pady=(0, 15))

        # Files Section
        file_frame = ttk.LabelFrame(main_frame, text=" Archivos y Directorios ", padding="10 10 10 10")
        file_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(file_frame, text="Archivo PDF:").grid(row=0, column=0, sticky=tk.W, pady=5)
        pdf_entry = ttk.Entry(file_frame, textvariable=self.pdf_file_path, width=50)
        pdf_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        browse_pdf_btn = ttk.Button(file_frame, text="Examinar...", command=self._browse_pdf)
        browse_pdf_btn.grid(row=0, column=2, pady=5)

        ttk.Label(file_frame, text="Carpeta de Salida:").grid(row=1, column=0, sticky=tk.W, pady=5)
        out_entry = ttk.Entry(file_frame, textvariable=self.output_dir_path, width=50)
        out_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        browse_out_btn = ttk.Button(file_frame, text="Examinar...", command=self._browse_output_dir)
        browse_out_btn.grid(row=1, column=2, pady=5)

        file_frame.columnconfigure(1, weight=1)

        # Text Options Section
        options_frame = ttk.LabelFrame(main_frame, text=" Opciones de Texto ", padding="10 10 10 10")
        options_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(
            options_frame,
            text="Separar por capítulos en archivos individuales (en carpeta reservada del libro)",
            variable=self.split_chapters_var
        ).pack(anchor=tk.W, pady=2)

        ttk.Checkbutton(
            options_frame,
            text="Eliminar guiones de diálogo iniciales y convertir acotaciones en pausas naturales (comas)",
            variable=self.clean_dialogues_var
        ).pack(anchor=tk.W, pady=2)

        ttk.Checkbutton(
            options_frame,
            text="Unificar párrafos y eliminar sangrías/saltos de línea innecesarios",
            variable=self.merge_paragraphs_var
        ).pack(anchor=tk.W, pady=2)

        ttk.Checkbutton(
            options_frame,
            text="Unir palabras divididas por guion al final de línea (ej. progra-ma -> programa)",
            variable=self.fix_hyphens_var
        ).pack(anchor=tk.W, pady=2)

        ttk.Checkbutton(
            options_frame,
            text="Detectar y eliminar encabezados, pies de página y números de página",
            variable=self.remove_headers_var
        ).pack(anchor=tk.W, pady=2)

        # Audio Generation & TextAloud Options
        audio_frame = ttk.LabelFrame(main_frame, text=" Opciones de Audio (Síntesis / TextAloud) ", padding="10 10 10 10")
        audio_frame.pack(fill=tk.X, pady=(0, 10))

        cb_audio = ttk.Checkbutton(
            audio_frame,
            text="Generar también archivos de audio MP3",
            variable=self.generate_audio_var,
            command=self._toggle_audio_options
        )
        cb_audio.pack(anchor=tk.W, pady=(2, 5))

        # Motor de voz Selection
        engine_row = ttk.Frame(audio_frame)
        engine_row.pack(fill=tk.X, pady=2)

        ttk.Label(engine_row, text="Motor de Voz:").pack(side=tk.LEFT, padx=(0, 10))

        self.rb_edge = ttk.Radiobutton(
            engine_row,
            text="Voces Neuronales (Integrado)",
            variable=self.tts_engine_var,
            value="edge_tts",
            command=self._on_engine_change,
            state="disabled"
        )
        self.rb_edge.pack(side=tk.LEFT, padx=(0, 10))

        self.rb_ta = ttk.Radiobutton(
            engine_row,
            text="TextAloud (Instalado en Windows)",
            variable=self.tts_engine_var,
            value="textaloud",
            command=self._on_engine_change,
            state="disabled"
        )
        self.rb_ta.pack(side=tk.LEFT)

        # Voice Selector Row
        voice_row = ttk.Frame(audio_frame)
        voice_row.pack(fill=tk.X, pady=5)

        ttk.Label(voice_row, text="Voz Narradora:").pack(side=tk.LEFT, padx=(0, 10))
        self.voice_combo = ttk.Combobox(
            voice_row,
            textvariable=self.selected_voice_display,
            values=list(SPANISH_VOICES.keys()),
            state="disabled",
            width=42
        )
        self.voice_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # TextAloud Path Row
        self.ta_path_frame = ttk.Frame(audio_frame)
        ttk.Label(self.ta_path_frame, text="Ruta TextAloud (TACommand.exe):").pack(side=tk.LEFT, padx=(0, 5))
        self.ta_entry = ttk.Entry(self.ta_path_frame, textvariable=self.textaloud_path_var, width=35)
        self.ta_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        browse_ta_btn = ttk.Button(self.ta_path_frame, text="Buscar...", command=self._browse_textaloud_exe)
        browse_ta_btn.pack(side=tk.LEFT)

        # Progress Section
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(5, 10))

        self.progress_bar = ttk.Progressbar(progress_frame, mode="determinate")
        self.progress_bar.pack(fill=tk.X, side=tk.TOP, pady=(0, 5))

        self.status_label = ttk.Label(progress_frame, text="Listo para comenzar.", font=("Helvetica", 9, "italic"))
        self.status_label.pack(anchor=tk.W)

        # Convert Button
        self.convert_btn = ttk.Button(
            main_frame,
            text="⚡ Convertir Libro",
            command=self._start_conversion
        )
        self.convert_btn.pack(pady=(0, 10), ipady=5, fill=tk.X)

        # Log Text Box
        log_frame = ttk.LabelFrame(main_frame, text=" Registro de Procesamiento ", padding="5 5 5 5")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=7, font=("Consolas", 8))
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

    def _toggle_audio_options(self):
        enabled = self.generate_audio_var.get()
        state = "normal" if enabled else "disabled"
        self.rb_edge.config(state=state)
        self.rb_ta.config(state=state)

        if enabled:
            self._on_engine_change()
        else:
            self.voice_combo.config(state="disabled")
            self.ta_path_frame.pack_forget()

    def _on_engine_change(self):
        engine = self.tts_engine_var.get()
        if engine == "edge_tts":
            self.voice_combo.config(values=list(SPANISH_VOICES.keys()), state="readonly")
            if self.selected_voice_display.get() not in SPANISH_VOICES:
                self.selected_voice_display.set(list(SPANISH_VOICES.keys())[0])
            self.ta_path_frame.pack_forget()
        else:
            voices = self.ta_sapi_voices if self.ta_sapi_voices else ["Voz por defecto de TextAloud"]
            self.voice_combo.config(values=voices, state="readonly")
            if self.selected_voice_display.get() not in voices:
                self.selected_voice_display.set(voices[0])
            self.ta_path_frame.pack(fill=tk.X, pady=(5, 0))

    def _browse_textaloud_exe(self):
        path = filedialog.askopenfilename(
            title="Seleccionar ejecutable de TextAloud (TACommand.exe)",
            filetypes=[("Ejecutables", "*.exe"), ("Todos los archivos", "*.*")]
        )
        if path:
            self.textaloud_path_var.set(path)

    def _browse_pdf(self):
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo PDF",
            filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            self.pdf_file_path.set(file_path)

    def _browse_output_dir(self):
        dir_path = filedialog.askdirectory(title="Seleccionar carpeta de salida")
        if dir_path:
            self.output_dir_path.set(dir_path)

    def _log(self, message: str):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def _update_progress(self, status: str, value: int):
        self.status_label.config(text=status)
        self.progress_bar["value"] = value
        self._log(f"[{value}%] {status}")

    def _check_queue(self):
        while not self.event_queue.empty():
            try:
                event_type, args = self.event_queue.get_nowait()
                if event_type == "progress":
                    status, val = args
                    self._update_progress(status, val)
                elif event_type == "success":
                    folder, txt_count, audio_count = args
                    self._conversion_success(folder, txt_count, audio_count)
                elif event_type == "error":
                    err_msg = args
                    self._conversion_error(err_msg)
            except queue.Empty:
                break
        self.after(100, self._check_queue)

    def _start_conversion(self):
        pdf_path = self.pdf_file_path.get().strip()
        out_dir = self.output_dir_path.get().strip()

        if not pdf_path or not os.path.exists(pdf_path):
            messagebox.showerror("Error", "Por favor seleccione un archivo PDF válido.")
            return

        if not out_dir:
            messagebox.showerror("Error", "Por favor especifique una carpeta de salida.")
            return

        engine = self.tts_engine_var.get()
        voice_display = self.selected_voice_display.get()

        if engine == "edge_tts":
            voice_id = SPANISH_VOICES.get(voice_display, DEFAULT_VOICE)
        else:
            voice_id = voice_display if voice_display != "Voz por defecto de TextAloud" else None

        options = {
            "split_chapters": self.split_chapters_var.get(),
            "fix_hyphens": self.fix_hyphens_var.get(),
            "clean_dialogues": self.clean_dialogues_var.get(),
            "merge_paragraphs": self.merge_paragraphs_var.get(),
            "remove_headers_footers": self.remove_headers_var.get(),
            "generate_audio": self.generate_audio_var.get(),
            "tts_engine": engine,
            "voice_id": voice_id,
            "ta_exe_path": self.textaloud_path_var.get().strip() or None
        }

        self.convert_btn.config(state=tk.DISABLED)
        self.log_text.delete("1.0", tk.END)
        self.progress_bar["value"] = 0

        threading.Thread(target=self._run_conversion_worker, args=(pdf_path, out_dir, options), daemon=True).start()

    def _run_conversion_worker(self, pdf_path: str, out_dir: str, options: dict):
        try:
            result = process_pdf_to_audiobook_txt(
                pdf_path=pdf_path,
                output_base_dir=out_dir,
                split_chapters=options["split_chapters"],
                fix_hyphens=options["fix_hyphens"],
                clean_dialogues=options["clean_dialogues"],
                merge_paragraphs=options["merge_paragraphs"],
                remove_headers_footers=options["remove_headers_footers"],
                generate_audio=options["generate_audio"],
                tts_engine=options["tts_engine"],
                voice_id=options["voice_id"],
                ta_exe_path=options["ta_exe_path"],
                progress_callback=lambda status, val: self.event_queue.put(("progress", (status, val)))
            )

            folder = result["folder"]
            txt_files = result["txt_files"]
            audio_files = result["audio_files"]

            self.event_queue.put(("success", (folder, len(txt_files), len(audio_files))))
        except Exception as e:
            self.event_queue.put(("error", str(e)))

    def _conversion_success(self, folder: str, txt_count: int, audio_count: int):
        self.convert_btn.config(state=tk.NORMAL)
        msg_summary = f"Se crearon {txt_count} archivo(s) .txt"
        if audio_count > 0:
            msg_summary += f" y {audio_count} archivo(s) de audio .mp3"

        self._log(f"\n✅ ¡Éxito! {msg_summary} en la carpeta:\n{folder}")
        messagebox.showinfo(
            "Conversión Completada",
            f"{msg_summary} con éxito en:\n\n{folder}"
        )

    def _conversion_error(self, err_msg: str):
        self.convert_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Error durante el procesamiento.")
        self._log(f"\n❌ Error: {err_msg}")
        messagebox.showerror("Error en Conversión", f"Ocurrió un error al procesar el PDF:\n\n{err_msg}")


def main():
    app = AudiobookConverterGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
