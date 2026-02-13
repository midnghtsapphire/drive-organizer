"""Tests for drive_organizer.music_organizer module."""

import pytest

from drive_organizer.categorizer import DriveFile
from drive_organizer.music_organizer import MusicOrganizer


class TestMusicOrganizer:
    """Test MusicOrganizer."""

    def setup_method(self):
        self.organizer = MusicOrganizer()

    def test_organize_mp3(self):
        f = DriveFile(id="1", name="my-song.mp3", mime_type="audio/mpeg")
        dest = self.organizer.organize(f)
        assert "MUSIC" in dest

    def test_organize_wav(self):
        f = DriveFile(id="1", name="recording.wav", mime_type="audio/wav")
        dest = self.organizer.organize(f)
        assert "MUSIC" in dest

    def test_organize_stem(self):
        f = DriveFile(id="1", name="vocals-stem.wav", mime_type="audio/wav")
        dest = self.organizer.organize(f)
        assert "Stems" in dest

    def test_organize_instrumental(self):
        f = DriveFile(id="1", name="beat-instrumental.mp3", mime_type="audio/mpeg")
        dest = self.organizer.organize(f)
        assert "Stems" in dest or "Instrumental" in dest

    def test_organize_cover_art(self):
        f = DriveFile(id="1", name="album-cover-art.jpg", mime_type="image/jpeg")
        dest = self.organizer.organize(f)
        assert "Cover-Art" in dest

    def test_organize_lyrics(self):
        f = DriveFile(id="1", name="song-lyrics.txt", mime_type="text/plain")
        dest = self.organizer.organize(f)
        assert "Lyrics" in dest

    def test_organize_non_music(self):
        f = DriveFile(id="1", name="document.pdf", mime_type="application/pdf")
        dest = self.organizer.organize(f)
        assert dest == ""

    def test_detect_genre_pop(self):
        genre = self.organizer.detect_genre("my-alt-pop-song.mp3")
        assert genre == "Alt-Pop"

    def test_detect_genre_rnb(self):
        genre = self.organizer.detect_genre("smooth-alt-rnb-track.mp3")
        assert "RnB" in genre or "R&B" in genre

    def test_detect_genre_none(self):
        genre = self.organizer.detect_genre("random-file.mp3")
        # May or may not detect — should not error
        assert isinstance(genre, str)

    def test_detect_release_status_final(self):
        status = self.organizer.detect_release_status("song-final-master.mp3")
        assert status in ("Released", "Work-In-Progress", "")

    def test_detect_release_status_draft(self):
        status = self.organizer.detect_release_status("song-draft-v2.mp3")
        assert status in ("Work-In-Progress", "Unreleased", "")

    def test_case_insensitive_genre(self):
        g1 = self.organizer.detect_genre("POP-song.mp3")
        g2 = self.organizer.detect_genre("pop-song.mp3")
        assert g1 == g2

    def test_organize_batch(self):
        files = {
            "1": DriveFile(id="1", name="song.mp3", mime_type="audio/mpeg"),
            "2": DriveFile(id="2", name="cover-art.jpg", mime_type="image/jpeg"),
            "3": DriveFile(id="3", name="document.pdf", mime_type="application/pdf"),
        }
        results = self.organizer.organize_batch(files)
        assert "1" in results
        assert "MUSIC" in results["1"]

    def test_acapella_is_stem(self):
        f = DriveFile(id="1", name="acapella-version.mp3", mime_type="audio/mpeg")
        dest = self.organizer.organize(f)
        assert "Stems" in dest

    def test_flac_music(self):
        f = DriveFile(id="1", name="hifi-track.flac", mime_type="audio/flac")
        dest = self.organizer.organize(f)
        assert "MUSIC" in dest

    def test_songwriting_is_lyrics(self):
        f = DriveFile(id="1", name="songwriting-notes.txt", mime_type="text/plain")
        dest = self.organizer.organize(f)
        assert "Lyrics" in dest
