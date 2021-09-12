"""
Compile-time hook used to set constants.
"""
from pathlib import Path

from brownie import ZERO_ADDRESS
from brownie._config import CONFIG


def brownie_load_source(path: Path, source: str):

    if "templates" not in path.parts:
        # compile-time substitution only applies to pool templates
        # and only when in test mode
        return source

    replacements = {
        "___BASE_N_COINS___": 3,
        "___BASE_COINS___": f"[{', '.join([ZERO_ADDRESS] * 3)}]",
    }
    if CONFIG.mode != "test":
        replacements = {
            "___BASE_N_COINS___": 69,
            "___BASE_COINS___": f"[{', '.join([ZERO_ADDRESS] * 69)}]",
        }

    for k, v in replacements.items():
        source = source.replace(k, str(v))

    return source
