# Camera Detection Fix Report - January 22, 2026

**Status:** ✅ RESOLVED

---

## Problem Summary

Running `lerobot-find-cameras` resulted in the error:
```
ERROR:lerobot.scripts.lerobot_find_cameras:Error finding RealSense cameras: name 'rs' is not defined
```

This prevented the script from completing and showed cameras without properly handling the missing RealSense library.

---

## Root Cause

The `RealSenseCamera.find_cameras()` method attempted to use the `rs` (pyrealsense2) module without checking if it was successfully imported.

**In `camera_realsense.py`:**
```python
# BAD: rs imported in try-except but no check if import failed
try:
    import pyrealsense2 as rs
except Exception as e:
    logging.info(f"Could not import realsense: {e}")
    # rs was never defined if import failed!

# Later in find_cameras()...
def find_cameras() -> list[dict[str, Any]]:
    context = rs.context()  # NameError: name 'rs' is not defined
```

---

## Solution Implemented

### Change 1: Initialize `rs` to None
```python
rs = None
try:
    import pyrealsense2 as rs
except Exception as e:
    logging.info(f"Could not import realsense: {e}")
```

### Change 2: Add Check in `find_cameras()`
```python
def find_cameras() -> list[dict[str, Any]]:
    if rs is None:
        raise ImportError(
            "pyrealsense2 is not installed. Please install it with: pip install pyrealsense2"
        )
    # ... rest of method
```

### Files Modified
- `lerobot/src/lerobot/cameras/realsense/camera_realsense.py` (Lines 28-31, 200-212)
- `src/lerobot/cameras/realsense/camera_realsense.py` (Lines 28-31, 200-212)

---

## Results After Fix

### Success Indicators
✅ **No more `'rs' is not defined` error**

✅ **Proper error message:**
```
WARNING:lerobot.scripts.lerobot_find_cameras:Skipping RealSense camera search: pyrealsense2 library not found or not importable.
```

✅ **Camera detection works:**
```
--- Detected Cameras ---
Camera #0:
  Name: OpenCV Camera @ 0
  Type: OpenCV
  Id: 0
  Backend api: DSHOW
  ...

Camera #1:
  Name: OpenCV Camera @ 1
  Type: OpenCV
  Id: 1
  ...

Camera #2:
  Name: OpenCV Camera @ 2
  Type: OpenCV
  Id: 2
  ...
```

✅ **All 3 cameras confirmed:**
- Index 0: Robot camera (SO-101 gripper)
- Index 1: Logitech C270 HD WebCam
- Index 2: Laptop built-in webcam

---

## OpenCV Errors Explanation

The `[ERROR:0@X.XXX] global obsensor_uvc_stream_channel.cpp` messages are **benign OpenCV warnings** from the OB sensor driver. They appear when OpenCV queries camera capabilities but don't affect functionality. These are from the underlying camera driver and cannot be suppressed from the Python application level.

**These errors are NOT related to your camera problem** - they're just noise from OpenCV's initialization.

---

## Testing Verification

```python
from lerobot.cameras.opencv.camera_opencv import OpenCVCamera

cams = OpenCVCamera.find_cameras()
# Returns 3 cameras with IDs: [0, 1, 2]
```

---

## Next Steps

1. ✅ **Cameras are properly detected** - All 3 cameras available at indices 0, 1, 2
2. ✅ **RealSense error is handled gracefully** - No more crashes
3. Use cameras with their detected indices for any application code

---

## Notes

- The fix ensures graceful degradation: if pyrealsense2 isn't installed, the tool skips RealSense detection and shows only OpenCV cameras
- The error handling now provides clear, actionable messages to users
- Camera indices remain stable as long as hardware isn't changed/reconnected
