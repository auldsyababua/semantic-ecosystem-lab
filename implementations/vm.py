from __future__ import annotations

from implementations.direct_eval import make_engine


FAMILY_NAME = "compiled_instruction_vm"


def build(cfg):
    return make_engine(FAMILY_NAME, cfg)
