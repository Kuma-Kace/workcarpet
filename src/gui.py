import os
import sys
import threading
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from src.pdf_processor import process_pdf_to_audiobook_txt


class AudiobookConverterGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Convertidor de PDF a AudioTexto para TextAloud")
        self.geometry("680x580")
        self.minsize(600, 500)

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

        self.event_queue = queue.Queue()

        self._create_widgets()
        self._check_queue()

    def _create_widgets(self):
        # Main Frame
        main_frame = ttk.Frame(self, padding="15 15 15 15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title / Description
        title_label = ttk.Label(
            main_frame,
            text="Convertidor de PDF a AudioTexto (TextAloud)",
            font=("Helvetica", 14, "bold")
        )
        title_label.pack(anchor=tk.W, pady=(0, 5))

        desc_label = ttk.Label(
            main_frame,
            text="Limpia guiones de diálogo, sangrías, encabezados y prepara el texto para una lectura fluida en TextAloud.",
            font=("Helvetica", 9),
            wraplength=620
        )
        desc_label.pack(anchor=tk.W, pady=(0, 15))

        # File Selection Section
        file_frame = ttk.LabelFrame(main_frame, text=" Archivos y Directorios ", padding="10 10 10 10")
        file_frame.pack(fill=tk.X, pady=(0, 10))

        # PDF input row
        ttk.Label(file_frame, text="Archivo PDF:").grid(row=0, column=0, sticky=tk.W, pady=5)
        pdf_entry = ttk.Entry(file_frame, textvariable=self.pdf_file_path, width=50)
        pdf_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        browse_pdf_btn = ttk.Button(file_frame, text="Examinar...", command=self._browse_pdf)
        browse_pdf_btn.grid(row=0, column=2, pady=5)

        # Output folder row
        ttk.Label(file_frame, text="Carpeta de Salida:").grid(row=1, column=0, sticky=tk.W, pady=5)
        out_entry = ttk.Entry(file_frame, textvariable=self.output_dir_path, width=50)
        out_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        browse_out_btn = ttk.Button(file_frame, text="Examinar...", command=self._browse_output_dir)
        browse_out_btn.grid(row=1, column=2, pady=5)

        file_frame.columnconfigure(1, weight=1)

        # Options Section
        options_frame = ttk.LabelFrame(main_frame, text=" Opciones de Procesamiento ", padding="10 10 10 10")
        options_frame.pack(fill=tk.X, pady=(0, 10))

        cb_chapters = ttk.Checkbutton(
            options_frame,
            text="Separar texto por capítulos en archivos individuales (en carpeta reservada del libro)",
            variable=self.split_chapters_var
        )
        cb_chapters.pack(anchor=tk.W, pady=2)

        cb_dialogues = ttk.Checkbutton(
            options_frame,
            text="Eliminar guiones de diálogo iniciales y convertir acotaciones en pausas naturales (comas)",
            variable=self.clean_dialogues_var
        )
        cb_dialogues.pack(anchor=tk.W, pady=2)

        cb_paragraphs = ttk.Checkbutton(
            options_frame,
            text="Unificar párrafos y eliminar sangrías/saltos de línea innecesarios",
            variable=self.merge_paragraphs_var
        )
        cb_paragraphs.pack(anchor=tk.W, pady=2)

        cb_hyphens = ttk.Checkbutton(
            options_frame,
            text="Unir palabras divididas por guion al final de línea (ej. progra-ma -> programa)",
            variable=self.fix_hyphens_var
        )
        cb_hyphens.pack(anchor=tk.W, pady=2)

        cb_headers = ttk.Checkbutton(
            options_frame,
            text="Detectar y eliminar encabezados, pies de página y números de página",
            variable=self.remove_headers_var
        )
        cb_headers.pack(anchor=tk.W, pady=2)

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
            text="⚡ Convertir a AudioTexto (.txt)",
            command=self._start_conversion
        )
        self.convert_btn.pack(pady=(0, 10), ipady=5, fill=tk.X)

        # Log Text Box
        log_frame = ttk.LabelFrame(main_frame, text=" Registro de Procesamiento ", padding="5 5 5 5")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=8, font=("Consolas", 8))
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

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
        """Processes events queued by background threads in the main Tk thread."""
        while not self.event_queue.empty():
            try:
                event_type, args = self.event_queue.get_nowait()
                if event_type == "progress":
                    status, val = args
                    self._update_progress(status, val)
                elif event_type == "success":
                    folder, count = args
                    self._conversion_success(folder, count)
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

        options = {
            "split_chapters": self.split_chapters_var.get(),
            "fix_hyphens": self.fix_hyphens_var.get(),
            "clean_dialogues": self.clean_dialogues_var.get(),
            "merge_paragraphs": self.merge_paragraphs_var.get(),
            "remove_headers_footers": self.remove_headers_var.get(),
        }

        self.convert_btn.config(state=tk.DISABLED)
        self.log_text.delete("1.0", tk.END)
        self.progress_bar["value"] = 0

        # Run conversion in background thread
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
                progress_callback=lambda status, val: self.event_queue.put(("progress", (status, val)))
            )

            folder = result["folder"]
            files = result["files"]

            self.event_queue.put(("success", (folder, len(files))))
        except Exception as e:
            self.event_queue.put(("error", str(e)))

    def _conversion_success(self, folder: str, file_count: int):
        self.convert_btn.config(state=tk.NORMAL)
        self._log(f"\n✅ ¡Éxito! Se crearon {file_count} archivo(s) en la carpeta:\n{folder}")
        messagebox.showinfo(
            "Conversión Completada",
            f"Se han generado {file_count} archivo(s) .txt con éxito en:\n\n{folder}"
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
