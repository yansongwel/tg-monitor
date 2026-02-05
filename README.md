# Telegram Monitor

这是一个基于 Python Telethon 的 Telegram 个人账号监听工具，支持监听私聊、被@、被拉入群组，并通过钉钉或飞书发送告警。

## 功能

*   📩 监听个人私聊消息
*   🔔 监听群组中 @你 的消息
*   👥 监听被拉入新群组/加入新群组
*   🚀 支持 Docker 部署
*   ⚡ 基于 `uv` 进行依赖管理

## 支持的告警渠道

目前项目已内置了 **钉钉 (DingTalk)**、**飞书 (Feishu)** 和 **Server酱 (WeChat)** 的告警。

如果需要扩展更多告警渠道（如企业微信、Slack、Bark、Telegram Bot 等），可以参考以下思路自行修改 `main.py`：

### 1. Server酱 (已内置)
在 [Server酱官网](https://sct.ftqq.com/) 申请 SendKey，然后配置到 `.env` 文件的 `SERVERCHAN_KEY` 字段。

### 2. 企业微信 (WeCom)
企业微信群机器人 Webhook，发送 JSON 格式：
```python
def send_wecom_alert(message: str):
    url = "YOUR_WECOM_WEBHOOK_URL"
    data = {
        "msgtype": "text",
        "text": {
            "content": f"[TG Monitor Alert]\n{message}"
        }
    }
    requests.post(url, json=data)
```

### 3. Bark (iOS 推送)
Bark 是 iOS 上一款好用的自定义推送工具，直接 GET 请求即可：
```python
def send_bark_alert(message: str):
    # 格式: https://api.day.app/{your_key}/{title}/{body}
    url = f"https://api.day.app/YOUR_KEY/TG_Alert/{message}"
    requests.get(url)
```

### 4. Telegram Bot
推送给另一个 Telegram 机器人（甚至是自己）：
```python
def send_tg_bot_alert(message: str):
    token = "YOUR_BOT_TOKEN"
    chat_id = "YOUR_CHAT_ID"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    requests.post(url, json=data)
```

## 快速开始 (本地开发)

### 1. 环境准备

确保已安装 `uv` (Python 包管理器)。

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

### 2. 配置

1.  复制 `.env.example` 为 `.env`:
    ```bash
    cp .env.example .env
    ```
2.  编辑 `.env` 文件，填入你的配置:
    *   **TG_API_ID** & **TG_API_HASH**: 需在 [https://my.telegram.org/apps](https://my.telegram.org/apps) 申请。
        > **📝 申请填写指南**:
        > *   **App title**: 随意填写 (如 `MyMonitor`)
        > *   **Short name**: 字母数字组合 (如 `mymonitor2024`)
        > *   **URL**: `http://localhost`
        > *   **Platform**: 选择 `Desktop`
        > *   **Description**: 随意填写 (如 `Personal monitoring`)
        >
        > 点击 "Create application" 后，将页面显示的 `App api_id` 和 `App api_hash` 填入 `.env`。
    *   **TG_PROXY_HOST** & **TG_PROXY_PORT**: (可选，国内环境必须配置) 代理地址和端口，例如 `127.0.0.1` 和 `7890`。
    *   **DINGTALK_WEBHOOK**: 钉钉群机器人的 Webhook URL。
    *   **FEISHU_WEBHOOK**: 飞书群机器人的 Webhook URL。
    *   **SERVERCHAN_KEY**: Server酱 (Turbo/SCT) 的 SendKey。

### 3. 运行 (首次登录)

首次运行需要进行交互式登录，这会在本地生成 `my_session.session` 文件。

```bash
uv run main.py
```

程序会提示 `Please enter your phone (or bot token):`，请按以下步骤操作：

1.  **输入手机号**: 必须包含国家代码（如中国大陆手机号 `+8613812345678`），按回车。
2.  **输入验证码**: Telegram 官方 App (手机或电脑版) 会收到一条包含验证码的消息，输入该验证码。
3.  **输入密码 (如有)**: 如果你的账号开启了 **两步验证 (2FA)**，程序会提示输入密码。

> ✅ **注意**: 登录成功后，你会看到 `Monitoring account: ...` 的提示，且目录下会生成 `my_session.session` 文件。后续再次运行无需重新登录。

## Docker 部署

在本地成功运行并生成 `my_session.session` 文件后，可以使用 Docker 部署。

### 1. 构建镜像

```bash
docker build -t tg-monitor .
```

### 2. 运行容器

必须挂载 `my_session.session` 文件，否则容器内无法登录。

```bash
docker run -d \
  --name tg-monitor \
  --restart unless-stopped \
  -v $(pwd)/my_session.session:/app/my_session.session \
  -v $(pwd)/.env:/app/.env \
  tg-monitor
```

或者直接传递环境变量:

```bash
docker run -d \
  --name tg-monitor \
  --restart unless-stopped \
  -v $(pwd)/my_session.session:/app/my_session.session \
  -e TG_API_ID=your_id \
  -e TG_API_HASH=your_hash \
  -e DINGTALK_WEBHOOK=your_webhook \
  -e SERVERCHAN_KEY=your_key \
  tg-monitor
```

## 注意事项

*   **Session 文件**: `.session` 文件包含了你的登录凭证，请勿泄露给他人。
*   **Docker 挂载**: 务必确保宿主机的 `.session` 文件已生成并成功挂载到容器中，因为容器通常运行在非交互模式，无法输入验证码。
