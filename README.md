Monitor de disponibilidade de serviços HTTP.

Configuração 100% via variáveis de ambiente (sem alterar o código):

    URLS       Lista de URLs separadas por vírgula (obrigatória)
    INTERVAL   Segundos entre cada rodada de checagens (padrão: 30)
    TIMEOUT    Timeout de cada requisição, em segundos (padrão: 5)
    RUN_ONCE   "true" executa uma única rodada e sai (padrão: false)
    LOG_FILE   Caminho de um arquivo de log opcional (padrão: só stdout)
    LOG_LEVEL  DEBUG, INFO, WARNING, ERROR (padrão: INFO)

Códigos de saída:
    0  encerrou normalmente (em RUN_ONCE, todas as URLs OK)
    1  configuração inválida
    2  RUN_ONCE e pelo menos uma URL falhou

    set URLS=https://google.com,https://github.com && set INTERVAL=10 && python src\monitor.py