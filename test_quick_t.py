import tempfile
import unittest
from pathlib import Path

from Quick_T import SPEED_BEAM_SIZES as CLI_SPEED_BEAM_SIZES
from Quick_T import safe_filename, unique_output_path
from Quick_T_gui import SPEED_BEAM_SIZES as GUI_SPEED_BEAM_SIZES
from Quick_T_gui import is_youtube_url, unique_path


class FilenameTests(unittest.TestCase):
    def test_cli_filename_removes_cross_platform_invalid_characters(self):
        self.assertEqual(safe_filename('A/B:C?'), 'A_B_C_')

    def test_cli_filename_avoids_windows_reserved_names(self):
        self.assertEqual(safe_filename('CON'), '_CON')

    def test_cli_output_name_is_unique(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / 'Cours.txt').write_text('existant', encoding='utf-8')
            self.assertEqual(unique_output_path(folder, 'Cours').name, 'Cours_2.txt')

    def test_gui_output_name_is_unique(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / 'Cours.txt').write_text('existant', encoding='utf-8')
            self.assertEqual(Path(unique_path(directory, 'Cours')).name, 'Cours_2.txt')


class SpeedPresetTests(unittest.TestCase):
    def test_fast_profile_uses_greedy_decoding(self):
        self.assertEqual(GUI_SPEED_BEAM_SIZES["Rapide"], 1)
        self.assertEqual(CLI_SPEED_BEAM_SIZES["rapide"], 1)

    def test_quality_profiles_use_larger_beam_sizes(self):
        self.assertEqual(GUI_SPEED_BEAM_SIZES["Équilibré"], 3)
        self.assertEqual(GUI_SPEED_BEAM_SIZES["Précis"], 5)
        self.assertEqual(CLI_SPEED_BEAM_SIZES["equilibre"], 3)
        self.assertEqual(CLI_SPEED_BEAM_SIZES["precis"], 5)


class UrlValidationTests(unittest.TestCase):
    def test_accepts_youtube_hosts(self):
        for url in ('https://youtube.com/watch?v=abc', 'https://www.youtube.com/watch?v=abc', 'https://youtu.be/abc'):
            with self.subTest(url=url):
                self.assertTrue(is_youtube_url(url))

    def test_rejects_unrelated_or_unsafe_urls(self):
        for url in ('https://example.com/watch?v=abc', 'file:///etc/passwd', 'javascript:alert(1)', 'not a url'):
            with self.subTest(url=url):
                self.assertFalse(is_youtube_url(url))


if __name__ == '__main__':
    unittest.main()
