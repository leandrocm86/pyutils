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
            exec([sys.executable, '-m', 'pip', 'install', modname], ignore_output=True)
            print(f'Module {modname} installed successfully!')
