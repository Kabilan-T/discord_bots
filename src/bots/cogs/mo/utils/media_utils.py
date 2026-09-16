#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Fit media files within Discord's attachment size limit by splitting long videos and compressing what's still too big '''

#-------------------------------------------------------------------------------

import os
import math
import glob
import subprocess
from PIL import Image

target_part_size = 22 * 1024 * 1024  # slightly under Discord's 25MB cap, leaves margin for container overhead
min_segment_duration = 30  # seconds - never split a video into a segment shorter than this

def get_video_duration(file_path) -> float:
    ''' Get the duration of a video file in seconds using ffprobe '''
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', file_path],
        capture_output=True, text=True)
    return float(result.stdout.strip())

def compress_video(file_path, target_size) -> str:
    ''' Compress a video to fit within target_size bytes (two-pass bitrate encode, downscales if needed) '''
    duration = get_video_duration(file_path)
    audio_bitrate = 128_000  # bps - reserved from the budget below, not added on top of it
    total_bitrate = target_size * 8 * 0.9 / duration  # 0.9 margin for container overhead
    video_bitrate = max(int(total_bitrate - audio_bitrate), 100_000)
    scale_args = ['-vf', 'scale=-2:720'] if video_bitrate < 1_000_000 else []
    output_path = file_path.replace('.mp4', '_compressed.mp4')
    for pass_num in (1, 2):
        pass_args = ['-b:v', str(video_bitrate), '-pass', str(pass_num)]
        audio_args = ['-an'] if pass_num == 1 else ['-c:a', 'aac', '-b:a', str(audio_bitrate)]
        destination = os.devnull if pass_num == 1 else output_path
        subprocess.run(['ffmpeg', '-y', '-i', file_path, *scale_args, *pass_args,
                        *audio_args, '-f', 'mp4', destination], capture_output=True)
    return output_path

def split_video(file_path, num_parts) -> list:
    ''' Split a video into num_parts roughly-equal segments without re-encoding '''
    duration = get_video_duration(file_path)
    segment_time = duration / num_parts
    output_pattern = file_path.replace('.mp4', '_part%d.mp4')
    subprocess.run(['ffmpeg', '-y', '-i', file_path, '-c', 'copy', '-f', 'segment',
                    '-segment_time', str(segment_time), '-reset_timestamps', '1', output_pattern],
                   capture_output=True)
    return sorted(glob.glob(file_path.replace('.mp4', '_part*.mp4')))

def compress_image(file_path, target_size) -> str:
    ''' Compress an image to fit within target_size bytes by reducing quality, then dimensions '''
    image = Image.open(file_path).convert('RGB')
    for quality in (85, 75, 65, 50, 35):
        image.save(file_path, quality=quality)
        if os.path.getsize(file_path) <= target_size:
            return file_path
    while os.path.getsize(file_path) > target_size:
        image = image.resize((image.width // 2, image.height // 2))
        image.save(file_path, quality=35)
    return file_path

def get_media_parts(file_path, max_size) -> list:
    ''' Fit a media file within max_size bytes, splitting long videos and compressing what's still too big '''
    if os.path.getsize(file_path) <= max_size:
        return [file_path]
    if not file_path.lower().endswith('.mp4'):
        return [compress_image(file_path, max_size)]
    duration = get_video_duration(file_path)
    num_parts = min(math.ceil(os.path.getsize(file_path) / target_part_size),
                    max(1, int(duration // min_segment_duration)))
    if num_parts == 1:
        return [compress_video(file_path, max_size)]
    parts = split_video(file_path, num_parts)
    return [part if os.path.getsize(part) <= max_size else compress_video(part, max_size) for part in parts]
