import subprocess
from typing import Iterable
from .log import LOG

# A grande vantagem de usar este mod em vez de subprocess diretamente
# é que ele utiliza parâmetros padrão mais seguros:
# - check=True: lança exceção se o comando falhar (exit code != 0)
# - capture_output=True: retorna o output do comando e confere se está vazio quando esperado (exec)
# - timeout=10: tempo máximo de execução, evitando travamentos


def _run(cmd: str | Iterable[str], check: bool, capture_output: bool,
        timeout: float = None) -> subprocess.CompletedProcess:
    LOG.debug(f'Executing: {cmd}')
    shell = isinstance(cmd, str)
    result = subprocess.run(cmd, shell=shell, check=check, timeout=timeout,
                            capture_output=capture_output, text=capture_output)
    LOG.debug(f'Result: {result}')
    return result


def exec(cmd: str | Iterable[str], check=True, ignore_output=False, timeout=10):
    """
    Executa um comando onde nenhum output é esperado.
    Params:
        cmd: o comando a ser executado (se string, será executado com shell=True)
        check: se True, uma exceção será lançada se o comando falhar (exit code != 0)
        ignore_output: se False, uma exceção será lançada se houver qualquer output
        timeout: tempo máximo de execução em segundos (padrao 10)
    """
    result = _run(cmd, check, not ignore_output, timeout=timeout)
    if not ignore_output:
        assert not result.stdout and not result.stderr, \
            f'Output inesperado: stdout={result.stdout}; stderr={result.stderr}'


def read(cmd: str | Iterable[str], check=True, timeout=10) -> str:
    """
    Executa um comando e retorna os outputs (stdout + stderr).
    Params:
        cmd: o comando a ser executado (se string, será executado com shell=True)
        check: se True, uma exceção será disparada se o comando falhar (exit code != 0)
        timeout: tempo máximo de execução em segundos (padrao 10)
    """
    result = _run(cmd, check, capture_output=True, timeout=timeout)
    return result.stdout.strip() + result.stderr.strip()


def exec_async(cmd: str | Iterable[str]):
    """
    Execute the commands on the OS, not waiting for their output.
    It's not possible to check the output, nor setting a timeout.
    If cmd is a string, it will be executed with shell=True (not recommended if there's user input).
    """
    LOG.debug(f'Executing asynchronously: {cmd}')
    shell = isinstance(cmd, str)
    subprocess.Popen(cmd, shell=shell)
