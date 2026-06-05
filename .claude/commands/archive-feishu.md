# 归档当前 Claude Code 对话到飞书

请将当前 Claude Code 对话整理成本地 Markdown 文件，并上传到飞书文档。

执行步骤：

1. 如果 `archives/` 目录不存在，先创建该目录。
2. 创建 Markdown 文件：`archives/claude-session-YYYYMMDD-HHMMSS.md`。
3. Markdown 文档使用中文编写。
4. 文档至少包含以下章节：
   - 标题
   - 归档时间
   - 用户目标
   - 关键讨论
   - 已确定结论
   - 代码或文件变更
   - 后续待办
5. 不要写入密钥、token、cookie、私钥、密码或个人敏感信息。
6. 保存 Markdown 后执行：

```bash
python scripts/upload_archive_to_feishu.py <生成的-md-文件路径>
```

7. 最后返回本地 Markdown 路径和飞书文档 URL。

如果上传命令返回异步任务 ticket 或 next_command，请继续执行查询命令，直到拿到最终结果或明确失败原因。
