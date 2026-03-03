"""
dataset.py
==========
PyTorch Dataset and DataLoader utilities for the Civil Registry OCR system.
"""

import os
import json
import random
from pathlib import Path
from typing import List, Tuple, Dict, Optional

import cv2
import numpy as np
import torch
from torch.utils.data import Dataset


# ─────────────────────────────────────────────────────────────────────────────
#  CHARACTER SET
# ─────────────────────────────────────────────────────────────────────────────

PRINTABLE_CHARS = [chr(i) for i in range(32, 127)]  # space (32) to ~ (126)


def build_char_maps(extra_chars: Optional[List[str]] = None):
    chars = PRINTABLE_CHARS.copy()
    if extra_chars:
        for c in extra_chars:
            if c not in chars:
                chars.append(c)
    char_to_idx = {c: i + 1 for i, c in enumerate(chars)}
    idx_to_char = {i + 1: c for i, c in enumerate(chars)}
    num_chars   = len(chars) + 1  # +1 for blank=0
    return char_to_idx, idx_to_char, num_chars


# ─────────────────────────────────────────────────────────────────────────────
#