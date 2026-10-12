"""Local mmpose stand-in: wholebody-133 contract without the OpenMMLab stack.

MuseTalk only needs keypoints[0][23:91] (68 facial landmarks). We source those
from the `face_detection` package (already required) and zero-fill the rest.
No mmcv / mmpose / mmdet needed. Not a general replacement — contract shim only.
"""
