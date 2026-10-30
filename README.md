# 通用视频 Agent

从“暮山保温杯电商广告”实验整理的最小客户端。使用火山中国站通用 Managed Agent (`ark_agent_preview`)、Evolving 规划模型及绑定的 Seedance / Seedream 工具。

这不是自研 Agent runtime：底层执行框架、沙箱、工具适配由火山 Managed Agents 提供。本项目包含配置模板、原实验 system/task prompt、创建和提交客户端、状态与事件/文件列表采集。新整理客户端没有再次在线生成，原实验实际完成过生成；本仓库不包含历史会话、账单或视频。

## Skill 与工具

本项目主要使用火山 Managed Agents 内置工具和我们配置的制作提示词，没有额外编写或打包专用的视频创作 Skill。底层框架是否自动加载平台内部 Skill，现有记录不足以完整确认。

| 类别 | 配置与用途 |
| --- | --- |
| Agent 框架 | 火山通用 Managed Agent：`ark_agent_preview`，提供执行框架、云端沙箱和工具适配 |
| 理解与编排模型 | `doubao-seed-evolving-latest-version`，负责理解需求、规划镜头、编排工具及检查结果 |
| 视频生成 | `video_generate`，绑定 Seedance 2.5；实验事件中的调用名称为 `GenVideo` |
| 图片生成 | `image_generate`，绑定 Seedream 5.0 Pro；实验事件中的调用名称为 `GenImage`，可用于建立参考图和关键帧 |
| 文件与代码 | `bash`、`read`、`write`、`edit`、`glob`、`grep`，用于执行代码、管理素材和检查文件 |
| 后期制作 | Agent 在云端通过脚本、FFmpeg 等完成剪辑、字幕、混音和导出；FFmpeg 是命令行程序，不是本项目自定义的 Skill |
| 其他启用工具 | `compose_video`、`visual_search`、`general_search`、`todo_write`、`web_fetch`；`web_search` 在本轮配置中关闭 |

启用工具不代表每次都实际调用。原实验的任务提示禁止使用外部检索素材，实际执行情况应以会话事件为准。通用 MA 三次测试均调用了视频生成工具，未调用图片生成工具；图片生成保留为可用能力。

仓库中的 Python 客户端负责创建 Agent、创建会话、提交任务和采集状态、事件及文件列表；真正的视频制作由云端 Agent 调用工具完成。我们提供的是 system/task prompt、模型与工具绑定、预算约束和客户端流程。

本轮禁止额外 TTS，旁白或对白要求来自 Seedance 原生音轨；允许通过 FFmpeg 剪辑、混音和添加字幕。Evolving 使用浮动版本别名，模型白名单和平台内部框架变化可能影响复现结果。

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
