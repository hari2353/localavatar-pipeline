"""Shim for mmpose.structures.merge_data_samples (contract-only)."""


class _PredInstances:
    def __init__(self, d):
        self.keypoints = d["keypoints"]
        self.keypoint_scores = d.get("scores")


class _Sample:
    def __init__(self, d):
        self.pred_instances = _PredInstances(d)


def merge_data_samples(results):
    return _Sample(results[0])
