#!/usr/bin/env python3
"""Print an ArUco marker image for table calibration. Save and print at 100% scale with known size."""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a printable ArUco marker image.")
    parser.add_argument("--id", type=int, default=0, help="Marker ID (0–49 for DICT_4X4_50).")
    parser.add_argument("--size-px", type=int, default=400, help="Output image size (square) in pixels.")
    parser.add_argument("--dict", type=str, default="DICT_4X4_50", help="ArUco dictionary.")
    parser.add_argument("--output", type=Path, default=Path("aruco_marker_0.png"), help="Output path.")
    args = parser.parse_args()

    name_to_dict = {
        "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
        "DICT_4X4_100": cv2.aruco.DICT_4X4_100,
        "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
    }
    dict_id = name_to_dict.get(args.dict, cv2.aruco.DICT_4X4_50)
    aruco_dict = cv2.aruco.getPredefinedDictionary(dict_id)
    img = cv2.aruco.generateImageMarker(aruco_dict, args.id, args.size_px)
    # Add white border so printer doesn't crop
    border = args.size_px // 10
    img = cv2.copyMakeBorder(img, border, border, border, border, cv2.BORDER_CONSTANT, value=255)
    cv2.imwrite(str(args.output), img)
    print(f"Saved {args.output}. Print at 100% scale; measure marker side and set marker_size_m in aruco_table.yaml.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
