#!/usr/bin/env python3
"""Quick script to check available cameras."""

from lerobot.cameras.opencv.camera_opencv import OpenCVCamera
import json

try:
    cams = OpenCVCamera.find_cameras()
    print(json.dumps([{'id': c['id'], 'name': c['name']} for c in cams], indent=2))
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
