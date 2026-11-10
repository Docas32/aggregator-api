# aggregator-api

API Flask de exemplo para receber lotes de telemetria e acompanhar métricas com
Prometheus e Grafana.

> **Estado atual:** a API aceita o lote e atualiza métricas, mas não salva os
> dados nem executa consolidação. O valor de `pending_batches` apenas aumenta
> conforme os itens recebidos.

## Requisitos

- Docker com Docker Compose (recomendado); ou
- Python 3.14+ para executar localmente.

## Executar com Docker Compose

Na raiz do projeto:

```bash
docker compose up -d --build
```

Isso inicia os seguintes serviços:

| Serviço | Endereço |
| --- | --- |
| API Flask | <http://localhost:8000> |
| Métricas da API | <http://localhost:8000/metrics> |
| Prometheus | <http://localhost:9090> |
| Grafana | <http://localhost:3000> |

Para verificar se os contêineres estão ativos:

```bash
docker compose ps
```

Para encerrar os serviços:

```bash
docker compose down
```

O Grafana está configurado com o usuário `admin` e a senha inicial `admin`.
Essa credencial é apenas para desenvolvimento local; altere-a antes de usar
este ambiente em qualquer contexto compartilhado ou de produção.

### Conectar Grafana ao Prometheus

1. No Grafana, acesse **Connections → Data sources → Add data source** e
   selecione **Prometheus**.
2. Em **Prometheus server URL**, informe `http://prometheus:9090`. Esse é o
   endereço do serviço na rede interna do Docker Compose.
3. Clique em **Save & test**.
4. Crie um dashboard, adicione uma visualização e consulte, por exemplo,
   `http_requests_total`.

O Prometheus coleta a API a cada 15 segundos, conforme `prometheus.yml`.

## Enviar um lote

Envie uma requisição `POST` com JSON para `/batch`:

```bash
curl -X POST http://localhost:8000/batch \
  -H "Content-Type: application/json" \
  -d '{"lotes":[{"id":1,"valor":100},{"id":2,"valor":200}]}'
```

Resposta esperada:

```json
{"lotes":2,"status":"aceito"}
```

Opcionalmente, envie um identificador de rastreamento no cabeçalho
`X-Trace-Id`. Se ele não for fornecido, a API gera um UUID:

```bash
curl -X POST http://localhost:8000/batch \
  -H "Content-Type: application/json" \
  -H "X-Trace-Id: exemplo-123" \
  -d '{"lotes":[{"id":1}]}'
```

## Executar localmente sem Docker

Com Python 3.14 ou superior:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app run --port 8000
```

Nesse modo, a API fica disponível em <http://localhost:8000>. Prometheus e
Grafana não são iniciados por esse comando; use Docker Compose para executar a
stack completa de monitoramento.

## Endpoints da API

| Método | Caminho | Descrição |
| --- | --- | --- |
| `GET` | `/` | Retorna o nome do serviço e os endpoints disponíveis. |
| `POST` | `/batch` | Recebe JSON com a propriedade `lotes` e atualiza as métricas. |
| `GET` | `/metrics` | Expõe métricas no formato do Prometheus. |

## Métricas

- `http_requests_total{route,method,status}`: conta as requisições tratadas
  pelo endpoint `/batch`, separadas por rota, método e status.
- `http_request_duration_seconds{route}`: histograma da duração das
  requisições ao endpoint `/batch`.
- `pending_batches`: soma o número de itens recebidos em `lotes`. Não diminui,
  pois ainda não há processamento ou consolidação implementados.
- Métricas padrão da biblioteca Prometheus para Python, incluindo
  `process_resident_memory_bytes`, também são expostas.

Exemplos de consultas PromQL:

```promql
http_requests_total
```

```promql
sum by (route) (rate(http_requests_total[5m]))
```

```promql
histogram_quantile(
  0.95,
  sum by (le, route) (rate(http_request_duration_seconds_bucket[5m]))
)
```

O Prometheus armazena as séries temporais coletadas. O Compose deste projeto
não configura um volume persistente para os dados do Prometheus; eles podem ser
perdidos quando o contêiner for removido ou recriado.

## SLI/SLO

O arquivo `sli-spec.yaml` registra objetivos propostos para disponibilidade,
latência, vazão e saturação de memória. Ele é uma especificação; a aplicação
não o carrega nem calcula automaticamente o cumprimento desses SLOs.

## Estrutura do projeto

| Arquivo | Finalidade |
| --- | --- |
| `app.py` | Rotas Flask e instrumentação das métricas. |
| `json_log.py` | Formatação de logs estruturados em JSON com contexto de rota e trace ID. |
| `prometheus.yml` | Configuração de coleta do Prometheus. |
| `docker-compose.yml` | Serviços da API, Prometheus e Grafana. |
| `Dockerfile` | Imagem de contêiner da API. |
| `requirements.txt` | Dependências Python da aplicação. |
| `sli-spec.yaml` | Especificação dos SLIs e SLOs. |
# aggregator-api
