import unittest
from src.text_cleaner import (
    fix_hyphenated_words,
    clean_dialogue_dashes,
    join_paragraphs,
    remove_headers_footers_and_page_numbers,
    clean_text_for_textaloud
)
from src.pdf_processor import detect_chapters, sanitize_filename


class TestTextCleaner(unittest.TestCase):

    def test_fix_hyphenated_words(self):
        text = "Esta es una palabra compa-\nñero dividida."
        expected = "Esta es una palabra compañero dividida."
        self.assertEqual(fix_hyphenated_words(text), expected)

        text_emdash = "Otra palabra especial—\nmente difícil."
        expected_emdash = "Otra palabra especialmente difícil."
        self.assertEqual(fix_hyphenated_words(text_emdash), expected_emdash)

    def test_clean_dialogue_dashes(self):
        # Opening dialogue dash
        text1 = "— Hola, ¿cómo estás?"
        self.assertEqual(clean_dialogue_dashes(text1), "Hola, ¿cómo estás?")

        # Dialogue with double dash narrator incise
        text2 = "—Hola —dijo Juan—, pasa por favor."
        cleaned2 = clean_dialogue_dashes(text2)
        self.assertNotIn("—", cleaned2)
        self.assertEqual(cleaned2, "Hola, dijo Juan, pasa por favor.")

        # Single dash at end of sentence
        text3 = "—Hola —dijo María."
        cleaned3 = clean_dialogue_dashes(text3)
        self.assertNotIn("—", cleaned3)
        self.assertEqual(cleaned3, "Hola, dijo María.")

    def test_join_paragraphs(self):
        text = "Este es un párrafo que continúa\nen la siguiente línea sin punto final\ny luego hay una línea nueva que sigue."
        joined = join_paragraphs(text)
        self.assertEqual(joined, "Este es un párrafo que continúa en la siguiente línea sin punto final y luego hay una línea nueva que sigue.")

    def test_remove_headers_footers_and_page_numbers(self):
        pages = [
            "Don Quijote de la Mancha\nPágina 1\nEn un lugar de la Mancha...\nEditorial Castalia",
            "Don Quijote de la Mancha\nPágina 2\nde cuyo nombre no quiero acordarme...\nEditorial Castalia",
            "Don Quijote de la Mancha\nPágina 3\nno ha mucho tiempo que vivía...\nEditorial Castalia"
        ]
        cleaned = remove_headers_footers_and_page_numbers(pages)
        for page in cleaned:
            self.assertNotIn("Don Quijote de la Mancha", page)
            self.assertNotIn("Editorial Castalia", page)
            self.assertNotIn("Página", page)

    def test_detect_chapters(self):
        text = "Capítulo I\nHabía una vez un hidalgo.\n\nCapítulo II\nLas aventuras del hidalgo."
        chapters = detect_chapters(text)
        self.assertEqual(len(chapters), 2)
        self.assertEqual(chapters[0][0], "Capítulo I")
        self.assertEqual(chapters[1][0], "Capítulo II")

    def test_sanitize_filename(self):
        self.assertEqual(sanitize_filename("Capítulo 1: ¿El Inicio?"), "Capítulo_1_El_Inicio")


if __name__ == '__main__':
    unittest.main()
