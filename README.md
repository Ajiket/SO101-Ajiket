# SO-101 Imitation Learning

End-to-end imitation learning on a pair of SO-101 arms (leader + follower): teleoperated demonstrations, dataset recording, ACT policy training with [Hugging Face LeRobot](https://github.com/huggingface/lerobot), and inference on the real hardware.

Demo video: _(coming soon — placeholder)_
Policy on Hugging Face: **[Ajiket/whistle_pick_place_ACT](https://huggingface.co/Ajiket/whistle_pick_place_ACT)**
Reported success rate: _(coming soon — placeholder, N/N trials)_

## Task

Pick up a whistle from the workspace and place it in a bin. Fixed workspace, two cameras (gripper view + overhead Logitech).

## Hardware setup

Two SO-101 arms (open-source robotic arm supported by [LeRobot](https://github.com/huggingface/lerobot)):

- **Leader arm** (`so101_leader`) — human-driven, teaches motions.
- **Follower arm** (`so101_follower`) — mirrors the leader during teleoperation, executes the policy during inference.
- Feetech STS3215 servo motors on both arms.
- Two USB cameras: Logitech C270 (overhead) and a small USB camera mounted near the gripper.
- Two FE-URT-1 motor-bus boards (one per arm), connected to the PC over USB-serial (`COM4`, `COM5` on Windows).

See [`Opening_docs/`](Opening_docs/) for photos of the hardware as it arrived — leader arm, follower arm, PCBs, servo motor, power adapters, cables and C-clamps.

### Hardware BOM

| Qty | Item | Notes |
|---:|---|---|
| 1 | SO-101 leader arm (teleoperation master) | 6 Feetech STS3215 servos |
| 1 | SO-101 follower arm (robot) | 6 Feetech STS3215 servos |
| 2 | FE-URT-1 motor-bus board | one per arm, USB-serial |
| 1 | Logitech C270 HD WebCam | overhead workspace view |
| 1 | USB webcam, small form factor | mounted at gripper |
| 2 | 12 V DC power adapter | one per arm |
| — | USB-A cables, Type-C data cables, C-clamps | for mounting and comms |

## Workflow

### 1. Install LeRobot

Follow the upstream install guide: <https://github.com/huggingface/lerobot>. Create a dedicated conda or venv environment.

### 2. Verify the cameras

```powershell
python scripts/check_cameras.py
```

Prints the index and name of every OpenCV-visible camera so you can map `index_or_path` correctly in the teleop/record configs. If this fails, see [`docs/camera_detection_fix.md`](docs/camera_detection_fix.md).

### 3. Calibrate each arm

Both arms must be calibrated once per build. Calibration files land in `~/.cache/huggingface/lerobot/calibration/`.

```powershell
lerobot-teleoperate ^
  --robot.type=so101_follower --robot.port=COM5 --robot.id=my_follower_arm ^
  --teleop.type=so101_leader   --teleop.port=COM4 --teleop.id=my_leader_arm
```

On the first run per arm, LeRobot steps through: *move to centre → sweep each joint through its full range → save*. The follower then mirrors the leader at 60 Hz.

### 4. Record a dataset

```powershell
lerobot-record ^
  --robot.type=so101_follower --robot.port=COM5 --robot.id=my_follower_arm ^
  --teleop.type=so101_leader   --teleop.port=COM4 --teleop.id=my_leader_arm ^
  --robot.cameras="{gripper_camera: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30, fourcc: MJPG}, logitech_camera: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30, fourcc: MJPG}}" ^
  --dataset.repo_id=Ajiket/whistle_pick_place ^
  --dataset.num_episodes=50 ^
  --dataset.single_task="Pick up whistle and place in bin" ^
  --display_data=true
```

Each episode is 60 s. Reset the scene between episodes. The dataset is pushed to the Hugging Face Hub when the run finishes.

### 5. Train ACT

Trained upstream using LeRobot's `lerobot-train` with the ACT policy preset on the recorded dataset. The trained checkpoint is published as **[Ajiket/whistle_pick_place_ACT](https://huggingface.co/Ajiket/whistle_pick_place_ACT)**.

### 6. Run inference on the real arm

```powershell
lerobot-record ^
  --robot.type=so101_follower --robot.port=COM5 --robot.id=my_follower_arm ^
  --robot.cameras="{gripper_camera: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30, fourcc: MJPG}, logitech_camera: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30, fourcc: MJPG}}" ^
  --dataset.repo_id=Ajiket/eval-test --dataset.num_episodes=0 ^
  --dataset.single_task="Pick up whistle and place in bin" ^
  --policy.path=Ajiket/whistle_pick_place_ACT ^
  --policy.device=cpu
```

`--policy.device=cuda` if you have a GPU; `cpu` works but runs at a lower effective rate.

## Troubleshooting

Debug reports written while bringing up the hardware — the kind of thing that doesn't make it into a tutorial:

- [`docs/camera_setup_debug.md`](docs/camera_setup_debug.md) — Logitech camera "not opening" turned out to be hardcoded camera indices in test scripts not matching the real device enumeration order.
- [`docs/camera_detection_fix.md`](docs/camera_detection_fix.md) — `lerobot-find-cameras` crashing with `name 'rs' is not defined` when `pyrealsense2` isn't installed. Fixed the import guard.
- [`docs/camera_system_fixes.md`](docs/camera_system_fixes.md) — Consolidated camera-system fixes from the build-up phase.

Short list of other things I had to work around:

- **Motor timeout on Windows + USB hubs.** The default 1000 ms Feetech motor timeout dropped frames; 5000 ms is reliable.
- **OpenCV backend on Windows.** Passing an explicit `cv2.CAP_*` backend to `cv2.VideoCapture` fails silently; the default backend works.
- **Motor 5 (SO-101 leader, wrist-roll).** Hardware wiring quirk on the kit I received, worked around in software.

## Credits

- Robot platform and framework: [Hugging Face LeRobot](https://github.com/huggingface/lerobot).
- SO-101 fork and Windows-friendly tutorials: [Vizuara's LeRobot fork](https://github.com/Vizuara) — my local setup is built on top of that fork.
- ACT (Action Chunking with Transformers): Zhao et al., 2023, [ALOHA paper](https://arxiv.org/abs/2304.13705).

This repository contains **only my own documentation, debugging notes, utility script, and hardware photos**. The LeRobot source is not vendored here; install it from upstream.

## License

MIT (my files only). LeRobot upstream is Apache-2.0, consult that project for its own terms.
