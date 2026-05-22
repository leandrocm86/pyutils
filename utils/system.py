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


def exec_async(cmd: str | Iterable[str],
        logfunc: Optional[Callable[[str], None]] = print,
        envs_to_keep: Optional[set[str]] = None
):
    """
    Execute the commands on the OS, not waiting for their output.
    It's not possible to check the output, nor setting a timeout.
    If cmd is a string, it will be executed with shell=True (not recommended if there's user input).
    """
    shell = isinstance(cmd, str)
    
    values_by_envs: dict[str, str] = {}
    if envs_to_keep:
        from os import environ
        for name in envs_to_keep:
            if value := environ.get(name):
                values_by_envs[name] = value

    if logfunc:
        logfunc(f'Executing asynchronously: {cmd}. Envs preserved: {values_by_envs.keys()}')
    subprocess.Popen(args=cmd, shell=shell,  # type: ignore
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True, close_fds=True, env=values_by_envs)


def install_external_libs(*modules: str | dict, auto=False):
    """
    Installs the given modules in the current system, using pip, if they are not already present.
    Params:
        module_names: The module names to import, as recognized by pip.
            If the name of the module is the same as the pip package, only a string is necessary.
            Otherwise, a dict must be given where the imported modules are keys and install packages are values.
        auto: If True, automatically confirms installation when not in interactive mode.
    Returns:
        The imported modules
    """

    def install(modname: str, pipname: str):
        import importlib
        import os
        import sys

        CURRENT_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')  # por padrao loga tudo
        def printlog(msg: str, level: str):
            if level == 'DEBUG':
                if CURRENT_LEVEL == 'DEBUG':
                    print(f'[DEBUG] {msg}', flush=True)
            elif CURRENT_LEVEL != 'OFF':  # Assumindo que o ambiente, se definido, vai ser no minimo INFO
                print(f'[{level}] {msg}', flush=True)

        debug, warn = lambda x: printlog(x, 'DEBUG'), lambda x: printlog(x, 'WARN')
        try:
            debug(f"Loading external module {modname}...")
            importlib.import_module(modname)
        except ImportError:
            if sys.stdout.isatty():
                from . import bool_input
                isok = bool_input(f'WARNING: Required module {modname} is not installed. Should try to install {pipname} via pip?', default=True)
                if not isok:
                    return
            elif not auto:
                warn(f'WARNING: Required module {modname} is not installed!')
                return
            exec([sys.executable, '-m', 'pip', 'install', pipname], ignore_output=True, timeout=120)
            warn(f'Module {modname} installed successfully!')

    for module in modules:
        if isinstance(module, dict):
            for modulename, packagename in module.items():
                install(modulename, packagename)
        else:
            install(module, module)


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
