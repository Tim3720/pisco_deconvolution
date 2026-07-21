import os
os.environ["CUDA_VISIBLE_DEVICES"]="0,1"
import cv2 as cv
import torch
import numpy as np
import os

from multiprocessing import Queue

from .lucyd import LUCYD

# Get the directory of the current file
current_dir = os.path.dirname(__file__)

MODEL_NAME = 'lucyd-edof-plankton_231204.pth'
# MODEL_NAME = "lucyd-edof-plankton_230901.pth"
# MODEL_NAME = "lucyd-edof-plankton_best_train_loss.pth"


class DeconvolutionModel:

    def __init__(self):
        self.model = None
        self.device = None

    def load_model(self):
        model_path = self._get_model_path()
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Deconvolution model not found at '{model_path}'. "
                "Set PISCO_SEGMENTER_MODEL_PATH to a valid .pth file."
            )

        self.model = LUCYD(num_res=1)
        if torch.cuda.is_available():
            self.device = torch.device('cuda')
            print("CUDA is available, using GPU.")
        else:
            self.device = torch.device('cpu')
            print("Warning! CUDA is not available, using CPU.")

        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        if torch.cuda.device_count() > 1:
            print(f"Using {torch.cuda.device_count()} GPUs.")
            self.model = torch.nn.DataParallel(self.model)

        self.model.to(self.device)
        self.model.eval()

    def _get_model_path(self) -> str:
        return os.environ.get(
            "PISCO_SEGMENTER_MODEL_PATH",
            os.path.join(current_dir, 'models', MODEL_NAME),
        )

    def run_deconvolution(self, image_stack: list[np.ndarray], output: list[np.ndarray]):
        if self.model is None or self.device is None:
            raise Exception(
                "Deconvolution model not loaded. "
                "Call load_model() before running deconvolution."
            )

        batch = []
        for image in image_stack:
            x = image / 255
            x_t = torch.from_numpy(x).to(self.device)
            x_t = x_t.unsqueeze(0).unsqueeze(0)

            # Accumulate batch
            batch.append(x_t)

        batch_tensor = torch.cat(batch, dim=0)  # Combine images into a single tensor

        # Deconvolution on the batch
        with torch.no_grad():
            y_hat_batch, _, _ = self.model(batch_tensor.float())

        # Process each image in the batch
        for i in range(y_hat_batch.shape[0]):
            deconv = y_hat_batch.detach().cpu().numpy()[i, 0]
            deconv = deconv * 255
            cleaned = deconv.astype(np.uint8)
            output.append(cleaned)


        # import cv2
        # for i in range(len(output)):
        #     image = image_stack[i]
        #     cleaned = output[i]
        #     # image = cv2.bitwise_not(image)
        #     # cleaned = cv2.bitwise_not(cleaned)
        #
        #     image = np.concatenate((image, cleaned), axis=1)
        #     image = cv2.resize(image, (2000, 1000))
        #     while True:
        #         cv2.imshow("Image", image)
        #         k = cv2.waitKey()
        #         if k == ord("q"):
        #             break
