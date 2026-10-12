"""Vendored `face_detection` package: FaceAlignment/LandmarksType surface backed by MediaPipe.

MuseTalk needs: FaceAlignment(LandmarksType._2D, flip_input, device) and
fa.get_detections_for_batch(batch) -> [ [x1,y1,x2,y2] | None ].
MediaPipe has Windows wheels (no compiler needed); dlib/biubug6 do not.
"""
from enum import Enum


class LandmarksType(Enum):
    _2D = 1
    _2D_HALF = 2
    _3D = 3


# mesh landmarks we rely on (stable, well-known indices)
TIP, UPPER, CHIN = 1, 10, 152
EAR_L, EAR_R = 234, 454
EYE_L_OUT, EYE_L_IN = 33, 133
EYE_R_IN, EYE_R_OUT = 362, 263
MOUTH_L, MOUTH_R, MOUTH_TOP, MOUTH_BOT = 61, 291, 13, 14


def _mesh_landmarks(face_mesh, rgb):
    res = face_mesh.process(rgb)
    if not res.multi_face_landmarks:
        return None
    h, w = rgb.shape[:2]
    lm = res.multi_face_landmarks[0].landmark
    import numpy as np
    return np.array([(p.x * w, p.y * h) for p in lm], dtype=np.float32)


class FaceAlignment:
    def __init__(self, landmarks_type=LandmarksType._2D, flip_input=False, device="cpu"):
        self.landmarks_type = landmarks_type
        self.flip_input = flip_input
        import mediapipe as mp
        self._mp = mp
        self._mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True, max_num_faces=1, min_detection_confidence=0.5)

    def _landmarks(self, img_rgb):
        import numpy as np
        if self.flip_input:
            img_rgb = np.ascontiguousarray(img_rgb[:, ::-1])
        return _mesh_landmarks(self._mesh, img_rgb)

    def get_landmarks(self, img_rgb):
        """Return [(68,2) float32] or [] — dlib-68-compatible subset of the mesh."""
        import numpy as np
        pts = self._landmarks(img_rgb)
        if pts is None:
            return []
        return [self.to_dlib68(pts)]

    @staticmethod
    def to_dlib68(pts468):
        """Build a geometric 68-slot array: real extremes + interpolated nose bridge.

        Downstream only needs slots 28/29/30 (bridge->tip, monotonic in y) and
        the x/y min/max over all slots for the crop box. Everything comes from
        real mesh points, so the box is a valid face crop.
        """
        import numpy as np
        tip, upper = pts468[TIP], pts468[UPPER]
        d68 = np.zeros((68, 2), dtype=np.float32)
        d68[27] = upper * 0.65 + tip * 0.35
        d68[28] = upper * 0.45 + tip * 0.55
        d68[29] = upper * 0.25 + tip * 0.75
        d68[30] = tip
        d68[31:36] = tip  # nostril wing area approx (only affects min/max mildly)
        anchors = [CHIN, UPPER, EAR_L, EAR_R, EYE_L_OUT, EYE_L_IN,
                   EYE_R_IN, EYE_R_OUT, MOUTH_L, MOUTH_R, MOUTH_TOP, MOUTH_BOT]
        for i, a in enumerate(anchors):
            d68[36 + i] = pts468[a]
        d68[0:27:3] = pts468[CHIN]
        return d68

    def get_detections_for_batch(self, batch):
        import numpy as np
        imgs = np.asarray(batch)
        if imgs.ndim == 3:
            imgs = imgs[None]
        out = []
        for img in imgs:
            rgb = img[:, :, ::-1]
            pts = self._landmarks(np.ascontiguousarray(rgb))
            if pts is None:
                out.append(None)
                continue
            x1, y1 = pts.min(axis=0)
            x2, y2 = pts.max(axis=0)
            mx, my = (x2 - x1) * 0.1, (y2 - y1) * 0.1
            h, w = rgb.shape[:2]
            out.append([max(0, x1 - mx), max(0, y1 - my), min(w, x2 + mx), min(h, y2 + my)])
        return out
