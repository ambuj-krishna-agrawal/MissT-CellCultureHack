"""Detect ArUco marker on the table and compute camera-to-table transform and table plane."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np
import yaml

from .camera_config import CameraIntrinsics, load_camera_intrinsics


@dataclass
class TableFrame:
    """Table frame derived from one ArUco marker: origin at marker center, Z up."""

    T_cam_table: np.ndarray  # 4x4, camera -> table
    plane_origin_cam: np.ndarray  # 3D point on table plane, in camera frame
    plane_normal_cam: np.ndarray  # unit normal (e.g. Z of table in camera frame)
    marker_center_pixel: Tuple[float, float]  # for debugging


def _get_aruco_dict(dict_name: str) -> cv2.aruco.Dictionary:
    """Resolve ArUco dictionary from string, e.g. DICT_4X4_50."""
    aruco = cv2.aruco
    name_to_dict = {
        "DICT_4X4_50": aruco.DICT_4X4_50,
        "DICT_4X4_100": aruco.DICT_4X4_100,
        "DICT_4X4_250": aruco.DICT_4X4_250,
        "DICT_5X5_50": aruco.DICT_5X5_50,
        "DICT_6X6_50": aruco.DICT_6X6_50,
        "DICT_7X7_50": aruco.DICT_7X7_50,
    }
    if dict_name not in name_to_dict:
        raise ValueError(f"Unknown ArUco dict: {dict_name}. Choose from {list(name_to_dict)}")
    return aruco.getPredefinedDictionary(name_to_dict[dict_name])


def _marker_corners_object(marker_size_m: float) -> np.ndarray:
    """Four corners of the marker in marker frame (center at origin, Z up)."""
    s = marker_size_m / 2.0
    return np.array(
        [[-s, s, 0], [s, s, 0], [s, -s, 0], [-s, -s, 0]],
        dtype=np.float32,
    )


def detect_table_frame(
    image: np.ndarray,
    intrinsics: CameraIntrinsics,
    marker_id: int,
    marker_size_m: float,
    dict_name: str = "DICT_4X4_50",
) -> Optional[TableFrame]:
    """
    Detect the table ArUco marker and return table frame and plane in camera frame.
    Returns None if the marker is not detected.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    aruco_dict = _get_aruco_dict(dict_name)
    params = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(aruco_dict, params)
    corners, ids, _ = detector.detectMarkers(gray)

    if ids is None or len(ids) == 0:
        return None

    # Find the requested marker
    idx = None
    for i, mid in enumerate(ids.flatten()):
        if mid == marker_id:
            idx = i
            break
    if idx is None:
        return None

    corner_pixels = np.array(corners[idx], dtype=np.float32)
    obj_pts = _marker_corners_object(marker_size_m)

    success, rvec, tvec = cv2.solvePnP(
        obj_pts,
        corner_pixels,
        intrinsics.K,
        intrinsics.D,
        flags=cv2.SOLVEPNP_IPPE_SQUARE,
    )
    if not success:
        return None

    R, _ = cv2.Rodrigues(rvec)
    t = tvec.flatten()
    T_cam_table = np.eye(4)
    T_cam_table[:3, :3] = R
    T_cam_table[:3, 3] = t

    # Table plane in camera frame: origin at marker center, normal = table Z (third column of R)
    plane_origin_cam = t.copy()
    plane_normal_cam = R[:, 2].copy()
    plane_normal_cam /= np.linalg.norm(plane_normal_cam)

    # Marker center in image (for debugging)
    center_px = corner_pixels[0].mean(axis=0)
    marker_center_pixel = (float(center_px[0]), float(center_px[1]))

    return TableFrame(
        T_cam_table=T_cam_table,
        plane_origin_cam=plane_origin_cam,
        plane_normal_cam=plane_normal_cam,
        marker_center_pixel=marker_center_pixel,
    )


def pixel_to_table_3d(
    u: float,
    v: float,
    table: TableFrame,
    intrinsics: CameraIntrinsics,
    camera_origin: np.ndarray,
) -> Optional[Tuple[float, float, float]]:
    """
    Unproject pixel (u,v) to a ray, intersect with table plane, return point in table frame.
    camera_origin is [0,0,0] in camera frame. Returns (x_table, y_table, z_table); z_table is 0.
    """
    from .camera_config import unproject_pixel, ray_plane_intersection

    ray_dir = unproject_pixel(intrinsics, u, v, normalize=True)
    pt_cam = ray_plane_intersection(
        camera_origin,
        ray_dir,
        table.plane_origin_cam,
        table.plane_normal_cam,
    )
    if pt_cam is None:
        return None
    # T_cam_table: camera -> table, so p_table = R @ p_cam + t
    R = table.T_cam_table[:3, :3]
    t = table.T_cam_table[:3, 3]
    pt_table = R @ pt_cam + t
    return (float(pt_table[0]), float(pt_table[1]), float(pt_table[2]))


def load_aruco_config(path: Path) -> Dict[str, Any]:
    """Load ArUco table config: marker_id, marker_size_m, dictionary."""
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {
        "marker_id": int(data.get("marker_id", 0)),
        "marker_size_m": float(data.get("marker_size_m", 0.05)),
        "dictionary": str(data.get("dictionary", "DICT_4X4_50")),
    }
