"""
calibrate_fields.py
===================
Click-to-measure tool for recalibrating field ratios in field_extractor.py.

Usage:
    python calibrate_fields.py --image your_scan.png --form birth

Controls:
    • Click and drag  → draw a field box
    • After releasing → enter the field name in the terminal
    • Press S         → save all measured ratios to calibrated_fields.py
    • Press Z         → undo last box
    • Press Q / ESC   → quit without saving

Output:
    calibrated_fields.py  — copy-paste the dict into field_extractor.py
"""

import argparse
import json
import cv2
import numpy as np
from pathlib import Path

# ── state ─────────────────────────────────────────────────────────────────────
drawing   = False
ix, iy    = -1, -1
ex, ey    = -1, -1
boxes     = []        # list of (name, rx1, ry1, rx2, ry2)
form_name = "birth"

COLOURS = [
    (0,200,0),(0,150,255),(200,0,200),(0,200,200),(200,200,0),(220,20,60),
    (255,140,0),(150,50,200),(0,160,80),(30,144,255),(255,20,147),(100,200,100),
]

def draw_boxes(img, bounds):
    left, top, right, bottom = bounds
    fw = right - left
    fh = bottom - top

    vis = img.copy()
    # form boundary
    cv2.rectangle(vis, (left, top), (right, bottom), (0, 140, 255), 2)

    for idx, (name, rx1, ry1, rx2, ry2) in enumerate(boxes):
        x1 = int(left + rx1 * fw)
        y1 = int(top  + ry1 * fh)
        x2 = int(left + rx2 * fw)
        y2 = int(top  + ry2 * fh)
        c  = COLOURS[idx % len(COLOURS)]
        cv2.rectangle(vis, (x1, y1), (x2, y2), c, 2)
        cv2.putText(vis, name[:25], (x1 + 2, max(0, y1 - 3)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, c, 1)

    # live cursor box
    if drawing and ix >= 0 and ex >= 0:
        cv2.rectangle(vis, (ix, iy), (ex, ey), (255, 255, 255), 1)

    # instructions
    cv2.putText(vis, "Drag=draw box | S=save | Z=undo | Q=quit",
                (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)
    cv2.putText(vis, f"Boxes: {len(boxes)}",
                (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)
    return vis


def detect_bounds(image_bgr):
    """Simple form boundary detection (reuses logic from FormBoundsDetector)."""
    h, w  = image_bgr.shape[:2]
    gray  = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    try:
        thresh  = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2)
        hk      = cv2.getStructuringElement(cv2.MORPH_RECT, (max(w // 5, 10), 1))
        h_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, hk)
        h_rows  = np.where(np.sum(h_lines, axis=1) > w * 0.15)[0]
        vk      = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(h // 5, 10)))
        v_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vk)
        v_cols  = np.where(np.sum(v_lines, axis=0) > h * 0.08)[0]
        if len(h_rows) == 0 or len(v_cols) == 0:
            return (0, 0, w, h)
        top_b, bottom_b = int(h_rows.min()), int(h_rows.max())
        left_b, right_b = int(v_cols.min()), int(v_cols.max())
        if (right_b - left_b) < w * 0.4 or (bottom_b - top_b) < h * 0.4:
            return (0, 0, w, h)
        return (left_b, top_b, right_b, bottom_b)
    except Exception:
        return (0, 0, w, h)


def save_calibration(output_path, form):
    dict_name = {
        "birth":            "BIRTH_FIELDS",
        "death":            "DEATH_FIELDS",
        "marriage":         "MARRIAGE_FIELDS",
        "marriage_license": "MARRIAGE_LICENSE_FIELDS",
    }.get(form, "CALIBRATED_FIELDS")

    lines = [f"# Auto-calibrated — copy-paste into field_extractor.py\n",
             f"{dict_name} = {{\n"]
    for name, rx1, ry1, rx2, ry2 in boxes:
        lines.append(f'    "{name}":{" " * max(1, 34 - len(name))}'
                     f'({rx1:.4f}, {ry1:.4f}, {rx2:.4f}, {ry2:.4f}),\n')
    lines.append("}\n")

    with open(output_path, "w") as f:
        f.writelines(lines)
    print(f"\n  Saved {len(boxes)} fields → {output_path}")


def main():
    global drawing, ix, iy, ex, ey, form_name

    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--form",  default="birth",
                        choices=["birth","death","marriage","marriage_license"])
    parser.add_argument("--output", default="calibrated_fields.py")
    parser.add_argument("--scale",  type=float, default=1.0,
                        help="Scale factor to fit image on screen (e.g. 0.5)")
    args = parser.parse_args()
    form_name = args.form

    img_orig = cv2.imread(args.image)
    if img_orig is None:
        print(f"ERROR: Cannot load {args.image}")
        return

    scale = args.scale
    if scale != 1.0:
        img_orig = cv2.resize(img_orig, None, fx=scale, fy=scale)

    bounds = detect_bounds(img_orig)
    left, top, right, bottom = bounds
    fw = right - left
    fh = bottom - top
    print(f"  Form boundary detected: {bounds}  ({fw}×{fh} px)")
    print(f"  Scale: {scale}")
    print("\n  Instructions:")
    print("    Drag  → draw a field box")
    print("    After releasing → type field name in terminal, press Enter")
    print("    S     → save all boxes")
    print("    Z     → undo last box")
    print("    Q/ESC → quit\n")

    win = "Calibrate Fields"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)

    def mouse(event, x, y, flags, param):
        global drawing, ix, iy, ex, ey
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            ix, iy  = x, y
            ex, ey  = x, y
        elif event == cv2.EVENT_MOUSEMOVE and drawing:
            ex, ey  = x, y
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            ex, ey  = x, y
            x1r = (min(ix, ex) - left) / fw
            y1r = (min(iy, ey) - top)  / fh
            x2r = (max(ix, ex) - left) / fw
            y2r = (max(iy, ey) - top)  / fh
            x1r, y1r = max(0.0, x1r), max(0.0, y1r)
            x2r, y2r = min(1.0, x2r), min(1.0, y2r)
            if (x2r - x1r) > 0.005 and (y2r - y1r) > 0.003:
                name = input(f"  Field name for ({x1r:.3f},{y1r:.3f},{x2r:.3f},{y2r:.3f}): ").strip()
                if name:
                    boxes.append((name, x1r, y1r, x2r, y2r))
                    print(f"  ✓  '{name}' added  (total: {len(boxes)})")

    cv2.setMouseCallback(win, mouse)

    while True:
        vis = draw_boxes(img_orig, bounds)
        cv2.imshow(win, vis)
        key = cv2.waitKey(20) & 0xFF

        if key in (ord('q'), 27):
            print("  Quit — no file saved.")
            break
        elif key == ord('s'):
            save_calibration(args.output, form_name)
            break
        elif key == ord('z') and boxes:
            removed = boxes.pop()
            print(f"  Undone: '{removed[0]}'")

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
