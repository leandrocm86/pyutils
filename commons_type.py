# Common modules bundle for typed scripts.
from datetime import datetime, timedelta, date  # type: ignore  # noqa
from typing import Annotated, Type, TypeVar, TypeAlias, Self, Any, Mapping as Map, Sequence as Seq, Set  # type: ignore  # noqa
from abc import ABC, abstractmethod  # type: ignore  # noqa
from typing import Iterable  # noqa
from dataclasses import dataclass, field  # type: ignore  # noqa
from enum import Enum  # type: ignore  # noqa
from collections import defaultdict  # type: ignore  # noqa
from pathlib import Path  # type: ignore  # noqa
from typing import Callable  # type: ignore  # noqa
from decimal import Decimal  # type: ignore  # noqa

from utils.type_checker import check_type, valint, valbool, valfloat, valstr, valseq, valset, valmap, valpath, valobj  # type: ignore  # noqa
from utils.mut import Mut  # type: ignore  # noqa
from utils.moeda import Moeda  # type: ignore  # noqa


T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

T_Type = Type[T]
K_Type = Type[K]
V_Type = Type[V]
