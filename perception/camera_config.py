"""Load camera intrinsics from YAML and provide unprojection / ray-plane intersection."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np
import yaml


@dataclass
class CameraIntrinsics:
    """Camera matrix and distortion for pinhole model."""

    K: np.ndarray  # 3x3
    D: np.ndarray  # dist_coeffs (1x4, 1x5, or 1x8)


def load_camera_intrinsics(path: Path) -> CameraIntrinsics:
    """Load from YAML with keys camera_matrix (3x3) and dist_coeffs (list)."""
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    K_list = data.get("camera_matrix")
    if K_list is None or len(K_list) != 3 or any(len(row) != 3 for row in K_list):
        raise ValueError("camera_intrinsics YAML must contain a 3x3 'camera_matrix'")
    K = np.array(K_list, dtype=np.float64)
    D_list = data.get("dist_coeffs", [])
    D = np.array(D_list, dtype=np.float64).ravel()
    return CameraIntrinsics(K=K, D=D)


def unproject_pixel(
    intrinsics: CameraIntrinsics, u: float, v: float, normalize: bool = True
) -> np.ndarray:
    """Unproject a pixel to a unit ray in camera frame (origin at camera)."""
    K = intrinsics.K
    fx, fy = K[0, 0], K[1, 1]
    cx, cy = K[0, 2], K[1, 2]
    x = (u - cx) / fx
    y = (v - cy) / fy
    ray = np.array([x, y, 1.0], dtype=np.float64)
    if normalize:
        ray /= np.linalg.norm(ray)
    return ray


def undistort_point(
    intrinsics: CameraIntrinsics, u: float, v: float
) -> Tuple[float, float]:
    """Undistort a single pixel; returns (u', v') in normalized pinhole coords scale."""
    pt = np.array([[[u, v]]], dtype=np.float32)
    out = cv2.undistortPoints(
        pt, intrinsics.K, intrinsics.D, None, None, intrinsics.K
    )
    return float(out[0, 0, 0]), float(out[0, 0, 1])


def ray_plane_intersection(
    ray_origin: np.ndarray,
    ray_direction: np.ndarray,
    plane_origin: np.ndarray,
    plane_normal: np.ndarray,
) -> np.ndarray | None:
    """Intersect ray with plane. Returns 3D point in same frame as inputs, or None if parallel."""
    n = np.asarray(plane_normal, dtype=np.float64)
    n = n / np.linalg.norm(n)
    denom = np.dot(ray_direction, n)
    if abs(denom) < 1e-9:
        return None
    t = np.dot(plane_origin - ray_origin, n) / denom
    if t < 0:
        return None
    return np.asarray(ray_origin + t * ray_direction, dtype=np.float64)


