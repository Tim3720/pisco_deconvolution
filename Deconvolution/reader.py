import os
from typing import Optional
import h5py
import numpy as np
from .hdf import get_group, get_dataset
import cv2

class Reader:

    def __init__(self, source_path: str):
        self.files: list[str] = []
        self.source_path: str = source_path

        self._current_file: Optional[h5py.File] = None
        self._current_filename: Optional[str] = None
        self._group_keys: list[str] = []

        self._current_file_index = 0
        self._current_group_index = 0

        self._find_checkpoint_files()

    def _find_checkpoint_files(self):
        for file in os.listdir(self.source_path):
            if "checkpoint_correction" in file  and file.endswith(".h5"):
                self.files.append(os.path.join(self.source_path, file))
        self.files.sort()
        print("Found the following checkpoint files:", self.files)

    def is_last_group(self) -> bool:
        return self._current_group_index >= len(self._group_keys)

    def is_last_file(self) -> bool:
        return self._current_file_index >= len(self.files)

    def close_current_file(self):
        if self._current_filename is not None:
            self._current_filename = None

    def open_next_file(self):
        if self._current_file_index >= len(self.files):
            raise ValueError("No more files to open")

        self._current_filename = self.files[self._current_file_index]

        with h5py.File(self._current_filename, "r") as f:
            self._group_keys = list(f.keys())

        self._current_file_index += 1
        self._current_group_index = 0

        return self._current_filename

    def get_next_group_images(self):
        if self._current_filename is None:
            raise ValueError("No open file")

        if self._current_group_index >= len(self._group_keys):
            raise ValueError("No more groups to read")

        with h5py.File(self._current_filename, "r") as f:
            group_name = self._group_keys[self._current_group_index]
            group = get_group(f, group_name)
            self._current_group_index += 1

            images = []
            widths = get_dataset(group, "boundingBoxW")[()]
            heights = get_dataset(group, "boundingBoxH")[()]
            pixel_data = get_dataset(group, "pixelData")[()]
            offset = 0

            for i in range(len(widths)):
                image = pixel_data[offset:offset + widths[i] * heights[i]]
                offset += widths[i] * heights[i]
                image = image.reshape(heights[i], widths[i])

                # balance crop:
                # image = cv2.normalize(image, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
                # image += 30
                # image = cv2.bitwise_not(image)

                padded = np.ones((image.shape[0] + 2, image.shape[1] + 2)) * 255
                padded[1:-1, 1:-1] = image
                image = padded
                # image[:, 0] = 255
                # image[:, -1] = 255
                # image[0, :] = 255
                # image[-1, :] = 255

                images.append(image)

        return group_name, images

