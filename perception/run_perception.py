#!/usr/bin/env python3
"""
Run standalone perception: ArUco table frame + 3D object positions.
Usage:
  python -m perception.run_perception --image path/to/image.png --config-dir .
  python -m perception.run_perception --camera 0 --config-dir .
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

# Run from standalone dir or repo root
_SCRIPT_DIR = Path(__file__).resolve().parent
if _SCRIPT_DIR.name == "perception":
    _CONFIG_DIR = _SCRIPT_DIR.parent / "config"
else:
    _CONFIG_DIR = _SCRIPT_DIR / "config"

from .camera_config import load_camera_intrinsics
from .aruco_table import load_aruco_config
from .detector import ContourBlobDetector
from .pipeline import run_perception, Object3D


def _load_table_base_transform(path: Path) -> tuple[np.ndarray, np.ndarray] | None:
    """Load translation (3,) and quaternion (4,) from YAML. Returns None if file missing."""
    if not path.is_file():
        return None
    import yaml
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    t = data.get("translation", {})
    r = data.get("rotation", {})
    trans = np.array([
        float(t.get("x", 0)), float(t.get("y", 0)), float(t.get("z", 0))
    ], dtype=np.float64)
    q = np.array([
        float(r.get("x", 0)), float(r.get("y", 0)),
        float(r.get("z", 0)), float(r.get("w", 1))
    ], dtype=np.float64)
    return trans, q


def _quat_to_rotation_matrix(q: np.ndarray) -> np.ndarray:
    x, y, z, w = q[0], q[1], q[2], q[3]
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    return np.array([
        [1 - 2 * (yy + zz), 2 * (xy - wz), 2 * (xz + wy)],
        [2 * (xy + wz), 1 - 2 * (xx + zz), 2 * (yz - wx)],
        [2 * (xz - wy), 2 * (yz + wx), 1 - 2 * (xx + yy)],
    ], dtype=np.float64)


def table_to_base(
    trans: np.ndarray, quat: np.ndarray, x: float, y: float, z: float
) -> tuple[float, float, float]:
    R = _quat_to_rotation_matrix(quat)
    p = np.array([x, y, z], dtype=np.float64)
    out = R @ p + trans
    return float(out[0]), float(out[1]), float(out[2])


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Perception: ArUco table frame + 3D object positions on the table.",
    )
    parser.add_argument(
        "--image",
        type=Path,
        help="Path to a single image (BGR).",
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=None,
        help="Camera device index (e.g. 0). If set, captures one frame.",
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=_CONFIG_DIR,
        help="Directory containing camera_intrinsics.yaml and aruco_table.yaml",
    )
    parser.add_argument(
        "--table-base",
        type=Path,
        default=None,
        help="Optional YAML with table->base_link transform (translation + rotation quat).",
    )
    parser.add_argument(
        "--detector",
        choices=["blob", "aruco"],
        default="blob",
        help="Object detector: blob (color contours) or aruco (markers on objects).",
    )
    parser.add_argument(
        "--blob-hsv",
        type=str,
        default="0,50,50:30,255,255",
        help="For blob detector: lower_h,s,v:upper_h,s,v (e.g. 0,50,50:30,255,255 for orange).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write JSON array of {x,y,z,yaw} (table frame) or {x,y,z,yaw,base_x,base_y,base_z} to this file.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show image with detected marker and object centers (press key to close).",
    )
    args = parser.parse_args()

    if (args.image is None) == (args.camera is None):
        print("Use exactly one of --image or --camera.", file=sys.stderr)
        return 1

    config_dir = args.config_dir
    cam_path = config_dir / "camera_intrinsics.yaml"
    aruco_path = config_dir / "aruco_table.yaml"
    if not cam_path.is_file():
        print(f"Missing {cam_path}", file=sys.stderr)
        return 1
    if not aruco_path.is_file():
        print(f"Missing {aruco_path}", file=sys.stderr)
        return 1

    intrinsics = load_camera_intrinsics(cam_path)
    aruco_cfg = load_aruco_config(aruco_path)

    if args.detector == "blob":
        hsv_parts = args.blob_hsv.split(":")
        if len(hsv_parts) != 2:
            print("--blob-hsv must be lower:upper (e.g. 0,50,50:30,255,255)", file=sys.stderr)
            return 1
        lo = [int(x) for x in hsv_parts[0].split(",")]
        hi = [int(x) for x in hsv_parts[1].split(",")]
        detector = ContourBlobDetector(tuple(lo), tuple(hi))
    else:
        # ArUco object detector: use config marker_ids if present, else default
        marker_ids = aruco_cfg.get("object_marker_ids", [1, 2, 3])
        from .detector import ArUcoObjectDetector
        detector = ArUcoObjectDetector(
            marker_ids=marker_ids,
            marker_size_m=aruco_cfg.get("object_marker_size_m", 0.02),
            dict_name=aruco_cfg.get("dictionary", "DICT_4X4_50"),
        )

    if args.image is not None:
        image = cv2.imread(str(args.image))
        if image is None:
            print(f"Failed to read image: {args.image}", file=sys.stderr)
            return 1
    else:
        cap = cv2.VideoCapture(args.camera)
        if not cap.isOpened():
            print(f"Could not open camera {args.camera}", file=sys.stderr)
            return 1
        ok, image = cap.read()
        cap.release()
        if not ok or image is None:
            print("Failed to capture frame.", file=sys.stderr)
            return 1

    table, objects_3d = run_perception(image, intrinsics, aruco_cfg, detector)

    if table is None:
        print("Table ArUco marker not detected.", file=sys.stderr)
        if args.show:
            cv2.imshow("perception", image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        return 1

    tf_base = None
    if args.table_base:
        tf_base = _load_table_base_transform(args.table_base)

    out_list = []
    for obj in objects_3d:
        entry = {"x": obj.x, "y": obj.y, "z": obj.z, "yaw": obj.yaw}
        if tf_base is not None:
            bx, by, bz = table_to_base(tf_base[0], tf_base[1], obj.x, obj.y, obj.z)
            entry["base_x"] = bx
            entry["base_y"] = by
            entry["base_z"] = bz
        out_list.append(entry)

    print(json.dumps(out_list, indent=2))
    if args.output is not None:
        args.output.write_text(json.dumps(out_list, indent=2))
        print(f"Wrote {args.output}", file=sys.stderr)

    if args.show:
        vis = image.copy()
        # Draw table marker center
        cx, cy = [int(round(c)) for c in table.marker_center_pixel]
        cv2.circle(vis, (cx, cy), 10, (0, 255, 0), 2)
        cv2.putText(vis, "table", (cx + 12, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0))
        # Draw object 3D positions by re-projecting (we'd need to project table x,y,0 to pixel; skip for simplicity or add)
        cv2.imshow("perception", vis)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    sys.exit(main())
