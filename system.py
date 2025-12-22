import subprocess
from typing import Any, Callable, Iterable, Optional

# A grande vantagem de usar este mod em vez de subprocess diretamente
# é que ele utiliza parâmetros padrão mais seguros:
# - check=True: lança exceção se o comando falhar (exit code != 0)
# - capture_output=True: retorna o output do comando e confere se está vazio quando esperado (exec)
# - timeout=10: tempo máximo de execução, evitando travamentos


def __run(cmd: str | Iterable[str],
          check: bool,
          capture_output: bool,
          timeout: Optional[float],
          logfunc: Optional[Callable[[str], None]]) -> subprocess.CompletedProcess[Any]:
    if logfunc:
        logfunc(f'Executing: {cmd}')
    shell = isinstance(cmd, str)
    result = subprocess.run(args=cmd, shell=shell, check=check, timeout=timeout, capture_output=capture_output, text=capture_output)  # type: ignore
    if logfunc:
        if result.stdout:
            logfunc(f'Stdout: {result.stdout}')
        if result.stderr:
            logfunc(f'Stderr: {result.stderr}')
    return result


def exec(cmd: str | Iterable[str],
         check: bool = True,
         ignore_output: bool = False,
         timeout: Optional[float] = 10,
         logfunc: Optional[Callable[[str], None]] = print):
    """
    Executa um comando onde nenhum output é esperado.
    Params:
        cmd: o comando a ser executado (se string, será executado com shell=True)
        check: se True, uma exceção será lançada se o comando falhar (exit code != 0)
        ignore_output: se False, uma exceção será lançada se houver qualquer output
        timeout: tempo máximo de execução em segundos (padrao 10)
        logfunc: função que recebe uma string para logar a execução do comando
    """
    result = __run(cmd, check, not ignore_output, timeout=timeout, logfunc=logfunc)
    if not ignore_output:
        assert not result.stdout and not result.stderr, \
            f'Output inesperado: stdout={result.stdout}; stderr={result.stderr}'


def read(cmd: str | Iterable[str],
         check: bool = True,
         timeout: Optional[float] = 10,
         logfunc: Optional[Callable[[str], None]] = print) -> str:
    """
    Executa um comando e retorna os outputs (stdout + stderr).
    Params:
        cmd: o comando a ser executado (se string, será executado com shell=True)
        check: se True, uma exceção será disparada se o comando falhar (exit code != 0)
        timeout: tempo máximo de execução em segundos (padrao 10)
        logfunc: função que recebe uma string para logar a execução do comando
    """
    result = __run(cmd, check, capture_output=True, timeout=timeout, logfunc=logfunc)
    return result.stdout.strip() + result.stderr.strip()


def exec_async(cmd: str | Iterable[str], logfunc: Optional[Callable[[str], None]] = print):
    """
    Execute the commands on the OS, not waiting for their output.
    It's not possible to check the output, nor setting a timeout.
    If cmd is a string, it will be executed with shell=True (not recommended if there's user input).
    """
    if logfunc:
        logfunc(f'Executing asynchronously: {cmd}')
    shell = isinstance(cmd, str)
    subprocess.Popen(args=cmd, shell=shell)  # type: ignore


def install_external_libs(*module_names: str):
    """
    Installs the given modules in the current system, using pip, if they are not already present.
    Params:
        module_names: The module names to import, as recognized by pip.
    Returns:
        The imported modules
    """
    import importlib
    for modname in module_names:
        try:
            importlib.import_module(modname)
        except ImportError:
            print(f'WARNING: Required module {modname} is not installed. Will try to install via pip...')
            import sys
            exec([sys.executable, '-m', 'pip', 'install', modname], ignore_output=True, timeout=120)
            print(f'Module {modname} installed successfully!')


def get_memory_from_proc() -> tuple[int, int, int]:
    try:
        with open('/proc/meminfo', 'r') as f:
            meminfo = {}
            for line in f:
                parts = line.split(':')
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip().split()[0]  # Get the number
                    meminfo[key] = int(value) * 1024  # Convert to bytes

            # Calculate available memory (approximation)
            # Different Linux kernels report memory differently
            total: int = meminfo.get('MemTotal', 0)
            available: int = meminfo.get('MemAvailable', 0)
            used: int = meminfo.get('MemUsed', 0)

            if available == 0:
                # Fallback calculation
                free = meminfo.get('MemFree', 0)
                buffers = meminfo.get('Buffers', 0)
                cached = meminfo.get('Cached', 0)
                available = free + buffers + cached

            return used, available, total

    except FileNotFoundError:
        print("Not running on Linux or /proc/meminfo not accessible")
        return 0, 0, 0
