"""Simple object detectors returning (u, v) or (u, v, yaw) for objects on the table."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Tuple

import cv2
import numpy as np


@dataclass
class Detection:
    """Single detection: pixel center and optional yaw in image (radians)."""

    u: float
    v: float
    yaw: float = 0.0


class ObjectDetector(ABC):
    """Base class for detectors that return list of (u, v, yaw)."""

    @abstractmethod
    def detect(self, image: np.ndarray) -> List[Detection]:
        """Return detections; (u, v) in pixel coords, yaw in radians (image plane)."""
        ...


class ContourBlobDetector(ObjectDetector):
    """
    Detect blobs by color (HSV range). Returns centroid and approximate yaw from ellipse.
    Use for colored objects or markers on the table (excluding the ArUco used for table frame).
    """

    def __init__(
        self,
        lower_hsv: Tuple[int, int, int],
        upper_hsv: Tuple[int, int, int],
        min_area: float = 100.0,
    ) -> None:
        self._lower = np.array(lower_hsv, dtype=np.uint8)
        self._upper = np.array(upper_hsv, dtype=np.uint8)
        self._min_area = min_area

    def detect(self, image: np.ndarray) -> List[Detection]:
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self._lower, self._upper)
        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        results: List[Detection] = []
        for cnt in contours:
            if cv2.contourArea(cnt) < self._min_area:
                continue
            M = cv2.moments(cnt)
            if M["m00"] == 0:
                continue
            cx = M["m10"] / M["m00"]
            cy = M["m01"] / M["m00"]
            yaw = 0.0
            if len(cnt) >= 5:
                (_, _), (_, _), angle = cv2.fitEllipse(cnt)
                yaw = float(np.deg2rad(angle))
            results.append(Detection(u=float(cx), v=float(cy), yaw=yaw))
        return results


class ArUcoObjectDetector(ObjectDetector):
    """
    Detect objects that have an ArUco marker on top (e.g. small marker on each flask).
    Returns center of marker in image and yaw from marker pose. Use a different
    marker ID than the table frame marker.
    """

    def __init__(
        self,
        marker_ids: List[int],
        marker_size_m: float,
        dict_name: str = "DICT_4X4_50",
    ) -> None:
        self._marker_ids = set(marker_ids)
        self._marker_size_m = marker_size_m
        self._dict_name = dict_name

    def detect(self, image: np.ndarray) -> List[Detection]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
        name_to_dict = {
            "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
            "DICT_4X4_100": cv2.aruco.DICT_4X4_100,
            "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
            "DICT_6X6_50": cv2.aruco.DICT_6X6_50,
        }
        dict_id = name_to_dict.get(self._dict_name, cv2.aruco.DICT_4X4_50)
        aruco_dict = cv2.aruco.getPredefinedDictionary(dict_id)
        params = cv2.aruco.DetectorParameters()
        detector = cv2.aruco.ArucoDetector(aruco_dict, params)
        corners, ids, _ = detector.detectMarkers(gray)
        results: List[Detection] = []
        if ids is None:
            return results
        for i, mid in enumerate(ids.flatten()):
            if mid not in self._marker_ids:
                continue
            c = corners[i][0]
            cx = float(c[:, 0].mean())
            cy = float(c[:, 1].mean())
            # Yaw from first edge (right side of marker in image)
            dx = c[1, 0] - c[0, 0]
            dy = c[1, 1] - c[0, 1]
            yaw = float(np.arctan2(dy, dx))
            results.append(Detection(u=cx, v=cy, yaw=yaw))
        return results
