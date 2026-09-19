#############################################################
# Modulo wrapper agrupando toda a standard library do python.
# Visa facilitar (reduzindo) os imports em cada script.
#############################################################

import abc as abc
import argparse as argparse
import array as array
import ast as ast
import asyncio as asyncio
import atexit as atexit
import base64 as base64
import bdb as bdb
import binascii as binascii
import bisect as bisect
import builtins as builtins
import bz2 as bz2
import calendar as calendar
import cmath as cmath
import cmd as cmd
import code as code
import codecs as codecs
import codeop as codeop
import collections as collections
import colorsys as colorsys
import compileall as compileall
import concurrent as concurrent
import configparser as configparser
import contextlib as contextlib
import contextvars as contextvars
import copy as copy
import copyreg as copyreg
import cProfile as cProfile
import csv as csv
import ctypes as ctypes
import curses as curses
import dataclasses as dataclasses
import dbm as dbm
import decimal as decimal
import difflib as difflib
import dis as dis
import doctest as doctest
import email as email
import encodings as encodings
import enum as enum
import errno as errno
import faulthandler as faulthandler
import fcntl as fcntl
import filecmp as filecmp
import fileinput as fileinput
import fnmatch as fnmatch
import fractions as fractions
import ftplib as ftplib
import functools as functools
import gc as gc
import genericpath as genericpath
import getopt as getopt
import getpass as getpass
import gettext as gettext
import glob as glob
import graphlib as graphlib
import grp as grp
import gzip as gzip
import hashlib as hashlib
import heapq as heapq
import hmac as hmac
import html as html
import http as http
import imaplib as imaplib
import importlib as importlib
import inspect as inspect
import io as io
import ipaddress as ipaddress
import itertools as itertools
import json as json
import keyword as keyword
import linecache as linecache
import locale as locale
import logging as logging
import lzma as lzma
import mailbox as mailbox
import marshal as marshal
import math as math
import mimetypes as mimetypes
import mmap as mmap
import modulefinder as modulefinder
import multiprocessing as multiprocessing
import netrc as netrc
import ntpath as ntpath
import nturl2path as nturl2path
import numbers as numbers
import opcode as opcode
import operator as operator
import optparse as optparse
import os as os
import pathlib as pathlib
import pdb as pdb
import pickle as pickle
import pickletools as pickletools
import pkgutil as pkgutil
import platform as platform
import plistlib as plistlib
import poplib as poplib
import posix as posix
import posixpath as posixpath
import pprint as pprint
import profile as profile
import pstats as pstats
import pty as pty
import pwd as pwd
import py_compile as py_compile
import pyclbr as pyclbr
import pydoc as pydoc
import pydoc_data as pydoc_data
import pyexpat as pyexpat
import queue as queue
import quopri as quopri
import random as random
import re as re
import readline as readline
import reprlib as reprlib
import resource as resource
import rlcompleter as rlcompleter
import runpy as runpy
import sched as sched
import secrets as secrets
import select as select
import selectors as selectors
import shelve as shelve
import shlex as shlex
import shutil as shutil
import signal as signal
import site as site
import smtplib as smtplib
import socket as socket
import socketserver as socketserver
import sqlite3 as sqlite3
import ssl as ssl
import stat as stat
import statistics as statistics
import string as string
import stringprep as stringprep
import struct as struct
import subprocess as subprocess
import symtable as symtable
import sys as sys
import sysconfig as sysconfig
import syslog as syslog
import tabnanny as tabnanny
import tarfile as tarfile
import tempfile as tempfile
import termios as termios
import textwrap as textwrap
import threading as threading
import time as time
import timeit as timeit

# tkinter is not available in all python installations
# import tkinter
import token as token
import tokenize as tokenize
import trace as trace
import traceback as traceback
import tracemalloc as tracemalloc
import tty as tty
import types as types
import typing as typing
import unicodedata as unicodedata
import unittest as unittest
import urllib as urllib
import uuid as uuid
import venv as venv
import warnings as warnings
import wave as wave
import weakref as weakref
import webbrowser as webbrowser
import wsgiref as wsgiref
import xml as xml
import xmlrpc as xmlrpc
import zipapp as zipapp
import zipfile as zipfile
import zipimport as zipimport
import zlib as zlib
import zoneinfo as zoneinfo

import tomllib as tomllib

from abc import ABC as ABC, abstractmethod as abstractmethod
from dataclasses import dataclass as dataclass
from datetime import date as date, datetime as datetime, timedelta as timedelta
from decimal import Decimal as Decimal
from enum import Enum as Enum
from pathlib import Path as Path
from statistics import mean as mean, fmean as fmean
from typing import Any as Any, Callable as Callable, cast as cast, Collection as Collection, final as final, Final as Final, FrozenSet as FrozenSet, Iterable as Iterable, Mapping as Mapping, Optional as Optional, override as override, Self as Self, Sequence as Sequence, Set as Set, Type as Type, TypeVar as TypeVar
from typing import Sequence as Seq
from urllib import request as request

__all__ = ["Seq"]
