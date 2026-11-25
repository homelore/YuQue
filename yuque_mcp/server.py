"""语雀 MCP Server 入口。

通过 stdio 暴露一组工具，用于读取和管理语雀知识库与文档。
需要在环境变量 ``YUQUE_TOKEN`` 中提供语雀个人访问 Token。
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from . import client

mcp = FastMCP("yuque-notes")


def _dump(data: Any) -> str:
    """把结果序列化为便于阅读的 JSON 字符串。"""
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_user() -> str:
    """获取当前语雀账号的用户信息（id、login、name 等）。

    可用于验证 YUQUE_TOKEN 是否有效。
    """
    return _dump(await client.get_user())


@mcp.tool()
async def list_repos(
    login: str | None = None,
    scope: str = "user",
    offset: int = 0,
    limit: int = 20,
) -> str:
    """列出知识库（repo），返回的 namespace 可用于后续文档操作。

    Args:
        login: 用户名或团队 login。scope=user 时留空则使用当前登录用户。
        scope: "user" 列出个人知识库，"group" 列出团队知识库。
        offset: 分页偏移，默认 0。
        limit: 每页数量，默认 20。
    """
    return _dump(await client.list_repos(login, scope, offset, limit))


@mcp.tool()
async def get_repo(namespace: str) -> str:
    """获取单个知识库详情。

    Args:
        namespace: 知识库命名空间，形如 "login/book_slug"。
    """
    return _dump(await client.get_repo(namespace))


@mcp.tool()
async def list_docs(namespace: str, offset: int = 0, limit: int = 20) -> str:
    """列出知识库下的文档概要（不含正文）。

    Args:
        namespace: 知识库命名空间，形如 "login/book_slug"。
        offset: 分页偏移，默认 0。
        limit: 每页数量，默认 20。
    """
    return _dump(await client.list_docs(namespace, offset, limit))


@mcp.tool()
async def get_doc(namespace: str, slug: str, include_html: bool = False) -> str:
    """获取单篇文档的正文内容。

    Args:
        namespace: 知识库命名空间，形如 "login/book_slug"。
        slug: 文档的 slug 或 id。
        include_html: 是否同时返回渲染后的 HTML（lake 格式文档可读性更好）。
    """
    return _dump(await client.get_doc(namespace, slug, include_html))


@mcp.tool()
async def create_doc(
    namespace: str,
    title: str,
    body: str,
    slug: str | None = None,
    public: bool = False,
    doc_format: str = "markdown",
) -> str:
    """在知识库中新建文档。

    Args:
        namespace: 知识库命名空间，形如 "login/book_slug"。
        title: 文档标题。
        body: 文档正文内容。
        slug: 自定义文档路径 slug（可选，需唯一）。
        public: 是否公开，默认 False。
        doc_format: 正文格式，"markdown" 或 "lake"，默认 "markdown"。
    """
    return _dump(
        await client.create_doc(namespace, title, body, slug, public, doc_format)
    )


@mcp.tool()
async def update_doc(
    namespace: str,
    id_or_slug: str,
    title: str | None = None,
    body: str | None = None,
    slug: str | None = None,
    public: bool | None = None,
    doc_format: str = "markdown",
) -> str:
    """更新文档，仅提交传入的字段。

    Args:
        namespace: 知识库命名空间，形如 "login/book_slug"。
        id_or_slug: 待更新文档的 id 或 slug。
        title: 新标题（可选）。
        body: 新正文（可选）。
        slug: 新路径 slug（可选）。
        public: 是否公开（可选）。
        doc_format: 正文格式，"markdown" 或 "lake"，默认 "markdown"。
    """
    return _dump(
        await client.update_doc(
            namespace, id_or_slug, title, body, slug, public, doc_format
        )
    )


@mcp.tool()
async def delete_doc(namespace: str, id_or_slug: str) -> str:
    """删除文档（不可恢复，请谨慎使用）。

    Args:
        namespace: 知识库命名空间，形如 "login/book_slug"。
        id_or_slug: 待删除文档的 id 或 slug。
    """
    return _dump(await client.delete_doc(namespace, id_or_slug))


@mcp.tool()
async def get_toc(namespace: str) -> str:
    """获取知识库的目录结构。

    Args:
        namespace: 知识库命名空间，形如 "login/book_slug"。
    """
    return _dump(await client.get_toc(namespace))


def main() -> None:
    """以 stdio 方式启动 MCP Server。"""
    mcp.run()


if __name__ == "__main__":
    main()
