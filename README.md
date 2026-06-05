# Claude 飞书对话归档工具

这是一个用于归档 Claude Code 对话的小工具项目。它可以把 Claude Code 的对话历史保存成本地 Markdown 文件，并通过 `lark-cli` 上传为飞书在线文档。

## 项目功能

- 手动归档当前 Claude Code 对话为 Markdown。
- 自动读取 Claude Code transcript 并生成 Markdown 归档。
- 将本地 Markdown 文件导入为飞书 Docx 文档。
- 支持上传到飞书云空间根目录或指定文件夹。
- 提供 Claude Code slash command 示例。
- 提供 Claude Code Stop Hook 自动归档示例。
- 内置基础敏感信息脱敏，避免归档常见 token、密钥和 cookie。

## 适用场景

- 想把重要的 Claude Code 编程会话沉淀成文档。
- 想把需求讨论、排查过程、代码修改记录同步到飞书。
- 想给团队留存 AI 协作过程。
- 想在每次 Claude Code 会话结束后自动生成归档。

## 项目结构

```text
claude-feishu-archiver/
  .claude/
    commands/
      archive-feishu.md          # Claude Code 手动归档命令
    settings.example.json        # Claude Code Stop Hook 示例
  archives/
    .gitkeep                     # 本地归档目录占位
  scripts/
    archive_claude_session.py    # 从 Claude transcript 生成 Markdown 并上传飞书
    upload_archive_to_feishu.py  # 上传本地 Markdown 到飞书文档
  .gitignore
  README.md
```

## 环境要求

- Python 3.10 或更高版本
- Claude Code
- `lark-cli`
- 一个已配置权限的飞书 / Lark 应用

## 安装 lark-cli

如果本机还没有配置 `lark-cli`，先执行：

```bash
lark-cli config init --new
```

如果需要用用户身份上传到自己的飞书云空间，还需要完成用户授权。具体权限不足时，按 `lark-cli` 返回的提示补充授权即可。

本项目上传 Markdown 到飞书文档时使用的是：

```bash
lark-cli drive +import --file ./archives/example.md --type docx
```

## 快速开始

进入项目目录：

```bash
cd claude-feishu-archiver
```

准备一个 Markdown 文件，例如：

```bash
mkdir archives
echo "# 测试归档" > archives/example.md
```

上传到飞书：

```bash
python scripts/upload_archive_to_feishu.py archives/example.md
```

上传到指定飞书文件夹：

```bash
python scripts/upload_archive_to_feishu.py archives/example.md --folder-token <FOLDER_TOKEN>
```

指定文档标题：

```bash
python scripts/upload_archive_to_feishu.py archives/example.md --name "Claude 会话归档"
```

指定身份：

```bash
python scripts/upload_archive_to_feishu.py archives/example.md --as user
```

或：

```bash
python scripts/upload_archive_to_feishu.py archives/example.md --as bot
```

## 快速适配本地 Claude Code

有两种适配方式：手动归档和自动归档。

推荐先使用手动归档，确认飞书上传链路正常后，再开启自动归档。

## 方式一：手动归档当前对话

把命令文件复制到你的目标项目中：

```text
.claude/commands/archive-feishu.md
```

如果你的目标项目还没有 `.claude/commands/` 目录，就新建这个目录。

复制后，在 Claude Code 对话中输入：

```text
/archive-feishu
```

Claude Code 会按照命令文件中的说明执行：

- 整理当前对话内容
- 生成本地 Markdown 文件
- 保存到 `archives/`
- 调用上传脚本导入飞书
- 返回本地路径和飞书文档 URL

注意：手动归档方式依赖 Claude Code 当前对话上下文，因此更适合“我认为这次对话值得保存”的场景。

## 方式二：Stop Hook 自动归档

如果你想在 Claude Code 每次会话结束时自动归档，可以使用 Stop Hook。

示例配置在：

```text
.claude/settings.example.json
```

内容如下：

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python scripts/archive_claude_session.py"
          }
        ]
      }
    ]
  }
}
```

你可以把这段配置合并到自己的 Claude Code settings 中。

启用后，Claude Code 在 Stop 事件触发时会把包含 `transcript_path` 的 JSON payload 传给脚本。脚本会读取 transcript，生成 Markdown，并上传飞书。

## Hook 脚本手动测试

如果你已经知道 Claude Code transcript 文件路径，可以手动测试：

```bash
python scripts/archive_claude_session.py --transcript-path <TRANSCRIPT_JSONL_PATH> --no-upload
```

这只会生成本地 Markdown，不会上传飞书。

确认本地文件没问题后，再执行上传：

```bash
python scripts/archive_claude_session.py --transcript-path <TRANSCRIPT_JSONL_PATH>
```

上传到指定飞书文件夹：

```bash
python scripts/archive_claude_session.py --transcript-path <TRANSCRIPT_JSONL_PATH> --folder-token <FOLDER_TOKEN>
```

## 飞书文件夹 Token 怎么获取

飞书文件夹 URL 通常类似：

```text
https://xxx.feishu.cn/drive/folder/<FOLDER_TOKEN>
```

其中 `/drive/folder/` 后面的部分就是 folder token。

如果不传 `--folder-token`，文档会导入到当前身份的飞书云空间根目录。

## 敏感信息处理

脚本会对常见敏感信息做基础脱敏：

- `api_key`
- `access_token`
- `refresh_token`
- `password`
- `secret`
- `Authorization: Bearer ...`
- `Cookie: ...`
- 私钥块

但自动脱敏不能保证覆盖所有场景。重要会话上传前，建议先检查 `archives/` 下生成的 Markdown 文件。

## 常见问题

### 1. 上传失败，提示权限不足

先确认 `lark-cli` 已初始化：

```bash
lark-cli config init --new
```

如果使用用户身份，按错误提示补充授权。

如果使用 bot 身份，确认飞书应用后台已经开通 Drive import 相关权限。

### 2. Hook 没有生成文件

检查 Claude Code settings 是否正确加载了 Stop Hook。

也可以手动执行：

```bash
python scripts/archive_claude_session.py --transcript-path <TRANSCRIPT_JSONL_PATH> --no-upload
```

如果手动执行成功，说明脚本正常，问题通常在 Claude Code Hook 配置。

### 3. 上传成功但没看到飞书 URL

`lark-cli drive +import` 有时会返回异步任务结果。如果命令输出里包含 `ticket` 或 `next_command`，按输出提示继续查询任务结果。

### 4. 我只想保存本地 Markdown，不想上传飞书

使用：

```bash
python scripts/archive_claude_session.py --transcript-path <TRANSCRIPT_JSONL_PATH> --no-upload
```

## 上传到 GitHub

如果你想把这个小项目单独上传到 GitHub，可以在项目目录中执行：

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

如果它是在另一个已有仓库的子目录中，也可以直接把 `claude-feishu-archiver/` 作为子项目目录提交。
