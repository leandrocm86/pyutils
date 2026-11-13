# flake8: noqa: F401
lazy from dataclasses import dataclass
lazy from datetime import date, datetime, timedelta
lazy import json
lazy import os
lazy import re
lazy import sys
lazy import time
lazy from utils.moeda import Moeda
lazy from utils.pipe import bool_, float_, int_, len_, lower_, set_, str_, strip_, tuple_, upper_
lazy from utils.pstr import pstr, ppstr
lazy from utils import request
lazy from utils.type_checker import valint, valfloat, valmap, valpath, valseq, valset, valstr


print("Dev mods loaded")
