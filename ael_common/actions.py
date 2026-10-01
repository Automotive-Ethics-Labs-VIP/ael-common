"""Action IDs shared by every AEL repo.

The ethical head chooses one of three actions at a frozen dilemma moment.
"maintain" means hand control back to the vehicle's normal controller; it does
not mean "drive straight at full speed".
"""

from enum import IntEnum
from typing import Union


class Action(IntEnum):
    MAINTAIN = 0
    SWERVE_LEFT = 1
    SWERVE_RIGHT = 2


ACTION_NAMES = {
    Action.MAINTAIN: "maintain",
    Action.SWERVE_LEFT: "swerve_left",
    Action.SWERVE_RIGHT: "swerve_right",
}

_BY_NAME = {name: action for action, name in ACTION_NAMES.items()}

# The path each action drives the vehicle into.
ACTION_DIRECTION = {
    Action.MAINTAIN: "straight",
    Action.SWERVE_LEFT: "left",
    Action.SWERVE_RIGHT: "right",
}


def to_action(value: Union[int, str, Action]) -> Action:
    """Convert an int ID or a name ("maintain", "swerve_left", ...) to an Action.

    Raises ValueError for anything outside the v1 action set, including the
    5-action IDs (brake_hard, accelerate) used by older Ethical_Head code.
    """
    if isinstance(value, Action):
        return value
    if isinstance(value, str):
        if value not in _BY_NAME:
            raise ValueError(
                "Unknown action name {!r}; expected one of {}".format(value, sorted(_BY_NAME))
            )
        return _BY_NAME[value]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("Action must be an int or name, got {!r}".format(value))
    try:
        return Action(value)
    except ValueError:
        raise ValueError("Action ID {} is not in the v1 set (0, 1, 2)".format(value)) from None
