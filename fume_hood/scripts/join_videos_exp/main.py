#!/usr/bin/env python3

import sys
from moviepy import VideoFileClip, concatenate_videoclips


def join_videos(video_paths, output_path="joined_video.mp4"):
    try:
        clips = [VideoFileClip(path) for path in video_paths]
        final_clip = concatenate_videoclips(clips, method="compose")
        final_clip.write_videofile(
            output_path, codec="libx264", audio_codec="aac")
        print(f"✅ Joined video saved as: {output_path}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: python join_videos.py video1.mp4 video2.mp4 [video3.mp4 ...]")
    else:
        video_files = sys.argv[1:]
        join_videos(video_files)
