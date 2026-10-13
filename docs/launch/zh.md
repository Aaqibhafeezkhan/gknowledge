# 中文社区发布文案

To post manually: V2EX needs a signed-in account (node 分享创造), Juejin needs a signed-in account (article editor). Copy the text as is.

## V2EX · 分享创造

**标题：** 把 Karpathy 的 LLM Wiki 做成了原生 GNOME 应用：导入文档，自动生成带出处的知识库，默认离线

**正文：**

大家好，分享一个我们做的开源项目 gknowledge（MIT 协议）。

今年 4 月 Karpathy 提出了 LLM Wiki 模式：不再每次提问都让模型重新读原始文档，而是让模型把资料整理成一个持续维护、相互链接的 wiki。社区里已经有很多实现，但基本都是 Electron 或 Tauri。我们想要一个真正的 Linux 桌面原生应用，于是做了 gknowledge：

- GTK 4 + Libadwaita，原生 GNOME 风格，没有浏览器内核
- 默认离线可用：内置离线引擎，不需要任何 API key
- 可以用自己的 ChatGPT Plus/Pro 套餐登录（OpenAI 新推出的 Sign in with ChatGPT），用量计入自己的套餐；也支持 Ollama 和任何 OpenAI 兼容接口
- 知识库就是普通的 Markdown 文件夹，带 `[[wikilinks]]` 和出处，可直接用 Obsidian 打开
- 不会生成一堆空页面，会自动合并重复条目
- 自带 MCP 服务器，Claude Code / Codex / Cursor 可以直接搜索、阅读、扩充同一个 wiki

Ubuntu / Debian 一行安装：

```
curl -fsSL https://github.com/openapi/gknowledge/releases/latest/download/install.sh | bash
```

GitHub：https://github.com/openapi/gknowledge （有中文 README）

项目还很早期（v0.2），欢迎试用、提 issue、提 PR，觉得有用的话点个 ⭐ 就是最大的支持。

## 掘金 · 文章

**标题：** 我们把 Karpathy 的 LLM Wiki 做成了原生 GNOME 应用（离线可用，支持 ChatGPT 套餐登录和 MCP）

**标签：** 开源、人工智能、Linux、Python

**正文：**

### 背景

2026 年 4 月，Andrej Karpathy 发布了一个叫 LLM Wiki 的“想法文件”：与其每次提问都让大模型重新检索、阅读原始文档（传统 RAG），不如让它把资料整理成一个持久的、不断积累的 wiki。一周之内 GitHub 上出现了上千个实现，其中 nashsu/llm_wiki 和 Tolaria 都超过了两万星。

但这些项目大多是 Tauri 或 Electron 应用。对于每天使用 GNOME / Ubuntu 的人来说，我们想要一个真正“原生”的版本。

### gknowledge 是什么

gknowledge 是一个 GTK 4 + Libadwaita 编写的桌面应用（Python）：

1. **导入资料**：Markdown、文本、PDF、HTML。
2. **自动构建 wiki**：每个来源生成摘要页，其中的人物、系统、概念生成独立页面，并用 `[[wikilinks]]` 互相链接，每个页面都记录出处。
3. **带引用问答**：答案来自 wiki，带编号引用，点击即可跳到对应页面。

整个知识库就是一个普通的 Markdown 文件夹，可以直接用 Obsidian 打开，也可以放进 git。

### 和其他实现的不同

- **原生界面**：没有 Electron、没有 Tauri，遵循 GNOME HIG。
- **无需模型也能用**：内置离线引擎；接入模型后效果更好。
- **用自己的 ChatGPT 套餐**：支持 OpenAI 的 Sign in with ChatGPT，用户登录自己的 Plus/Pro 账号，用量计入自己的套餐，不需要 API key，也没有人转卖 token。同时支持 Ollama、LM Studio 和任何 OpenAI 兼容接口。
- **不制造垃圾页面**：只在有实际内容时才创建页面，自动合并重复条目（例如 “Kasparov” 会链接到 “Garry Kasparov”）。在 6 篇 AI 论文的测试中，页面数从 114 降到 64，而且每页都有真实描述。
- **支持智能体**：自带 MCP 服务器，一行命令就能让 Claude Code 使用你的 wiki：

```
claude mcp add gknowledge -- gknowledge-mcp ~/Knowledge/my-project
```

### 安装

```
curl -fsSL https://github.com/openapi/gknowledge/releases/latest/download/install.sh | bash
```

### 接下来

Lint（发现矛盾、孤立页面）、知识图谱视图、并行导入、Flatpak / PPA / Snap。

项目地址：https://github.com/openapi/gknowledge （MIT，欢迎 PR）。如果你也希望 Linux 桌面上有这样的工具，欢迎点个 ⭐。
