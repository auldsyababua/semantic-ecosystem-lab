from __future__ import annotations

from implementations.direct_eval import make_engine


FAMILY_NAME = "table_driven_matcher"


def build(cfg):
    return make_engine(FAMILY_NAME, cfg)
