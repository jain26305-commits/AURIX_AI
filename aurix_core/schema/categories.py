from enum import Enum


class DataCategory(str, Enum):
    OBSERVED = "OBSERVED"
    DERIVED = "DERIVED"
    INFERRED = "INFERRED"
    USER_INPUT = "USER_INPUT"
    ASSUMPTION = "ASSUMPTION"
    MODEL_OUTPUT = "MODEL_OUTPUT"
