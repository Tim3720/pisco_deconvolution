import numpy as np
import cv2
import h5py
from .hdf import get_group, get_dataset
from datetime import datetime


def write_crops(deconvolved_atlases: list[np.ndarray],
                maps: list[dict[str, list[tuple[int, int, int, int, int]]]],
                filename):

    for i, image in enumerate(deconvolved_atlases):
        map = maps[i]
        image = cv2.bitwise_not(image)


        for name, crops in map.items():
            with h5py.File(filename, "r") as f:
                image_group = get_group(f, name)
                widths = get_dataset(image_group, "boundingBoxW")[()]
                heights = get_dataset(image_group, "boundingBoxH")[()]

            offsets = [0]
            for j in range(len(widths) - 1):
                offsets.append(offsets[j] + widths[j] * heights[j])

            with h5py.File(filename, "r+") as f:
                image_group = get_group(f, name)
                # overwrite existing pixel data set:
                dataset = get_dataset(image_group, "pixelData")

                for crop in crops:
                    x, y, w, h, idx = crop

                    crop_image = image[y:y + h, x:x + w]
                    # crop_image = cv2.normalize(crop_image, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)

                    dataset[offsets[idx]:offsets[idx] + w * h] = crop_image.flatten()


        # org_image = image.copy()
        # image = cv2.cvtColor(org_image, cv2.COLOR_GRAY2BGR)
        # full_thresh = np.zeros_like(image)
        # for name, crops in map.items():
        #     for crop in crops:
        #         x, y, w, h, idx = crop
        #         cv2.rectangle(image, (x, y), (x + w, y + h), (255, 0, 0), 2)
        #
        #         thresh = cv2.threshold(org_image[y:y + h, x:x + w], 60, 255,
        #                                cv2.THRESH_BINARY)[1]
        #
        #         full_thresh[y:y + h, x:x + w, 0] = thresh
        #         full_thresh[y:y + h, x:x + w, 1] = thresh
        #         full_thresh[y:y + h, x:x + w, 2] = thresh
        #
        #         cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        #         for c in cnts[0]:
        #             cv2.drawContours(image, [c], 0, (0, 0, 255), 2, offset=(x, y))
        #
        # image = np.concatenate((batch[i], image), axis=1)
        # image = cv2.bitwise_not(image)
        # image = cv2.resize(image, (1000, 1000))
        # while True:
        #     cv2.imshow("Image", image)
        #     k = cv2.waitKey()
        #     if k == ord("q"):
        #         break
