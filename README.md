# Monitor de disponibilidade de serviços HTTP.

# ::Configuração 100% via variáveis de ambiente (sem alterar o código):

    URLS       Lista de URLs separadas por vírgula (obrigatória)
    INTERVAL   Segundos entre cada rodada de checagens (padrão: 30)
    TIMEOUT    Timeout de cada requisição, em segundos (padrão: 5)
    RUN_ONCE   "true" executa uma única rodada e sai (padrão: false)
    LOG_LEVEL  INFO, ERROR (padrão: INFO)
    LOG_FILE   Caminho de um arquivo de log temporario (padrão: só stdout)
    LOG_FILE_LEVEL   INFO, ERROR (padrão: INFO)

# ::Códigos de saída:
    0  encerrou normalmente (em RUN_ONCE, todas as URLs OK)
    1  configuração inválida
    2  RUN_ONCE e pelo menos uma URL falhou

    set URLS=https://google.com,https://github.com && set INTERVAL=10 && python src\monitor.py

# Comandos Docker

    :: 1. Build da imagem
    docker build -t <nome-img> .

    :: 2. Criar e iniciar o container, lendo o .env
    docker run -d --name <nome-container> --env-file .env <nome-img>

    :: 3. Acompanhar os logs em tempo real
    docker logs -f <nome-container>

    :: 4. Parar e remover
    docker stop <nome-container>
    docker rm <nome-container>

    :: Ver o arquivo temporário de log
    docker exec monitor cat <caminho do LOG_FILE>