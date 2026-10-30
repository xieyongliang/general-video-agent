# 手搓视频 MA

从“暮山保温杯电商广告”实验整理的最小客户端。使用火山中国站通用 Managed Agent (`ark_agent_preview`)、Evolving 规划模型及绑定的 Seedance / Seedream 工具。

这不是自研 Agent runtime：底层执行框架、沙箱、工具适配由火山 Managed Agents 提供。本项目包含配置模板、原实验 system/task prompt、创建和提交客户端、状态与事件/文件列表采集。新整理客户端没有再次在线生成，原实验实际完成过生成；本仓库不包含历史会话、账单或视频。

## 前提

- Python 3.10+，仅标准库。
- 火山账号已开通 Managed Agents，具有 `ark_agent_preview`、Evolving 及所需生成模型权限。
- 自己账号内可用的 Seedance 2.5 与 Seedream 5.0 Pro 接入点；模板保留原实验模型名称与版本，若不可用请明确修改，不能静默换模型后称为复现。
- 已创建的云环境 ID；已上传至方舟的 `references.zip` 文件 ID。ZIP 包含 `product.jpg`，以及任务所需的人物参考素材。素材须自行准备，本仓库不上传原实验图片。

## 使用

在 shell 中设置环境变量（`.env.example` 仅模板，程序不会自动加载）：

```bash
read -s -p 'ARK API key: ' ARK_API_KEY
export ARK_API_KEY
export ARK_API_BASE=https://ark.cn-beijing.volces.com/api/v3
export SEEDANCE_ENDPOINT_ID=你的接入点ID
export SEEDREAM_ENDPOINT_ID=你的接入点ID
python3 ma.py create-agent
python3 ma.py create-session --agent-id 你的AgentID --version 1 --environment-id 你的环境ID --reference-file-id 你的文件ID
python3 ma.py submit --session-id 你的SessionID
python3 ma.py status --session-id 你的SessionID
python3 ma.py events --session-id 你的SessionID
python3 ma.py files --session-id 你的SessionID
```

`submit` 会实际启动模型和视频生成并产生费用。工具中的 `always_allow` 表示 Agent 可自主调用已启用工具；应在隔离云环境执行，不放入无关凭据。

结果保存在被 Git 忽略的 `state/`。`files.json` 可包含临时下载链接，不能提交或公开。可在控制台检查会话并下载 `final.mp4`、storyboard、manifest、qa 等交付文件。

一次目录对应一次运行。写操作先保存 intent，再发送请求；已有 intent/result 时拒绝重复提交。出现超时应在控制台按创建时间和名称对账，不能直接删除 intent 后重试。不会自动恢复后台任务，也不会把 `idle` 或 Agent 自报完成当作视频质量验收。

## 原实验约束

30 秒（允许 28–32 秒）电商广告，16:9、720p、最终 24fps；最多 6 次视频调用、累计请求 45 秒、4 次图片调用。失败计入预算；原生 Seedance 音频，禁用额外 TTS。system prompt 与 task prompt 的补充硬约束优先于前文通用的工具描述。

预算目前由提示词约束，客户端没有实现服务端硬限额，必须检查实际工具事件。成片需独立检查产品一致性、字幕、冷热卖点、声音与品牌尾卡；任务执行成功不等于质量通过。

## 分享范围

仅提交源代码、模板及提示词。没有 API Key、历史 Agent/Session/环境/文件 ID、私有链接、参考素材及实验产物。模型白名单及 Evolving 浮动版本会影响可复现性。
