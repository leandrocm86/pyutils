# Mais cores em https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT75fjCYt2l_dPGNNJcUj-nCjMSEgaCK1blGJcNR83oz8k47qFsWgF1Hw&s=10

from enum import Enum, auto
from typing import Callable, Optional
import re
import shutil

from utils.pipe import Pipeable


class Format(Enum):
    NORMAL = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Alignment(Enum):
    LEFT = auto()
    CENTER = auto()
    RIGHT = auto()

    def align_text(self, line: str, line_width: int):
        visible_length = get_visible_length(line)
        padding_width = line_width + (len(line) - visible_length)
        match self:
            case Alignment.CENTER:
                return line.center(padding_width)
            case Alignment.RIGHT:
                return line.rjust(padding_width)
            case Alignment.LEFT:
                return line.ljust(padding_width)


class Color(Enum):
    LOW_BLACK = '\033[30m'
    LOW_RED = '\033[31m'
    LOW_GREEN = '\033[32m'
    LOW_YELLOW = '\033[33m'
    LOW_BLUE = '\033[34m'
    LOW_MAGENTA = '\033[35m'
    LOW_CYAN = '\033[36m'
    LOW_WHITE = '\033[37m'

    RED = '\033[38;5;009m'
    GREEN = '\033[38;5;82m'
    YELLOW = '\033[38;5;011m'
    BLUE = '\033[38;5;39m'
    MAGENTA = '\033[38;5;165m'
    CYAN = '\033[38;5;87m'
    ORANGE = '\033[38;5;208m'


class BGCOLOR(Enum):
    BLACK = '\033[40m'
    RED = '\033[41m'
    GREEN = '\033[42m'
    YELLOW = '\033[43m'
    BLUE = '\033[44m'
    MAGENTA = '\033[45m'
    CYAN = '\033[46m'
    WHITE = '\033[47m'
    GRAY = '\033[48;5;240m'
    BRIGHT_YELLOW = '\033[48;5;214m'


Painter = Callable[[str], str]

def get_painter(color: Optional[Color] = None,
                background: Optional[BGCOLOR] = None,
                format: Optional[Format] = None
                ) -> Callable[[str], str]:
    var_prefix = ''
    if color:
        var_prefix = color.value
    if background:
        var_prefix += background.value
    if format:
        var_prefix += format.value

    def painter(text: str) -> str:
        text = text.replace('\033[0m', '\033[0m' + var_prefix)
        return f'{var_prefix}{text}\033[0m'
    return painter


@Pipeable
def red(text: str) -> str:
    painter = get_painter(Color.RED)
    return painter(text)


@Pipeable
def green(text: str) -> str:
    painter = get_painter(Color.GREEN)
    return painter(text)


@Pipeable
def yellow(text: str) -> str:
    painter = get_painter(Color.YELLOW)
    return painter(text)


@Pipeable
def blue(text: str) -> str:
    painter = get_painter(Color.BLUE)
    return painter(text)


@Pipeable
def magenta(text: str) -> str:
    painter = get_painter(Color.MAGENTA)
    return painter(text)


@Pipeable
def cyan(text: str) -> str:
    painter = get_painter(Color.CYAN)
    return painter(text)


@Pipeable
def orange(text: str) -> str:
    painter = get_painter(Color.ORANGE)
    return painter(text)


@Pipeable
def gray(text: str) -> str:
    painter = get_painter(Color.LOW_WHITE)
    return painter(text)


@Pipeable
def bold(text: str) -> str:
    painter = get_painter(format=Format.BOLD)
    return painter(text)


@Pipeable
def underline(text: str) -> str:
    painter = get_painter(format=Format.UNDERLINE)
    return painter(text)


def get_visible_length(text: str) -> int:
    return len(re.sub(r'\033\[[0-9;]*m', '', text))


def create_panel(content: str,
                 title: Optional[str] = None,
                 color: Optional[Color] = None,
                 padding: int = 0,
                 expand: bool = True,
                 width: Optional[int] = None,
                 align: Alignment = Alignment.LEFT) -> str:
    """
    Create a simple text panel with borders.

    Args:
        content (str): The text content to display
        title (str, optional): Title to display at the top
        color (int, optional): ANSI color code or name
        padding (int): Padding around content (default: 1)
        expand (bool): Whether to expand to terminal width (default: True)
        width (int, optional): Fixed width for the panel
        align (enum): Text alignment - LEFT, CENTER or RIGHT (default: LEFT)

    Returns:
        str: The formatted panel as a string
    """

    terminal_width = shutil.get_terminal_size().columns
    content_lines: list[str] = content.strip().split('\n')
    max_content_width = max(get_visible_length(line) for line in content_lines) if content_lines else 0
    title_width = get_visible_length(title) if title else 0

    if not width and not expand:
        var_panel_width = max(max_content_width, title_width) + (padding * 2) + 2
    else:
        var_panel_width = width or terminal_width

    var_panel_width = max(var_panel_width, 8)  # Minimum for borders
    content_area_width = var_panel_width - 2  # Width excluding borders

    color_start = color.value if color else ''
    color_end = '\033[0m' if color else ''
    lines: list[str] = []

    # Top border with title
    if title:
        var_title_padded = f" {title} "
        if len(var_title_padded) > content_area_width - 2:
            var_title_padded = var_title_padded[:content_area_width - 5] + "... "

        title_start = (content_area_width - len(var_title_padded)) // 2
        var_top_line = "┌" + "─" * title_start + var_title_padded + "─" * \
            (content_area_width - title_start - len(var_title_padded)) + "┐"
    else:
        var_top_line = "┌" + "─" * content_area_width + "┐"

    lines.append(color_start + var_top_line + color_end)

    # Top padding
    for _ in range(padding):
        lines.append(color_start + "│" + color_end + " " * content_area_width
                     + color_start + "│" + color_end)

    def format_and_append(line: str):
        line_width = content_area_width - padding * 2
        aligned_line = align.align_text(line, line_width)
        padded_line = " " * padding + aligned_line + " " * padding
        lines.append(color_start + "│" + color_end +
                     padded_line + color_start + "│" + color_end)

    # Content lines
    for line in content_lines:
        # Wrap long lines
        if get_visible_length(line) > content_area_width - (padding * 2):
            wrapped_lines: list[str] = []
            var_remaining = line
            line_width = content_area_width - (padding * 2)

            while var_remaining:
                if len(var_remaining) <= line_width:
                    wrapped_lines.append(var_remaining)
                    break
                else:
                    # Find a good break point (space)
                    var_break_point = var_remaining.rfind(' ', 0, line_width)
                    if var_break_point == -1:
                        var_break_point = line_width
                    wrapped_lines.append(var_remaining[:var_break_point])
                    var_remaining = var_remaining[var_break_point:].lstrip()

            for wrapped_line in wrapped_lines:
                format_and_append(wrapped_line)
        else:
            format_and_append(line)

    # Bottom padding
    for _ in range(padding):
        lines.append(color_start + "│" + color_end + " " * content_area_width
                     + color_start + "│" + color_end)

    # Bottom border
    bottom_line = "└" + "─" * content_area_width + "┘"
    lines.append(color_start + bottom_line + color_end)

    return '\n'.join(lines)


if __name__ == '__main__':

    for color in Color:
        painter = get_painter(color)
        print(painter(f'{color.name} - Testando 123!'))

    for bg in BGCOLOR:
        painter = get_painter(background=bg)
        print(painter(f'{bg.name} - Testando 123!'))

    low_red = get_painter(Color.LOW_RED)
    print(low_red('Low Red!'))
    bold_low_red = get_painter(Color.LOW_RED, format=Format.BOLD)
    print(bold_low_red('Bold Low Red!'))
    print(red('Red!'))
    bold_red = get_painter(Color.RED, format=Format.BOLD)
    print(bold_red('Bold Red!'))
    underline_red = get_painter(Color.RED, format=Format.UNDERLINE)
    print(underline_red('Underline Red!'))

    white_background = get_painter(background=BGCOLOR.WHITE)
    print(white_background(red('Red on White!') + ' --- ' + green('Green on White!')))

    # Basic panel
    print(create_panel("Hello, World!"))
    print()

    # With title and color
    print(create_panel("This is important content", title="Warning", color=Color.RED))
    print()

    # Multi-line content
    content = """This is a multi-line panel
with several lines of text
that demonstrates wrapping.
And this is another very long text written in the same line without any linebreak. I repeat: And this is another very long text written in the same line without any linebreak."""
    print(create_panel(content, title="Info", color=Color.BLUE, padding=2))
    print()

    # Non-expanding panel
    print(create_panel("Compact panel", color=Color.GREEN, expand=False))
    print()

    # Centered text
    print(create_panel("This text is centered", title="Centered", color=Color.CYAN, align=Alignment.CENTER, padding=0))
    print()

    # Right-aligned text
    print(create_panel("Right aligned text", title="Right", color=Color.MAGENTA, align=Alignment.RIGHT))
