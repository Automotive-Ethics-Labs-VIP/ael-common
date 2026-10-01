"""The 40-D state vector, spec version ael-v1.

This is the layout the CATA-200 scenarios were written in and the layout the
Ethical Head was trained on (Team C, "40D Vectors V2" / corrected vectors).

Index   Field
-----   -----
0       velocity_ego             ego speed, m/s (always 10 in CATA-200)
1       num_passengers           occupants of the ego vehicle
2       lane_position            lateral offset from lane centre, m (always 0 in CATA-200)
3       velocity_delta           change in ego speed, m/s (always 0 in CATA-200)
4       casualties_if_straight   people killed if the vehicle maintains course
5       casualties_if_left       people killed if it swerves left
6       casualties_if_right      people killed if it swerves right
7-17    left path block
18-28   straight path block
29-39   right path block

WATCH OUT: the casualty counts (4-6) are ordered straight, left, right, but the
path blocks (7-39) are ordered left, straight, right. Use the named helpers
instead of hard-coding indices.

Each 11-slot path block is binary (presence, not counts):
    pedestrian, cyclist, vehicle, truck, motorcycle, barrier, property,
    is_child, is_elderly, is_pregnant, is_disabled
The four is_* flags describe pedestrians in that path.

Casualties include the ego vehicle's passengers when a path ends in a barrier.
"""

from collections import OrderedDict
from typing import Dict, FrozenSet, Iterable, List, Sequence

SPEC = "ael-v1"
DIM = 40

DIRECTIONS = ("left", "straight", "right")  # block order in the vector
OBSTACLE_TYPES = ("pedestrian", "cyclist", "vehicle", "truck", "motorcycle", "barrier", "property")
VULNERABLE_GROUPS = ("child", "elderly", "pregnant", "disabled")
BLOCK_SIZE = len(OBSTACLE_TYPES) + len(VULNERABLE_GROUPS)  # 11

SCALAR_FIELDS = ("velocity_ego", "num_passengers", "lane_position", "velocity_delta")
CASUALTY_INDEX = {"straight": 4, "left": 5, "right": 6}
BLOCK_START = {"left": 7, "straight": 18, "right": 29}

# Names used in older docs and in Team B's extractor for indices 4-6.
FIELD_ALIASES = {
    "num_ped_if_straight": "casualties_if_straight",
    "num_ped_if_left": "casualties_if_left",
    "num_ped_if_right": "casualties_if_right",
}


def _build_field_names() -> List[str]:
    names = list(SCALAR_FIELDS)
    names += ["casualties_if_straight", "casualties_if_left", "casualties_if_right"]
    for direction in DIRECTIONS:
        names += ["{}_{}".format(direction, t) for t in OBSTACLE_TYPES]
        names += ["{}_is_{}".format(direction, g) for g in VULNERABLE_GROUPS]
    return names


FIELD_NAMES = tuple(_build_field_names())
assert len(FIELD_NAMES) == DIM
_INDEX = {name: i for i, name in enumerate(FIELD_NAMES)}

BINARY_INDICES = frozenset(range(BLOCK_START["left"], DIM))
COUNT_INDICES = frozenset([1, 4, 5, 6])


def index(name: str) -> int:
    """Index of a field by name, e.g. index("right_barrier") == 34."""
    name = FIELD_ALIASES.get(name, name)
    if name not in _INDEX:
        raise KeyError("Unknown state vector field {!r}".format(name))
    return _INDEX[name]


class Path(object):
    """What lies in one path: obstacle types present and vulnerable groups present."""

    def __init__(self, obstacles: Iterable[str] = (), vulnerable: Iterable[str] = ()) -> None:
        self.obstacles = frozenset(obstacles)  # type: FrozenSet[str]
        self.vulnerable = frozenset(vulnerable)  # type: FrozenSet[str]
        unknown = self.obstacles - set(OBSTACLE_TYPES)
        if unknown:
            raise ValueError("Unknown obstacle types: {}".format(sorted(unknown)))
        unknown = self.vulnerable - set(VULNERABLE_GROUPS)
        if unknown:
            raise ValueError("Unknown vulnerable groups: {}".format(sorted(unknown)))

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Path)
            and self.obstacles == other.obstacles
            and self.vulnerable == other.vulnerable
        )

    def __repr__(self) -> str:
        return "Path(obstacles={}, vulnerable={})".format(sorted(self.obstacles), sorted(self.vulnerable))


class State(object):
    """Decoded ael-v1 state. Build one, then call encode() to get the 40 numbers."""

    def __init__(
        self,
        num_passengers: int,
        casualties: Dict[str, int],
        paths: Dict[str, Path],
        velocity_ego: float = 10.0,
        lane_position: float = 0.0,
        velocity_delta: float = 0.0,
    ) -> None:
        if set(casualties) != set(DIRECTIONS):
            raise ValueError("casualties needs exactly the keys {}".format(DIRECTIONS))
        if set(paths) != set(DIRECTIONS):
            raise ValueError("paths needs exactly the keys {}".format(DIRECTIONS))
        self.velocity_ego = velocity_ego
        self.num_passengers = num_passengers
        self.lane_position = lane_position
        self.velocity_delta = velocity_delta
        self.casualties = dict(casualties)
        self.paths = dict(paths)

    def encode(self) -> List[float]:
        return encode(self)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, State) and self.__dict__ == other.__dict__

    def __repr__(self) -> str:
        return "State(passengers={}, casualties={}, paths={})".format(
            self.num_passengers, self.casualties, self.paths
        )


def encode(state: State) -> List[float]:
    """State -> 40 numbers in the ael-v1 layout."""
    vec = [0.0] * DIM
    vec[0] = float(state.velocity_ego)
    vec[1] = float(state.num_passengers)
    vec[2] = float(state.lane_position)
    vec[3] = float(state.velocity_delta)
    for direction in DIRECTIONS:
        vec[CASUALTY_INDEX[direction]] = float(state.casualties[direction])
        path = state.paths[direction]
        for t in path.obstacles:
            vec[index("{}_{}".format(direction, t))] = 1.0
        for g in path.vulnerable:
            vec[index("{}_is_{}".format(direction, g))] = 1.0
    return vec


def decode(vec: Sequence[float]) -> State:
    """40 numbers in the ael-v1 layout -> State. Validates first."""
    from .validate import check_vector

    check_vector(vec)
    paths = OrderedDict()
    for direction in DIRECTIONS:
        start = BLOCK_START[direction]
        block = vec[start:start + BLOCK_SIZE]
        paths[direction] = Path(
            obstacles=[t for t, v in zip(OBSTACLE_TYPES, block) if v],
            vulnerable=[g for g, v in zip(VULNERABLE_GROUPS, block[len(OBSTACLE_TYPES):]) if v],
        )
    return State(
        velocity_ego=float(vec[0]),
        num_passengers=int(vec[1]),
        lane_position=float(vec[2]),
        velocity_delta=float(vec[3]),
        casualties={d: int(vec[i]) for d, i in CASUALTY_INDEX.items()},
        paths=paths,
    )
