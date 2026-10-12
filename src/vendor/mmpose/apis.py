"""Shim for mmpose.apis.inference_topdown / init_model (contract-only).

Sources REAL facial geometry from the vendored face_detection shim (MediaPipe)
and presents it as wholebody-133 keypoints. MuseTalk reads keypoints[0][23:91].
"""
import numpy as np

N_TOTAL = 133
FACE_LO, FACE_HI = 23, 91  # wholebody-133 facial slice used by MuseTalk


def init_model(config_file=None, checkpoint_file=None, device="cpu"):
    from face_detection import FaceAlignment, LandmarksType
    fa = FaceAlignment(LandmarksType._2D, flip_input=False, device=device)
    return {"fa": fa}


def inference_topdown(model, img):
    """img: BGR uint8 HxWx3. Returns [{\"keypoints\": (1,133,2), \"scores\": (1,133)}]."""
    fa = model["fa"]
    rgb = np.ascontiguousarray(img[:, :, ::-1])
    lm68_list = fa.get_landmarks(rgb)
    kpts = np.zeros((1, N_TOTAL, 2), dtype=np.float32)
    scores = np.zeros((1, N_TOTAL), dtype=np.float32)
    if lm68_list:
        kpts[0, FACE_LO:FACE_HI] = lm68_list[0]
        scores[0, FACE_LO:FACE_HI] = 1.0
    return [{"keypoints": kpts, "scores": scores}]
