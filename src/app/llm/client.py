import os, re, json
import httpx
from typing import List, Dict, Any

def _sanitize_base_url(raw: str) -> str:
    raw = (raw or "").strip()
    raw = re.sub(r"\s+", "", raw)
    if not raw:
        raise RuntimeError("缺少 LLM_BASE_URL（例如 http://10.110.3.61:9997/v1）")
    if not raw.startswith(("http://","https://")):
        raw = "http://" + raw
    return raw[:-1] if raw.endswith("/") else raw

# 单例 AsyncClient：明确 proxies=None，且 trust_env=False（不继承系统代理）
_http_client: httpx.AsyncClient | None = None
def _client(timeout: int) -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            proxies=None,
            timeout=timeout,
            trust_env=False,      # 关键：彻底不读系统代理
        )
    else:
        # 更新超时时间（可选）
        _http_client.timeout = timeout
    return _http_client


def _cfg():
    base_url = _sanitize_base_url(os.getenv("LLM_BASE_URL", "http://10.110.3.61:9997/v1"))
    api_key  = os.getenv("LLM_API_KEY", "sk-local")
    model    = os.getenv("LLM_MODEL", "qwen3")
    timeout  = int(os.getenv("LLM_TIMEOUT", "45"))

    # 调试：打印每个字符和 Unicode 码位，抓全角冒号/零宽字符等
    if os.getenv("LLM_DEBUG") == "1":
        chars = " ".join([f"{repr(ch)}(U+{ord(ch):04X})" for ch in base_url])
        print(f"[LLM DEBUG] base_url={repr(base_url)} chars={chars} model={model} timeout={timeout}")

    return base_url, api_key, model, timeout

def _strip_code_fences(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = s.split("```", 2)[1] if "```" in s[3:] else s[3:]
    return s.strip()

async def chat_completion(messages, temperature: float = 0.2) -> str:
    base_url, api_key, model, timeout = _cfg()
    url = f"{base_url}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"model": model, "messages": messages, "temperature": temperature}

    if os.getenv("LLM_DEBUG") == "1":
        print(f"[LLM DEBUG] POST {url} (msgs={len(messages)}) trust_env=False proxies=None")

    r = await _client(timeout).post(url, headers=headers, json=payload)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]

async def chat_completion_json(messages: List[Dict[str, Any]], temperature: float = 0.2) -> Any:
    text = await chat_completion(messages, temperature)
    try:
        return json.loads(_strip_code_fences(text))
    except json.JSONDecodeError:
        # 再提醒只输出 JSON，重试一次
        messages2 = messages + [{"role":"system","content":"仅输出严格 JSON，不要解释文字。"}]
        text2 = await chat_completion(messages2, temperature)
        return json.loads(_strip_code_fences(text2))
