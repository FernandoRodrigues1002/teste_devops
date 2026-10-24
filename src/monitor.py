import logging
import os
import signal
import sys
import threading
import time
from dataclasses import dataclass
from typing import List, Optional

import requests

logger = logging.getLogger("monitor")
stop_event = threading.Event()


@dataclass
class Config:
    urls: List[str]
    interval: float
    timeout: float
    run_once: bool
    log_file: Optional[str]
    log_level: str
    log_file_level: str


@dataclass
class CheckResult:
    url: str
    ok: bool
    status: str  # HTTP ou erro (TIMEOUT, etc)
    elapsed_ms: float


# valida a configuração a partir do env
def load_config() -> Config:
    raw_urls = os.getenv("URLS", "")
    urls = [u.strip() for u in raw_urls.split(",") if u.strip()]
    if not urls:
        raise ValueError("Nenhuma URL informada. Defina a variável URLS "
                         "(ex.: URLS='https://google.com,https://github.com').")

    invalid = [u for u in urls if not u.lower().startswith(("http://", "https://"))]
    if invalid:
        raise ValueError(f"URLs inválidas (devem começar com http:// ou https://): {invalid}")

    def positive_number(name: str, default: str) -> float:
        value = os.getenv(name, default)
        try:
            number = float(value)
        except ValueError:
            raise ValueError(f"{name} deve ser um número, recebido: '{value}'")
        if number <= 0:
            raise ValueError(f"{name} deve ser maior que zero, recebido: {number}")
        return number

    def valid_level(name: str, default: str) -> str:
        level = os.getenv(name, default).upper()
        if level not in ("INFO", "ERROR"):
            raise ValueError(f"{name} inválido: '{level}'")
        return level

    level = valid_level("LOG_LEVEL", "INFO")
    file_level = valid_level("LOG_FILE_LEVEL", level)

    return Config(
        urls=urls,
        interval=positive_number("INTERVAL", "30"),
        timeout=positive_number("TIMEOUT", "5"),
        run_once=os.getenv("RUN_ONCE", "false").strip().lower() in ("1", "true", "yes"),
        log_file=os.getenv("LOG_FILE") or None,
        log_level=level,
        log_file_level=file_level,
    )


def setup_logging(config: Config) -> None:
    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(config.log_level)
    handlers = [console]

    if config.log_file:
        file_handler = logging.FileHandler(config.log_file, encoding="utf-8")
        file_handler.setLevel(config.log_file_level)
        handlers.append(file_handler)

    for handler in handlers:
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    # O logger deixa tudo passar; cada handler filtra pelo seu próprio nível
    logger.setLevel(logging.DEBUG)


def check_url(url: str, timeout: float) -> CheckResult:
    start = time.perf_counter()
    try:
        response = requests.get(url, timeout=timeout)
        elapsed = (time.perf_counter() - start) * 1000
        # 2xx e 3xx contam como sucesso também
        ok = response.status_code < 400
        return CheckResult(url, ok, str(response.status_code), elapsed)

    except requests.exceptions.Timeout:
        status = "TIMEOUT"
    except requests.exceptions.SSLError:
        status = "SSL_ERROR"
    except requests.exceptions.ConnectionError:
        status = "CONNECTION_ERROR"
    except requests.exceptions.RequestException as exc:
        status = f"ERROR({type(exc).__name__})"
    elapsed = (time.perf_counter() - start) * 1000
    return CheckResult(url, False, status, elapsed)


def log_result(result: CheckResult) -> None:
    message = (f"url={result.url} status={result.status} "
               f"time={result.elapsed_ms:.0f}ms result={'OK' if result.ok else 'FAIL'}")
    logger.log(logging.INFO if result.ok else logging.ERROR, message)


def run_round(config: Config) -> bool:
    all_ok = True
    for url in config.urls:
        if stop_event.is_set():
            break
        result = check_url(url, config.timeout)
        log_result(result)
        all_ok = all_ok and result.ok
    return all_ok


def handle_signal(signum, _frame) -> None:
    logger.info("Sinal %s recebido, encerrando...", signal.Signals(signum).name)
    stop_event.set()


def main() -> int:
    try:
        config = load_config()
    except ValueError as exc:
        print(f"[ERRO DE CONFIGURAÇÃO] {exc}", file=sys.stderr)
        return 1

    setup_logging(config)
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    mode = "execução única" if config.run_once else f"contínuo (a cada {config.interval:g}s)"
    logger.info("Monitor iniciado | modo=%s timeout=%gs urls=%s",
                mode, config.timeout, config.urls)

    if config.run_once:
        return 0 if run_round(config) else 2

    while not stop_event.is_set():
        run_round(config)
        stop_event.wait(config.interval)

    logger.info("Monitor finalizado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
