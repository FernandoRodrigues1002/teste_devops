# Monitor de Disponibilidade de URLs

Serviço em Python que consulta URLs HTTP periodicamente, identifica sucessos e falhas, mede o tempo de resposta e registra tudo em logs. Empacotado em Docker, validado e publicado automaticamente por uma pipeline no GitHub Actions.

> Desafio técnico DevOps Júnior: Python, Docker, GitHub Actions e IA.

## Sumário

- [Objetivo e tecnologias](#objetivo-e-tecnologias)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Configuração](#configuração)
- [Execução local](#execução-local)
- [Execução via Docker](#execução-via-docker)
- [Logs](#logs)
- [Como o código funciona](#como-o-código-funciona)
- [Testes e qualidade de código](#testes-e-qualidade-de-código)
- [Pipeline CI/CD](#pipeline-cicd)
- [Principais dificuldades e soluções](#principais-dificuldades-e-soluções)
- [Uso de IA no desenvolvimento](#uso-de-ia-no-desenvolvimento)
- [Limitações e melhorias futuras](#limitações-e-melhorias-futuras)

## Objetivo e tecnologias

O monitor faz requisições GET para uma lista de URLs e, a cada rodada, registra para cada uma:

- data e hora;
- URL consultada;
- status (código HTTP ou tipo de erro: `TIMEOUT`, `CONNECTION_ERROR`, `SSL_ERROR`);
- tempo de resposta em milissegundos;
- resultado (`OK` ou `FAIL`).


| Tecnologia | Uso |
|---|---|
| Python 3.12 | linguagem da aplicação |
| `requests` | requisições HTTP |
| `logging` (biblioteca padrão) | registro dos resultados |
| Docker | empacotamento e execução padronizada |
| GitHub Actions | lint, testes, build e publicação |
| GitHub Container Registry (GHCR) | armazenamento da imagem |
| pytest / flake8 | testes automatizados e análise de código |

## Estrutura do projeto

```
.
├── .github/workflows/ci-cd.yml   # pipeline
├── src/
│   └── monitor.py                # aplicação
├── tests/
│   └── test_monitor.py           # testes automatizados
├── .dockerignore
├── .env.example                  # modelo de configuração
├── .gitignore
├── Dockerfile
├── pytest.ini                    # configuração do pytest
├── requirements.txt              # dependências de execução
└── requirements-dev.txt          # dependências de desenvolvimento (testes e lint)
```

`requirements.txt` e `requirements-dev.txt` são separados de propósito: a imagem Docker instala apenas o primeiro, então pytest e flake8 não vão para a imagem final (menor e com menos pacotes expostos).

## Configuração

Toda a configuração é feita por **variáveis de ambiente**, sem alterar o código. A mesma imagem funciona em qualquer ambiente, e só a configuração muda.

| Variável | Padrão | Descrição |
|---|---|---|
| `URLS` | *(obrigatória)* | URLs separadas por vírgula, iniciando com `http://` ou `https://`. Espaços ao redor são ignorados |
| `INTERVAL` | `30` | Segundos entre cada rodada de checagens. Deve ser maior que zero |
| `TIMEOUT` | `5` | Tempo máximo de espera por requisição, em segundos. Deve ser maior que zero |
| `RUN_ONCE` | `false` | Com `true`, `1` ou `yes`, executa uma única rodada e encerra |
| `LOG_LEVEL` | `INFO` | Nível do log no terminal: `INFO` (tudo) ou `ERROR` (só falhas) |
| `LOG_FILE` | *(vazio)* | Caminho de um arquivo de log. Se vazio, não cria arquivo |
| `LOG_FILE_LEVEL` | igual ao `LOG_LEVEL` | Nível do log no arquivo: `INFO` ou `ERROR`. Só tem efeito com `LOG_FILE` |

Se a configuração for inválida (sem URLs, URL sem `http(s)://`, número inválido, nível desconhecido), o programa não inicia.

### Arquivo `.env`

Exemplo de `.env`:

```env
URLS=https://google.com,https://github.com
INTERVAL=30
TIMEOUT=5
LOG_LEVEL=INFO
```

### Modos de execução

| Modo | Como ativar | Comportamento |
|---|---|---|
| Contínuo (padrão) | nenhuma variável extra | checa todas as URLs a cada `INTERVAL` segundos até receber Ctrl+C ou SIGTERM |
| Sob demanda | `RUN_ONCE=true` | uma rodada e encerra |

### Códigos de saída

| Código | Significado |
|---|---|
| `0` | encerrou normalmente (em `RUN_ONCE`, todas as URLs estavam OK) |
| `1` | configuração inválida |
| `2` | `RUN_ONCE` e pelo menos uma URL falhou |

## Execução local

Requisitos: Python 3.12 ou superior.

```bash
pip install -r requirements.txt
```

**Linux / macOS:**

```bash
URLS="https://google.com,https://github.com" INTERVAL=10 python src/monitor.py
```

**Windows (cmd):**

```cmd
set URLS=https://google.com,https://github.com && set INTERVAL=10 && python src\monitor.py
```

**Windows (PowerShell):**

```powershell
$env:URLS="https://google.com,https://github.com"; $env:INTERVAL="10"; python src/monitor.py
```

Uma única rodada (sob demanda):

```bash
URLS="https://google.com" RUN_ONCE=true python src/monitor.py
```


## Execução via Docker

### Build da imagem

```bash
docker build -t < nome da imagem > < caminho da imagem >
```

### Executar o container

Com o `.env` configurado:

```bash
docker run -d --name < nome do container > --env-file .env < nome da imagem >
```

Ou passando as variáveis direto no comando:

```bash
docker run -d --name < nome do container > -e URLS="https://google.com,https://github.com" -e INTERVAL=10 < nome da imagem >
```

### Acompanhar, parar e remover

```bash
docker logs -f monitor
docker stop monitor
docker rm monitor
```

Execução única, descartando o container ao final:

```bash
docker run --rm --env-file .env -e RUN_ONCE=true < nome da imagem >
```

### Usar a imagem publicada no GHCR

Sem precisar de build local:

```bash
docker pull ghcr.io/fernandorodrigues1002/teste_devops:latest
docker run -d --name < nome do container > --env-file .env ghcr.io/fernandorodrigues1002/teste_devops:latest
```

### Detalhes do Dockerfile

- O processo roda como **usuário não root** (`appuser`), seguindo o princípio do menor privilégio.
- O `.env` não é copiado para a imagem (está no `.dockerignore`).

## Logs

Por padrão, os logs vão para a saída padrão (stdout), que é o padrão em containers: o `docker logs` os coleta.

### Exemplo de saída

Os valores de tempo variam a cada execução:

```
2026-10-24 10:15:00 | INFO    | Monitor iniciado | modo=contínuo (a cada 30s) timeout=5s urls=['https://google.com', 'https://github.com']
2026-10-24 10:15:00 | INFO    | url=https://google.com status=200 time=312ms result=OK
2026-10-24 10:15:01 | INFO    | url=https://github.com status=200 time=487ms result=OK
2026-10-24 10:15:31 | ERROR   | url=https://exemplo-fora-do-ar.com status=TIMEOUT time=5003ms result=FAIL
2026-10-24 10:15:31 | ERROR   | url=https://site-inexistente.invalid status=CONNECTION_ERROR time=24ms result=FAIL
2026-10-24 10:15:45 | INFO    | Sinal SIGTERM recebido, encerrando...
2026-10-24 10:15:45 | INFO    | Monitor finalizado.
```

Sucessos são registrados com nível `INFO` e falhas com nível `ERROR`. O resultado é `OK` para códigos HTTP abaixo de 400 e `FAIL` para 4xx, 5xx, timeout ou erro de conexão.

### Arquivo de log (opcional)


| `LOG_LEVEL` | `LOG_FILE_LEVEL` | Terminal | Arquivo |
|---|---|---|---|
| `INFO` | não definido | tudo | tudo |
| `INFO` | `ERROR` | tudo | só erros |
| `ERROR` | `INFO` | só erros | tudo |
| `ERROR` | não definido | só erros | só erros |

Em container, o processo roda sem privilégios de root e só consegue gravar em pastas onde tenha permissão. Por isso:

- **Arquivo dentro do container:** use um caminho gravável, como `LOG_FILE=/tmp/monitor.log`. O arquivo existe só dentro do container e some quando ele é removido. Para ler: `docker exec monitor cat /tmp/monitor.log`.
- **Caminhos como `/app/monitor.log` ou `/temp/...` falham:**.
- **Arquivo persistente no computador:** exige uma pasta gravável pelo usuário do container e um volume (`-v`) ligando-a a uma pasta local.

Sem o volume, o arquivo é descartado junto com o container.

## Como o código funciona

O arquivo `src/monitor.py` é organizado em funções pequenas, cada uma com uma responsabilidade:

| Elemento | Função |
|---|---|
| `Config` (dataclass) | agrupa a configuração validada: URLs, intervalo, timeout, modo e níveis de log |
| `CheckResult` (dataclass) | agrupa o resultado de uma checagem: URL, ok ou não, status e tempo |
| `load_config()` | lê as variáveis de ambiente, aplica os valores padrão, valida e devolve um `Config`. Levanta `ValueError` com mensagem clara se algo estiver errado |
| `setup_logging()` | configura o formato do log e os destinos (terminal e, opcionalmente, arquivo), cada um com seu próprio nível |
| `check_url()` | faz o GET com timeout, mede o tempo com `time.perf_counter()` e classifica o resultado. Trata `Timeout`, `ConnectionError`, `SSLError` e qualquer outro erro do `requests` sem derrubar o programa |
| `log_result()` | formata a linha de log e escolhe o nível: `INFO` se OK, `ERROR` se falhou |
| `run_round()` | percorre todas as URLs, registra cada resultado e devolve se todas estavam OK |
| `handle_signal()` | acionada por `SIGINT` (Ctrl+C) e `SIGTERM` (`docker stop`); levanta uma flag de encerramento |
| `main()` | carrega a configuração, prepara o log, registra os sinais e executa o modo único ou o loop contínuo |

## Testes e qualidade de código

Instalação das dependências de desenvolvimento:

```bash
pip install -r requirements-dev.txt
```

Execução:

```bash
python -m flake8 src tests --max-line-length=100
python -m pytest
```

- **flake8:** analisa sintaxe e estilo sem executar o código (imports não usados, erros de sintaxe, formatação).
- **pytest:** executa 17 testes automatizados em `tests/test_monitor.py`:
  - `load_config`: configuração válida, ausência de `URLS`, URL sem `http(s)://`, intervalo não numérico ou negativo, conversão do `RUN_ONCE`;
  - `check_url`: sucesso, erro 500, `Timeout`, `ConnectionError` e `SSLError`;
  - `run_round`: todas OK e com falha.
- **Sem internet nos testes:** `requests.get` é substituído por um objeto simulado (*mock*). Os testes ficam rápidos e determinísticos, sem depender de nenhum site estar no ar.
- O `pytest.ini` define `pythonpath = src` (para o `import monitor` funcionar) e `testpaths = tests`.

## Pipeline CI/CD

O workflow está em `.github/workflows/ci-cd.yml`.

### Quando executa

| Evento | Executa? | Publica a imagem? |
|---|---|---|
| Pull Request | sim | **não** |
| Push na `main` | sim | **sim** |

### Jobs

Os jobs rodam em sequência: o segundo só executa se o primeiro passar (`needs: test`).

**1. `Lint e testes`**

| Passo | O que faz |
|---|---|
| Checkout | baixa o código do repositório na máquina do job |
| Configurar Python | instala o Python 3.12 e guarda cache do pip |
| Instalar dependências | `pip install -r requirements-dev.txt` |
| Lint | `flake8 src tests --max-line-length=100` |
| Testes | `pytest` |

**2. `Build e publicação da imagem`**

| Passo | O que faz |
|---|---|
| Checkout | baixa o código (cada job roda em uma máquina nova e vazia) |
| Configurar Docker Buildx | prepara o motor de build |
| Login no GHCR | só em push (nunca em PR), usando o `GITHUB_TOKEN` |
| Gerar tags e labels | define os nomes e metadados da imagem |
| Build e push | constrói a imagem; só envia ao GHCR se o evento for push |

### Tags da imagem

A imagem é publicada em `ghcr.io/fernandorodrigues1002/teste_devops` com duas tags:

| Tag | Significado |
|---|---|
| `latest` | versão mais recente da `main` |
| `sha-<commit>` | fixa a versão de um commit específico, permitindo rastrear a origem e voltar a uma versão anterior |

### Segurança da pipeline

- **Sem credenciais no repositório.** A autenticação usa o `GITHUB_TOKEN`, gerado automaticamente pelo GitHub a cada execução, com validade limitada ao job. Não existe senha nem token pessoal armazenado.
- **Permissões mínimas.** O padrão do workflow é `contents: read`. Apenas o job de Docker recebe `packages: write`, necessário para publicar no GHCR.
- **Não publica em Pull Request**, com duas camadas de proteção: o login é condicionado a `github.event_name == 'push'` e o parâmetro `push` do build também.
- **Imagem quebrada não é publicada.** Se o lint ou os testes falharem, o job de Docker não executa, e a imagem `latest` anterior permanece intacta.

## Uso de IA no desenvolvimento

Utilizei o **Claude (Anthropic)** como assistente ao longo do desafio. Usos principais:

- anaisar o enunciado;
- gerar a primeira versão do `monitor.py`, dos testes e do workflow;
- explicar o código função por função e esclarecer conceitos;
- revisar erros que apareceram durante os testes e indicar a causa de cada um.

O que fiz por conta própria:

- corrigi os problemas encontrados.
- executei e testei tudo localmente (código, build da imagem, container, testes, lint) e na pipeline;
- estudei o código e escrevi minha própria explicação de cada função, apontando dúvidas até entender cada trecho;

O código gerado com apoio de IA não foi usado sem entendimento: todas as partes foram testadas e questionadas até que eu soubesse explicar o porquê de cada escolha.

## Limitações e melhorias futuras

- Alterar URLs exige recriar o container..
- O arquivo de log cresce sem limite..
- Checagens sequenciais, Com muitas URLs, uma rodada pode demorar mais que o intervalo.
- Versões das dependências são uma faixa.
