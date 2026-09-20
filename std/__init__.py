#############################################################
# Modulo wrapper agrupando toda a standard library do python.
# Visa facilitar (reduzindo) os imports em cada script.
#############################################################

lazy import abc as abc
lazy import argparse as argparse
lazy import array as array
lazy import ast as ast
lazy import asyncio as asyncio
lazy import atexit as atexit
lazy import base64 as base64
lazy import bdb as bdb
lazy import binascii as binascii
lazy import bisect as bisect
lazy import builtins as builtins
lazy import bz2 as bz2
lazy import calendar as calendar
lazy import cmath as cmath
lazy import cmd as cmd
lazy import code as code
lazy import codecs as codecs
lazy import codeop as codeop
lazy import collections as collections
lazy import colorsys as colorsys
lazy import compileall as compileall
lazy import concurrent as concurrent
lazy import configparser as configparser
lazy import contextlib as contextlib
lazy import contextvars as contextvars
lazy import copy as copy
lazy import copyreg as copyreg
lazy import cProfile as cProfile
lazy import csv as csv
lazy import ctypes as ctypes
lazy import curses as curses
lazy import dataclasses as dataclasses
lazy import dbm as dbm
lazy import decimal as decimal
lazy import difflib as difflib
lazy import dis as dis
lazy import doctest as doctest
lazy import email as email
lazy import encodings as encodings
lazy import enum as enum
lazy import errno as errno
lazy import faulthandler as faulthandler
lazy import fcntl as fcntl
lazy import filecmp as filecmp
lazy import fileinput as fileinput
lazy import fnmatch as fnmatch
lazy import fractions as fractions
lazy import ftplib as ftplib
lazy import functools as functools
lazy import gc as gc
lazy import genericpath as genericpath
lazy import getopt as getopt
lazy import getpass as getpass
lazy import gettext as gettext
lazy import glob as glob
lazy import graphlib as graphlib
lazy import grp as grp
lazy import gzip as gzip
lazy import hashlib as hashlib
lazy import heapq as heapq
lazy import hmac as hmac
lazy import html as html
lazy import http as http
lazy import imaplib as imaplib
lazy import importlib as importlib
lazy import inspect as inspect
lazy import io as io
lazy import ipaddress as ipaddress
lazy import itertools as itertools
lazy import json as json
lazy import keyword as keyword
lazy import linecache as linecache
lazy import locale as locale
lazy import logging as logging
lazy import lzma as lzma
lazy import mailbox as mailbox
lazy import marshal as marshal
lazy import math as math
lazy import mimetypes as mimetypes
lazy import mmap as mmap
lazy import modulefinder as modulefinder
lazy import multiprocessing as multiprocessing
lazy import netrc as netrc
lazy import ntpath as ntpath

# DEPRECATED in python 3.19
# lazy import nturl2path as nturl2path

lazy import numbers as numbers
lazy import opcode as opcode
lazy import operator as operator
lazy import optparse as optparse
lazy import os as os
lazy import pathlib as pathlib
lazy import pdb as pdb
lazy import pickle as pickle
lazy import pickletools as pickletools
lazy import pkgutil as pkgutil
lazy import platform as platform
lazy import plistlib as plistlib
lazy import poplib as poplib
lazy import posix as posix
lazy import posixpath as posixpath
lazy import pprint as pprint

# DEPRECATED in python 3.17
# lazy import profile as profile

lazy import pstats as pstats
lazy import pty as pty
lazy import pwd as pwd
lazy import py_compile as py_compile
lazy import pyclbr as pyclbr
lazy import pydoc as pydoc
lazy import pydoc_data as pydoc_data
lazy import pyexpat as pyexpat
lazy import queue as queue
lazy import quopri as quopri
lazy import random as random
lazy import re as re
lazy import readline as readline
lazy import reprlib as reprlib
lazy import resource as resource
lazy import rlcompleter as rlcompleter
lazy import runpy as runpy
lazy import sched as sched
lazy import secrets as secrets
lazy import select as select
lazy import selectors as selectors
lazy import shelve as shelve
lazy import shlex as shlex
lazy import shutil as shutil
lazy import signal as signal
lazy import site as site
lazy import smtplib as smtplib
lazy import socket as socket
lazy import socketserver as socketserver
lazy import sqlite3 as sqlite3
lazy import ssl as ssl
lazy import stat as stat
lazy import statistics as statistics
lazy import string as string
lazy import stringprep as stringprep
lazy import struct as struct
lazy import subprocess as subprocess
lazy import symtable as symtable
lazy import sys as sys
lazy import sysconfig as sysconfig
lazy import syslog as syslog
lazy import tabnanny as tabnanny
lazy import tarfile as tarfile
lazy import tempfile as tempfile
lazy import termios as termios
lazy import textwrap as textwrap
lazy import threading as threading
lazy import time as time
lazy import timeit as timeit

# tkinter is not available in all python installations
# import tkinter
lazy import token as token
lazy import tokenize as tokenize
lazy import trace as trace
lazy import traceback as traceback
lazy import tracemalloc as tracemalloc
lazy import tty as tty
lazy import types as types
lazy import typing as typing
lazy import unicodedata as unicodedata
lazy import unittest as unittest
lazy import urllib as urllib
lazy import uuid as uuid
lazy import venv as venv
lazy import warnings as warnings
lazy import wave as wave
lazy import weakref as weakref
lazy import webbrowser as webbrowser
lazy import wsgiref as wsgiref
lazy import xml as xml
lazy import xmlrpc as xmlrpc
lazy import zipapp as zipapp
lazy import zipfile as zipfile
lazy import zipimport as zipimport
lazy import zlib as zlib
lazy import zoneinfo as zoneinfo

lazy import tomllib as tomllib

lazy from abc import ABC as ABC, abstractmethod as abstractmethod
lazy from dataclasses import dataclass as dataclass
lazy from datetime import date as date, datetime as datetime, timedelta as timedelta
lazy from decimal import Decimal as Decimal
lazy from enum import Enum as Enum
lazy from pathlib import Path as Path
lazy from statistics import mean as mean, fmean as fmean
lazy from typing import Any as Any, Callable as Callable, cast as cast, Collection as Collection, final as final, Final as Final, FrozenSet as FrozenSet, Iterable as Iterable, Mapping as Mapping, Optional as Optional, override as override, Self as Self, Sequence as Sequence, Set as Set, Type as Type, TypeVar as TypeVar
lazy from typing import Sequence as Seq
lazy from urllib import request as request

__all__ = ["Seq"]
