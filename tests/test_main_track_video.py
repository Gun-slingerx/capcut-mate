"""CutFlow's video must land on Jianying's only main video track."""

import json
import subprocess
from pathlib import Path

import config
from src.service.create_draft import create_draft
from src.service.add_videos import _add_videos_internal
from src.utils.draft_cache import DRAFT_CACHE


def test_add_videos_to_main_track(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DRAFT_DIR", str(tmp_path / "drafts"))
    video_path = tmp_path / "clip.mp4"
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
         "color=c=black:s=64x112:d=1", "-c:v", "mpeg4", str(video_path)],
        check=True,
    )
    draft_url = create_draft(64, 112)
    draft_id = draft_url.split("draft_id=", 1)[1]
    video = {
        "video_url": "http://example.invalid/clip.mp4", "local_video_path": str(video_path),
        "start": 0, "end": 1_000_000, "duration": 1_000_000,
        "original_start": 0, "original_end": 1_000_000,
    }
    try:
        _add_videos_internal(draft_url, json.dumps([video]), prepared_videos=[video], use_main_track=True)
        content = json.loads((tmp_path / "drafts" / draft_id / "draft_content.json").read_text())
        tracks = [track for track in content["tracks"] if track["type"] == "video"]
        assert len(tracks) == 1
        assert tracks[0]["name"] == "main_track"
        assert len(tracks[0]["segments"]) == 1
        assert len(content["materials"]["videos"]) == 1
    finally:
        DRAFT_CACHE.pop(draft_id, None)
