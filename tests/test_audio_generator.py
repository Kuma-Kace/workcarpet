import os
import unittest
from src.audio_generator import get_available_voices, SPANISH_VOICES, DEFAULT_VOICE, generate_audio_from_text


class TestAudioGenerator(unittest.TestCase):

    def test_voices_dict(self):
        voices = get_available_voices()
        self.assertIn("Álvaro (España - Masculino)", voices)
        self.assertEqual(voices["Álvaro (España - Masculino)"], "es-ES-AlvaroNeural")
        self.assertEqual(DEFAULT_VOICE, "es-ES-AlvaroNeural")

    def test_generate_audio_empty_text(self):
        # Should return without exception
        generate_audio_from_text("", "test_output.mp3")
        self.assertFalse(os.path.exists("test_output.mp3"))


if __name__ == '__main__':
    unittest.main()
