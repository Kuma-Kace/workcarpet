import os
import unittest
from src.textaloud_integration import find_textaloud_executable, get_installed_sapi5_voices, generate_audio_with_textaloud


class TestTextAloudIntegration(unittest.TestCase):

    def test_find_textaloud_executable_non_windows(self):
        # On Linux/macOS, find_textaloud_executable should safely return None
        if os.name != 'nt':
            self.assertIsNone(find_textaloud_executable())

    def test_get_installed_sapi5_voices_non_windows(self):
        if os.name != 'nt':
            self.assertEqual(get_installed_sapi5_voices(), [])

    def test_generate_audio_with_missing_textaloud_exe(self):
        with self.assertRaises(FileNotFoundError):
            generate_audio_with_textaloud("Texto de prueba", "output.mp3", ta_executable_path="/path/non_existent.exe")


if __name__ == '__main__':
    unittest.main()
