import os, re
import httpx
from openai import AsyncOpenAI           # 官方 SDK
from langchain_openai import ChatOpenAI  # LangChain 封装

def _sanitize_base_url(raw: str) -> str:
    raw = (raw or "").strip()
    raw = re.sub(r"\s+", "", raw)
    if not raw:
        raise RuntimeError("缺少 LLM_BASE_URL（例：http://10.110.3.61:9997/v1）")
    if not raw.startswith(("http://", "https://")):
        raw = "http://" + raw
    return raw[:-1] if raw.endswith("/") else raw

def get_llm() -> ChatOpenAI:
    # 环境
    base_url = _sanitize_base_url(os.getenv("LLM_BASE_URL", ""))
    api_key  = os.getenv("LLM_API_KEY", "sk-local")
    model    = os.getenv("LLM_MODEL", "qwen3")
    timeout  = int(os.getenv("LLM_TIMEOUT", "45"))

    # 让 10.* 内网直连（可叠加已有 NO_PROXY）
    no_proxy = os.environ.get("NO_PROXY", "")
    parts = {p.strip() for p in no_proxy.split(",") if p.strip()}
    parts.update({"10.110.3.61", "localhost", "127.0.0.1"})
    os.environ["NO_PROXY"] = ",".join(sorted(parts))

    # 构造“不开代理”的 HTTP 客户端（与 test 脚本一致）
    http_client = httpx.AsyncClient(proxies=None, timeout=timeout)

    # 1) 官方 SDK 客户端（关键：base_url + http_client）
    oai_client = AsyncOpenAI(
        base_url=base_url,             # 例如 http://10.110.3.61:9997/v1
        api_key=api_key,               # 任意非空字符串（Xinference 常兼容 Bearer）
        http_client=http_client,       # 禁用代理
    )

    # 2) 交给 LangChain（保留 LangChain 写法与链路）
    return ChatOpenAI(
        model=model,
        client=oai_client,             # 传自定义 OpenAI 客户端
        temperature=0.4,
        max_retries=1,
        timeout=timeout,
    )
