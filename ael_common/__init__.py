"""ael-common: the Automotive Ethics Lab's shared data agreement."""

from .actions import ACTION_DIRECTION, ACTION_NAMES, Action, to_action
from .datasets import load_cata_200, load_cata_200_labels, load_cata_200_split
from .state_vector import DIM, FIELD_NAMES, SPEC, Path, State, decode, encode, index
from .validate import (
    ValidationError,
    check_doc,
    check_file,
    check_vector,
    load_file,
    validate_doc,
    validate_file,
    validate_vector,
)

__version__ = "0.1.1"
