from enum import Enum
from typing import Callable


class Format(Enum):
    NORMAL = 0
    BOLD = 1
    UNDERLINE = 4


class Low(Enum):
    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37


class BG(Enum):
    BLACK = 40
    RED = 41
    GREEN = 42
    YELLOW = 43
    BLUE = 44
    MAGENTA = 45
    CYAN = 46
    WHITE = 47


class Bright(Enum):
    RED = 196
    GREEN = 82
    YELLOW = 190
    BLUE = 39
    MAGENTA = 165
    CYAN = 87


def get_painter(color: int | Low | Bright = 0,
                background: int | BG = 0,
                format: int | Format = 0
                ) -> Callable[[str], str]:
    prefix = ''
    if color:
        color = color if isinstance(color, int) else color.value
        assert 0 < color < 256 and color not in BG and color not in Format, \
            'Invalid text color!'
        prefix = f"{'\033[38;5;' if color in Bright else '\033['}{color}m"
    if background:
        assert background in BG, 'Invalid background color!'
        background = background if isinstance(background, int) else background.value
        prefix += f'\033[{background}m'
    if format:
        assert format in Format, 'Invalid format!'
        format = format if isinstance(format, int) else format.value
        prefix += f'\033[{format}m'

    def painter(text: str) -> str:
        text = text.replace('\033[0m', '\033[0m' + prefix)
        return f'{prefix}{text}\033[0m'
    return painter


def red(text: str) -> str:
    painter = get_painter(Bright.RED)
    return painter(text)


def green(text: str) -> str:
    painter = get_painter(Bright.GREEN)
    return painter(text)


def yellow(text: str) -> str:
    painter = get_painter(Bright.YELLOW)
    return painter(text)


def blue(text: str) -> str:
    painter = get_painter(Bright.BLUE)
    return painter(text)


def magenta(text: str) -> str:
    painter = get_painter(Bright.MAGENTA)
    return painter(text)


def cyan(text: str) -> str:
    painter = get_painter(Bright.CYAN)
    return painter(text)


if __name__ == '__main__':

    for low in Low:
        painter = get_painter(low.value)
        print(painter(f'{low.name} - Testando 123!'))

    for bg in BG:
        painter = get_painter(background=bg.value)
        print(painter(f'{bg.name} - Testando 123!'))

    for bright in Bright:
        painter = get_painter(bright.value)
        print(painter(f'{bright.name} - Testando 123!'))

    black = get_painter(Low.BLACK.value)
    print(black('Black!'))
    print(red('Red!'))
    print(green('Green!'))
    print(yellow('Yellow!'))
    print(blue('Blue!'))
    print(magenta('Magenta!'))
    print(cyan('Cyan!'))
    white = get_painter(Low.WHITE)
    print(white('White!'))
    black_on_white = get_painter(Low.BLACK, BG.WHITE)
    print(black_on_white('Black on White!'))
    red_on_blue = get_painter(Low.RED, BG.BLUE)
    print(red_on_blue('Red on Blue!'))

    low_red = get_painter(Low.RED)
    print(low_red('Low Red!'))
    bold_low_red = get_painter(Low.RED, format=Format.BOLD)
    print(bold_low_red('Bold Low Red!'))
    print(red('Red!'))
    bold_red = get_painter(Bright.RED, format=Format.BOLD)
    print(bold_red('Bold Red!'))
    underline_red = get_painter(Bright.RED, format=Format.UNDERLINE)
    print(underline_red('Underline Red!'))

    white_background = get_painter(background=BG.WHITE)
    print(white_background(red('Red on White!') + ' --- ' + green('Green on White!')))
