import sys
from pathlib import Path

import pytest

from utils.system import package_resource


@pytest.fixture
def fakepkg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    var_pkg = tmp_path / "fakepkg"
    var_pkg.mkdir()
    (var_pkg / "__init__.py").write_text("")
    (var_pkg / "dados.txt").write_text("oi")
    monkeypatch.syspath_prepend(str(tmp_path))
    return var_pkg


def test_fonte(fakepkg: Path) -> None:
    assert package_resource("fakepkg", "dados.txt").read_text() == "oi"
    assert package_resource("fakepkg", "dados.txt").is_absolute()


def test_nao_encontrado_lista_sondados(fakepkg: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Caminhos sondados"):
        package_resource("fakepkg", "nao-existe.txt")


def test_pacote_vazio() -> None:
    with pytest.raises(ValueError, match="vazio"):
        package_resource("  ", "x")


def test_env_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    var_alvo = tmp_path / "fora"
    var_alvo.mkdir()
    monkeypatch.setenv("PYUTILS_TESTE_DIR", str(var_alvo))
    assert package_resource("qualquer", "x", env_var="PYUTILS_TESTE_DIR") == var_alvo


def test_env_override_inexistente(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYUTILS_TESTE_DIR", "/nao/existe/aqui")
    with pytest.raises(FileNotFoundError, match="PYUTILS_TESTE_DIR"):
        package_resource("qualquer", "x", env_var="PYUTILS_TESTE_DIR")


def test_frozen_meipass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    var_base = tmp_path / "bundle"
    (var_base / "fakepkg").mkdir(parents=True)
    (var_base / "fakepkg" / "dados.txt").write_text("congelado")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(var_base), raising=False)
    assert package_resource("fakepkg", "dados.txt").read_text() == "congelado"


def test_frozen_layout_flat(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    var_base = tmp_path / "bundle"
    var_base.mkdir()
    (var_base / "dados.txt").write_text("flat")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(var_base), raising=False)
    assert package_resource("fakepkg", "dados.txt").read_text() == "flat"
