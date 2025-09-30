import logging, sys, uuid, time
from typing import Callable
from fastapi import Request

def setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        stream=sys.stdout,
    )

def gen_request_id() -> str:
    return uuid.uuid4().hex[:12]

async def request_id_middleware(request: Request, call_next: Callable):
    req_id = request.headers.get("X-Request-ID") or gen_request_id()
    request.state.request_id = req_id
    start = time.perf_counter()
    response = await call_next(request)
    cost = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = req_id
    response.headers["X-Response-Time-ms"] = f"{cost:.1f}"
    return response
