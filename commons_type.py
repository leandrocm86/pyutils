# Common modules bundle for typed scripts.
from datetime import datetime, timedelta, date  # type: ignore  # noqa
from typing import Type, TypeVar, TypeAlias, Self, Any, Mapping as Map, Sequence as Seq, Set  # type: ignore  # noqa
from abc import ABC, abstractmethod  # type: ignore  # noqa
from dataclasses import dataclass, field  # type: ignore  # noqa
from enum import Enum  # type: ignore  # noqa 
from collections import defaultdict  # type: ignore  # noqa
import mods.checker  # type: ignore  # noqa
from mods.mut import mut  # type: ignore  # noqa


T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

T_Type = Type[T]
K_Type = Type[K]
V_Type = Type[V]
