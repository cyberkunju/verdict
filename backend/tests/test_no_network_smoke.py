from services.archive_service import load_archive_clips


def test_archive_loads_without_network() -> None:
    clips = load_archive_clips()
    assert isinstance(clips, list)
    assert all("clip_id" in clip for clip in clips)
