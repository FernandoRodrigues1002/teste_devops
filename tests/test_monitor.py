from unittest.mock import MagicMock, patch

import pytest
import requests

import monitor


# ---------- load_config ----------

def test_config_valida(monkeypatch):
    monkeypatch.setenv("URLS", " https://a.com , https://b.com ")
    monkeypatch.setenv("INTERVAL", "10")
    config = monitor.load_config()
    assert config.urls == ["https://a.com", "https://b.com"]  # strip funcionou
    assert config.interval == 10
    assert config.timeout == 5            # valor padrão
    assert config.run_once is False       # valor padrão


def test_config_sem_urls(monkeypatch):
    monkeypatch.delenv("URLS", raising=False)
    with pytest.raises(ValueError):
        monitor.load_config()


def test_config_url_invalida(monkeypatch):
    monkeypatch.setenv("URLS", "google.com")
    with pytest.raises(ValueError):
        monitor.load_config()


def test_config_intervalo_nao_numerico(monkeypatch):
    monkeypatch.setenv("URLS", "https://a.com")
    monkeypatch.setenv("INTERVAL", "abc")
    with pytest.raises(ValueError):
        monitor.load_config()


def test_config_intervalo_negativo(monkeypatch):
    monkeypatch.setenv("URLS", "https://a.com")
    monkeypatch.setenv("INTERVAL", "-5")
    with pytest.raises(ValueError):
        monitor.load_config()


@pytest.mark.parametrize("valor, esperado", [
    ("true", True), ("1", True), ("YES", True), ("false", False), ("abc", False),
])
def test_config_run_once(monkeypatch, valor, esperado):
    monkeypatch.setenv("URLS", "https://a.com")
    monkeypatch.setenv("RUN_ONCE", valor)
    assert monitor.load_config().run_once is esperado


# ---------- check_url (requests.get é simulado, sem internet) ----------

def _resposta(status_code):
    resposta = MagicMock()
    resposta.status_code = status_code
    return resposta


def test_check_url_sucesso():
    with patch("monitor.requests.get", return_value=_resposta(200)):
        result = monitor.check_url("https://a.com", timeout=5)
    assert result.ok is True
    assert result.status == "200"
    assert result.elapsed_ms >= 0


def test_check_url_erro_500():
    with patch("monitor.requests.get", return_value=_resposta(500)):
        result = monitor.check_url("https://a.com", timeout=5)
    assert result.ok is False
    assert result.status == "500"


@pytest.mark.parametrize("excecao, status_esperado", [
    (requests.exceptions.Timeout(), "TIMEOUT"),
    (requests.exceptions.ConnectionError(), "CONNECTION_ERROR"),
    (requests.exceptions.SSLError(), "SSL_ERROR"),
])
def test_check_url_excecoes(excecao, status_esperado):
    with patch("monitor.requests.get", side_effect=excecao):
        result = monitor.check_url("https://a.com", timeout=5)
    assert result.ok is False
    assert result.status == status_esperado


# ---------- run_round ----------

def test_run_round_todas_ok(monkeypatch):
    monkeypatch.setenv("URLS", "https://a.com,https://b.com")
    config = monitor.load_config()
    with patch("monitor.requests.get", return_value=_resposta(200)):
        assert monitor.run_round(config) is True


def test_run_round_com_falha(monkeypatch):
    monkeypatch.setenv("URLS", "https://a.com,https://b.com")
    config = monitor.load_config()
    respostas = [_resposta(200), _resposta(503)]
    with patch("monitor.requests.get", side_effect=respostas):
        assert monitor.run_round(config) is False