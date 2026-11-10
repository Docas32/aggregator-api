# Logger estruturado em JSON
import json
import logging
from datetime import datetime, timezone

class JsonFormatter(logging.Formatter):
    def format(self, record):
        base = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        base.update(getattr(record, "extra_fields", {})) # contexto por requisicao
        return json.dumps(base, ensure_ascii=False)


def get_logger(trace_id, route):
    logger = logging.getLogger("aggregator")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    extra = {"extra_fields": {"trace_id": trace_id, "route": route}}
    return logger, extra

# {"ts":"2026-02-10T14:03:22.114+00:00","level":"INFO","logger":"aggregator",
# "msg":"lote recebido","trace_id":"7f3a...","route":"/batch"}