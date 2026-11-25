"""语雀 API v2 客户端封装。

所有函数都会把语雀返回的 ``{"data": ...}`` 自动解包，并尽量只保留
后续操作真正需要的字段，避免把超大的原始响应塞进模型上下文。
"""

from __future__ import annotations

import os
from typing import Any

import httpx

BASE_URL = "https://www.yuque.com/api/v2"
USER_AGENT = "yuque-mcp/0.1.0 (+https://github.com/homelore/YuQue)"


class YuqueError(Exception):
    """语雀 API 调用异常。"""


_http_client: httpx.AsyncClient | None = None


def _get_token() -> str:
    token = os.environ.get("YUQUE_TOKEN", "").strip()
    if not token:
        raise YuqueError(
            "未设置环境变量 YUQUE_TOKEN。请到 语雀 → 账户设置 → Token 页面生成"
            "个人访问 Token，并在启动 MCP Server 时通过环境变量提供。"
        )
    return token


def _get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={
                "X-Auth-Token": _get_token(),
                "User-Agent": USER_AGENT,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=httpx.Timeout(30.0),
        )
    return _http_client


async def _request(method: str, path: str, **kwargs: Any) -> Any:
    """发起一次请求并返回已解析的 JSON（自动解包 ``data`` 字段）。"""
    http = _get_http_client()
    try:
        resp = await http.request(method, path, **kwargs)
    except httpx.HTTPError as exc:
        raise YuqueError(f"请求语雀 API 失败：{exc}") from exc

    if resp.status_code >= 400:
        raise YuqueError(f"语雀 API 返回错误 {resp.status_code}：{resp.text}")

    if not resp.content:
        return None

    try:
        payload = resp.json()
    except ValueError:
        return resp.text

    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    return payload


# --------------------------------------------------------------------------- #
# 字段裁剪
# --------------------------------------------------------------------------- #
def _summarize_user(user: dict[str, Any]) -> dict[str, Any]:
    keys = ("id", "login", "name", "description", "avatar_url")
    return {key: user.get(key) for key in keys}


def _summarize_repo(repo: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "id",
        "name",
        "slug",
        "namespace",
        "description",
        "items_count",
        "public",
        "updated_at",
    )
    return {key: repo.get(key) for key in keys}


def _summarize_doc(doc: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "id",
        "slug",
        "title",
        "format",
        "word_count",
        "created_at",
        "updated_at",
    )
    return {key: doc.get(key) for key in keys}


# --------------------------------------------------------------------------- #
# 用户
# --------------------------------------------------------------------------- #
async def get_user() -> dict[str, Any]:
    """获取当前 Token 对应的用户信息。"""
    data = await _request("GET", "/user")
    return _summarize_user(data or {})


# --------------------------------------------------------------------------- #
# 知识库 (repo)
# --------------------------------------------------------------------------- #
async def list_repos(
    login: str | None = None,
    scope: str = "user",
    offset: int = 0,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """列出知识库。

    Args:
        login: 用户名或团队 login。scope=user 且不传时默认使用当前用户。
        scope: ``user`` 列出个人知识库，``group`` 列出团队知识库。
    """
    if scope not in ("user", "group"):
        raise YuqueError("scope 只能是 'user'（个人）或 'group'（团队）")

    if not login:
        if scope == "group":
            raise YuqueError("列出团队知识库时必须传入 login（团队 login）")
        current = await get_user()
        login = current.get("login")
        if not login:
            raise YuqueError("无法获取当前用户 login，请显式传入 login 参数")

    prefix = "users" if scope == "user" else "groups"
    data = await _request(
        "GET",
        f"/{prefix}/{login}/repos",
        params={"offset": offset, "limit": limit},
    )
    return [_summarize_repo(repo) for repo in (data or [])]


async def get_repo(namespace: str) -> dict[str, Any]:
    """获取单个知识库详情。``namespace`` 形如 ``login/book_slug``。"""
    data = await _request("GET", f"/repos/{namespace}")
    return _summarize_repo(data or {})


# --------------------------------------------------------------------------- #
# 文档 (doc)
# --------------------------------------------------------------------------- #
async def list_docs(
    namespace: str,
    offset: int = 0,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """列出知识库下的文档。"""
    data = await _request(
        "GET",
        f"/repos/{namespace}/docs",
        params={"offset": offset, "limit": limit},
    )
    return [_summarize_doc(doc) for doc in (data or [])]


async def get_doc(
    namespace: str,
    slug: str,
    include_html: bool = False,
) -> dict[str, Any]:
    """获取单篇文档内容。

    默认返回语雀原始正文 ``body``（markdown 或 lake 格式）。当文档是 lake
    格式时，可传 ``include_html=True`` 额外拿到渲染后的 HTML。
    """
    data = await _request("GET", f"/repos/{namespace}/docs/{slug}")
    data = data or {}
    result = _summarize_doc(data)
    result["body"] = data.get("body")
    if include_html:
        result["body_html"] = data.get("body_html")
    return result


async def create_doc(
    namespace: str,
    title: str,
    body: str,
    slug: str | None = None,
    public: bool = False,
    doc_format: str = "markdown",
) -> dict[str, Any]:
    """在知识库中新建文档。"""
    payload: dict[str, Any] = {
        "title": title,
        "body": body,
        "format": doc_format,
        "public": public,
    }
    if slug:
        payload["slug"] = slug
    data = await _request("POST", f"/repos/{namespace}/docs", json=payload)
    return _summarize_doc(data or {})


async def update_doc(
    namespace: str,
    id_or_slug: str,
    title: str | None = None,
    body: str | None = None,
    slug: str | None = None,
    public: bool | None = None,
    doc_format: str = "markdown",
) -> dict[str, Any]:
    """更新文档，只提交传入的字段。"""
    payload: dict[str, Any] = {}
    if title is not None:
        payload["title"] = title
    if slug is not None:
        payload["slug"] = slug
    if public is not None:
        payload["public"] = public
    if body is not None:
        payload["body"] = body
        payload["format"] = doc_format

    if not payload:
        raise YuqueError("没有需要更新的字段，请至少提供 title / body / slug / public 之一")

    data = await _request(
        "PUT", f"/repos/{namespace}/docs/{id_or_slug}", json=payload
    )
    return _summarize_doc(data or {})


async def delete_doc(namespace: str, id_or_slug: str) -> dict[str, Any]:
    """删除文档。"""
    data = await _request("DELETE", f"/repos/{namespace}/docs/{id_or_slug}")
    return {"deleted": True, "id_or_slug": id_or_slug, "result": data}


# --------------------------------------------------------------------------- #
# 目录 (toc)
# --------------------------------------------------------------------------- #
async def get_toc(namespace: str) -> list[dict[str, Any]]:
    """获取知识库目录结构。"""
    data = await _request("GET", f"/repos/{namespace}/toc")
    return data or []
