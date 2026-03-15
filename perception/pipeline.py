"""Run perception: detect table frame (ArUco) and object 3D positions on the table."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import numpy as np

from .aruco_table import (
    TableFrame,
    detect_table_frame,
    load_aruco_config,
    pixel_to_table_3d,
)
from .camera_config import CameraIntrinsics, load_camera_intrinsics
from .detector import Detection, ObjectDetector


@dataclass
class Object3D:
    """Object position in table frame (meters)."""

    x: float
    y: float
    z: float
    yaw: float = 0.0  # in table plane, radians


def run_perception(
    image: np.ndarray,
    intrinsics: CameraIntrinsics,
    aruco_cfg: dict,
    detector: ObjectDetector,
) -> tuple[Optional[TableFrame], List[Object3D]]:
    """
    Detect table frame from ArUco and object 3D positions.
    Returns (table_frame or None if marker not seen, list of Object3D in table frame).
    """
    table = detect_table_frame(
        image,
        intrinsics,
        marker_id=aruco_cfg["marker_id"],
        marker_size_m=aruco_cfg["marker_size_m"],
        dict_name=aruco_cfg.get("dictionary", "DICT_4X4_50"),
    )
    if table is None:
        return None, []

    detections: List[Detection] = detector.detect(image)
    camera_origin = np.zeros(3, dtype=np.float64)
    objects_3d: List[Object3D] = []
    for d in detections:
        pt = pixel_to_table_3d(
            d.u, d.v, table, intrinsics, camera_origin
        )
        if pt is None:
            continue
        x_t, y_t, z_t = pt
        objects_3d.append(Object3D(x=x_t, y=y_t, z=z_t, yaw=d.yaw))
    return table, objects_3d
