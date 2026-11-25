# YuQue MCP Server

一个基于 [Model Context Protocol](https://modelcontextprotocol.io) 的语雀（Yuque）笔记服务器，让支持 MCP 的 AI 客户端（Trae、Claude Desktop 等）能够直接读取和管理你的语雀知识库与文档。

- **语言/运行时**：Python 3.10+
- **传输方式**：stdio（本地进程，标准接入方式）
- **认证**：语雀个人访问 Token（环境变量 `YUQUE_TOKEN`）

## 提供的工具

| 工具 | 说明 |
| --- | --- |
| `get_user` | 获取当前账号信息，可用于验证 Token 是否有效 |
| `list_repos` | 列出个人或团队知识库，返回可用于后续操作的 `namespace` |
| `get_repo` | 获取单个知识库详情 |
| `list_docs` | 列出知识库下的文档概要（不含正文） |
| `get_doc` | 获取单篇文档正文（可选返回渲染后的 HTML） |
| `create_doc` | 新建文档 |
| `update_doc` | 更新文档（仅提交传入字段） |
| `delete_doc` | 删除文档（不可恢复） |
| `get_toc` | 获取知识库目录结构 |

> 语雀云文档的 `namespace` 形如 `login/book_slug`，团队知识库形如 `group_login/book_slug`。

## 安装

```bash
# 方式一：创建虚拟环境并安装依赖
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# 方式二：仅安装依赖后用 python -m 运行
pip install "mcp>=1.2.0" "httpx>=0.27"
```

## 配置 Token

在 [语雀 → 账户设置 → Token](https://www.yuque.com/settings/tokens) 新建个人访问 Token，然后通过环境变量提供：

```bash
export YUQUE_TOKEN="你的_token"
```

也可以复制 `.env.example` 为 `.env` 参考填写（本服务直接读取环境变量 `YUQUE_TOKEN`）。

## 在 MCP 客户端中接入

### 使用已安装的虚拟环境

```json
{
  "mcpServers": {
    "yuque": {
      "command": "/绝对路径/到/YuQue/.venv/bin/python",
      "args": ["-m", "yuque_mcp"],
      "env": { "YUQUE_TOKEN": "你的_token" }
    }
  }
}
```

如果已执行 `pip install -e .`，也可以直接用命令行入口：

```json
{
  "mcpServers": {
    "yuque": {
      "command": "yuque-mcp",
      "env": { "YUQUE_TOKEN": "你的_token" }
    }
  }
}
```

### 使用 uv（推荐，无需手动建环境）

```json
{
  "mcpServers": {
    "yuque": {
      "command": "uv",
      "args": [
        "run", "--with", "mcp", "--with", "httpx",
        "python", "-m", "yuque_mcp"
      ],
      "cwd": "/绝对路径/到/YuQue",
      "env": { "YUQUE_TOKEN": "你的_token" }
    }
  }
}
```

## 使用示例

接入后可以直接用自然语言让 AI 操作，例如：

- “列出我的语雀知识库”
- “看一下 `myname/notes` 知识库的目录结构”
- “把 `myname/notes` 里 slug 为 `hello-world` 的文档读出来”
- “在 `myname/notes` 新建一篇标题为‘周报’、内容是……的文档”
- “更新刚才那篇文档，把正文改成……”

## 说明

- 请求语雀 API 需要 30 秒超时与自定义 User-Agent，均已内置。
- 语雀官方 OpenAPI **未提供全局搜索接口**，因此本服务不含 `search` 工具；可通过 `list_docs` + `get_doc` 组合检索。
- 语雀对 API 有频率限制，请避免高频批量调用。
- `create_doc` / `update_doc` 默认按 `markdown` 格式写入；若知识库使用 Lake 格式，可传 `doc_format="lake"`。
- Token 拥有账号读写权限，请勿提交到仓库（`.gitignore` 已忽略 `.env`）。

## 项目结构

```
yuque_mcp/
├── __init__.py     # 版本信息
├── __main__.py     # python -m yuque_mcp 入口
├── client.py       # 语雀 API v2 客户端封装
└── server.py       # MCP Server 与工具定义
```
