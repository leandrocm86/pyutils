# Baseado em https://github.com/juanrgon/terminology/blob/master/terminology/ansi.py

import re
from contextlib import contextmanager
from typing import Self


no_color = False


@contextmanager
def disable():
    global no_color
    original = no_color
    no_color = True
    try:
        yield
    finally:
        no_color = original


def visual_len(text: str) -> int:
    """The apparent visual length of this string in a terminal."""
    return len(text) if no_color else len(_remove_regex("\033\\[[0-9]*m", text))


class StyledStr(str):
    def black(self) -> Self:
        return black(self)

    def blue(self) -> Self:
        return blue(self)

    def bold(self) -> Self:
        return bold(self)

    def cyan(self) -> Self:
        return cyan(self)

    def green(self) -> Self:
        return green(self)

    def magenta(self) -> Self:
        return magenta(self)

    def red(self) -> Self:
        return red(self)

    def white(self) -> Self:
        return white(self)

    def yellow(self) -> Self:
        return yellow(self)

    def on_black(self) -> Self:
        return on_black(self)

    def on_blue(self) -> Self:
        return on_blue(self)

    def on_cyan(self) -> Self:
        return on_cyan(self)

    def on_green(self) -> Self:
        return on_green(self)

    def on_magenta(self) -> Self:
        return on_magenta(self)

    def on_red(self) -> Self:
        return on_red(self)

    def on_white(self) -> Self:
        return on_white(self)

    def on_yellow(self) -> Self:
        return on_yellow(self)

    def underlined(self) -> Self:
        return underlined(self)

    def visual_len(self) -> int:
        """The apparent visual length of this string in a terminal."""
        return visual_len(self)


def _apply_ansi_code(ansi_code: str, text: str) -> StyledStr:
    if no_color:
        return StyledStr(text)

    start = ESCAPE_BEGIN + ansi_code + ESCAPE_END
    end = STYLE_RESET
    text = _remove_regex("\033\\[0m$", text)
    text = (STYLE_RESET + start).join(text.split(STYLE_RESET))
    return StyledStr(start + text + end)


def _change_text_color(text: str, color_code: str) -> StyledStr:
    """Change the color of text to the given color code."""
    uncolored_fg = _remove_text_colors(text)
    return _apply_ansi_code(color_code, uncolored_fg)


def _change_background_color(text: str, color_code: str) -> StyledStr:
    """Change the background color of text to the given color code."""
    uncolored_bg = _remove_background_colors(text)
    return _apply_ansi_code(color_code, uncolored_bg)


def _remove_background_colors(text: str) -> StyledStr:
    """Remove all background coloring from the given text."""
    return _remove_regex(BACKGROUND_COLORS_REGEX, text)


def _remove_bold(text: str) -> StyledStr:
    """Remove all text modifications from the given text."""
    return _remove_regex(BOLD_REGEX, text)


def _remove_text_colors(text: str) -> StyledStr:
    """Remove all foreground coloring from the given text."""
    return _remove_regex(FOREGROUND_COLORS_REGEX, text)


def _remove_regex(regex: str, text: str) -> StyledStr:
    """Remove the given regex from the text."""
    text = str(text)
    if no_color:
        return StyledStr(text)
    return StyledStr(re.sub(regex, "", text))


def _remove_underline(text: str) -> StyledStr:
    """Remove underlining from the given text."""
    return _remove_regex(UNDERLINED_REGEX, text)


def black(text: str) -> StyledStr:
    return _change_text_color(text, AnsiCode.BLACK_TEXT)


def blue(text: str) -> StyledStr:
    return _change_text_color(text, AnsiCode.BLUE_TEXT)


def bold(text: str) -> StyledStr:
    non_bold = _remove_bold(text)
    return _apply_ansi_code(AnsiCode.BOLD, non_bold)


def cyan(text: str) -> StyledStr:
    return _change_text_color(text, AnsiCode.CYAN_TEXT)


def green(text: str) -> StyledStr:
    return _change_text_color(text, AnsiCode.GREEN_TEXT)


def magenta(text: str) -> StyledStr:
    return _change_text_color(text, AnsiCode.MAGENTA_TEXT)


def red(text: str) -> StyledStr:
    return _change_text_color(text, AnsiCode.RED_TEXT)


def white(text: str) -> StyledStr:
    return _change_text_color(text, AnsiCode.WHITE_TEXT)


def yellow(text: str) -> StyledStr:
    return _change_text_color(text, AnsiCode.YELLOW_TEXT)


def on_black(text: str) -> StyledStr:
    return _change_background_color(text, AnsiCode.BLACK_BACKGROUND)


def on_blue(text: str) -> StyledStr:
    return _change_background_color(text, AnsiCode.BLUE_BACKGROUND)


def on_cyan(text: str) -> StyledStr:
    return _change_background_color(text, AnsiCode.CYAN_BACKGROUND)


def on_green(text: str) -> StyledStr:
    return _change_background_color(text, AnsiCode.GREEN_BACKGROUND)


def on_magenta(text: str) -> StyledStr:
    return _change_background_color(text, AnsiCode.MAGENTA_BACKGROUND)


def on_red(text: str) -> StyledStr:
    return _change_background_color(text, AnsiCode.RED_BACKGROUND)


def on_white(text: str) -> StyledStr:
    return _change_background_color(text, AnsiCode.WHITE_BACKGROUND)


def on_yellow(text: str) -> StyledStr:
    return _change_background_color(text, AnsiCode.YELLOW_BACKGROUND)


def underlined(text: str) -> StyledStr:
    non_underlined = _remove_underline(text)
    return _apply_ansi_code(AnsiCode.UNDERLINE, non_underlined)


ESCAPE_BEGIN = "\033["
ESCAPE_END = "m"
STYLE_RESET = "\033[0m"
FOREGROUND_COLORS_REGEX = "\033\\[3[0-9]m"
BACKGROUND_COLORS_REGEX = "\033\\[4[0-9]m"
BOLD_REGEX = "\033\\[1m"
UNDERLINED_REGEX = "\033\\[4m"
INVERTED_REGEX = "\033\\[7m"


class AnsiCode:
    BLACK_BACKGROUND = "40"
    BLACK_TEXT = "30"
    BLUE_BACKGROUND = "44"
    BLUE_TEXT = "34"
    CYAN_BACKGROUND = "46"
    CYAN_TEXT = "36"
    BOLD = "1"
    GREEN_BACKGROUND = "42"
    GREEN_TEXT = "32"
    MAGENTA_BACKGROUND = "45"
    MAGENTA_TEXT = "35"
    RED_BACKGROUND = "41"
    RED_TEXT = "31"
    WHITE_BACKGROUND = "47"
    WHITE_TEXT = "37"
    YELLOW_BACKGROUND = "43"
    YELLOW_TEXT = "33"
    NORMAL = "0"
    UNDERLINE = "4"
