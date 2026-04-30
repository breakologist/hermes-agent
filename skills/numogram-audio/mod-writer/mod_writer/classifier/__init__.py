"""Numogram Classifier — MIR features → AQ zone/gate prediction.

Optional dependency: scikit-learn.
Usage:
    from mod_writer.classifier import predict
    pred = predict(feature_vector)  # returns {'aq': 42, 'zone': 4, 'gate': 2, 'candidates': [...]}
"""

__all__ = ['predict', 'train', 'DatasetBuilder']
