[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

## 🚀 Hazeron - 浙江大学信息通知机器人

本项目是一个高效、智能的钉钉通知机器人，旨在自动化浙江大学相关网站信息的获取和通知流程。它提供 **主动推送** 和 **被动应答** 两种模式，确保您不错过任何重要信息，并能随时检索已获取的历史数据。

-----

## 💡 项目功能

本项目将传统的信息查询流程完全自动化，聚焦于以下两种核心服务：

### 1\. **信息主动推送**

只需一键启动，自动运行，将最新信息送达用户，无需手动查询。

  * **全自动数据获取：** 定时访问配置好的信息源，自动抓取最新发布的内容。
  * **灵活的个性化配置：** 所有爬取源和规则均通过本地的 `config/sites.json` 文件配置。能个性化定制信息来源。兼容各种网站（包括非校内网站）的信息获取。
  * **专业高效的推送格式：** 消息以简洁美观的 Markdown 格式推送，支持**点击标题直接跳转**到原始链接。

### 2\. **历史查询与应答**

项目启动钉钉 Stream 模式，赋予机器人强大的实时数据检索能力。

  * **强大的布尔逻辑检索：** 支持在聊天中输入包含 **AND/OR/NOT** 关键词的复杂布尔逻辑查询（例如：`搜索 讲座 AND 报告 NOT 艺术`），实现对历史数据的精准、高级检索。
  * **实时指令应答：** 机器人即时响应用户的搜索指令，快速返回与关键词相关的历史通知结果。
  * **持续运行：** 此模式持续运行，作为您的专属“知识库”和“客服”。

-----

## ✨ 项目技术亮点

项目在设计上追求专业和可扩展性，具备以下技术优势：

  * **双模式架构，职责分离：** 清晰地将后台数据处理 (`process`) 与前端交互 (`callback`) 分离，结构稳定。
  * **模块化设计：** 代码结构严格按照职责划分组织（`crawler`, `database`, `dingtalk`, `services`），便于维护和功能扩展。
  * **配置驱动：** 通过 `config/sites.json` 配置即可快速添加新信息源，无需修改核心代码。

-----

## 🛠️ 快速安装与配置

### 1\. 创建钉钉机器人

#### 1\. 创建企业与应用

1.  在钉钉 App 或电脑端中，新建一个企业组织。
2.  搜索并登录 [钉钉开放平台](https://open-dev.dingtalk.com/)，切换到您的企业组织。
3.  点击 **应用开发** \> **企业内部应用** \> **创建应用**。
4.  应用类型选择 **机器人**，并完成基础信息配置。

#### 2\. 配置与发布机器人

1.  创建好新应用后，进入应用详情页，点击 **应用能力** \> **机器人**，然后填写机器人的配置信息（如图标、描述）。消息接收模式设为Stream模式。
2.  在 **应用发布** 页面，完成应用的发布。

#### 3\. 获取核心凭证与 ID

进入您的应用详情页，获取以下配置信息。

| 凭证/ID | 获取路径 | 对应配置变量 | 用途 |
| :--- | :--- | :--- | :--- |
| **Client ID** | **基础信息** \> **应用凭证** | `DINGTALK_APP_KEY` | 机器人身份标识 |
| **Client Secret** | **基础信息** \> **应用凭证** | `DINGTALK_APP_SECRET` | 机器人密钥 |
| **Robot Code** | **应用能力** \> **机器人** | `DINGTALK_ROBOT_CODE` | 机器人唯一编码（SDK 自动处理） |
| **Conversation ID** | 使用 **官方调试工具** | `DINGTALK_CONVERSATION_ID` | 主动推送目标群聊 ID |

> **获取 Conversation ID 步骤：**
>
> 1.  在新企业中发起群聊（可创建一个只有您和机器人的群聊）。
> 2.  将创建好的机器人添加到该群聊中。
> 3.  使用 [钉钉官方调试工具](https://www.google.com/search?q=https://open.dingtalk.com/tools/explorer/jsapi%3Fspm%3Dding_open_doc.document.0.0.5a054a97Awtksx%26id%3D10303)，调用相关接口获取该群聊的 `conversation_id`。


### 2\. 安装依赖

```bash
# 1. 推荐使用虚拟环境
python -m venv venv
source venv/bin/activate  # 或 .\venv\Scripts\activate

# 2. 安装所有依赖
pip install -r requirements.txt
```

### 3\. 配置数据源

编辑 `config/sites.json` 文件，灵活定义您希望机器人获取的所有信息源的 URL、栏目名称和解析规则。当前已预置一部分网站。具体配置指南请见 `config/sites_json_helper.md` 。

### 4\. 填写私密配置和访问方式

创建或编辑 `config/secret_config.py` 文件，**替换所有占位符**。

```python
# config/secret_config.py

# --------------------------------------------------
# 钉钉开放平台配置 (Client ID/Secret)
# --------------------------------------------------
DINGTALK_APP_KEY = "YOUR_APP_KEY"               # 钉钉机器人的 App Key (Client ID)
DINGTALK_APP_SECRET = "YOUR_APP_SECRET"         # 钉钉机器人的 App Secret
DINGTALK_ROBOT_CODE = "YOUR_ROBOT_CODE"         # 钉钉机器人的 RobotCode

# 机器人发送消息的默认对话 ID。用于主动推送。
DINGTALK_CONVERSATION_ID = "YOUR_CONVERSATION_ID" 

# --------------------------------------------------
# WebVPN/数据源访问配置 (如需校外访问校内资源)
# --------------------------------------------------
WEBVPN_NAME = "YOUR_WEBVPN_USERNAME" 
WEBVPN_SECRET = "YOUR_WEBVPN_PASSWORD" 
```
如需启用爬虫的WEBVPN模式（暂时不稳定，默认关闭），请将`crawler/config.py`中的`ENABLE_WEBVPN`改为`True`：

```python
ENABLE_WEBVPN = True
```


-----

## ⚙️ 运行方式

应用通过 `main.py` 和命令行参数来选择工作模式。

### 模式一：主动推送 (`process` mode)

运行一次数据获取、处理和通知推送的完整流程。如需定时运行，可另接入程序。

```bash
python main.py process
```

### 模式二：被动应答 (`callback` mode)

启用机器人的 Stream 模式，保持运行状态，监听并实时响应钉钉群聊中的用户指令。

```bash
python main.py callback
```

-----

## 🔮 未来发展规划

我们的目标是将 Hazeron 升级为一个完全自动、易于部署、且高度用户化的通知服务。

* **实现定时运行：** 接入外部调度或服务器，实现定时运行。
* **简化部署流程：** 探索使用Docker部署、微信接口、云端服务器或者重新开发桌面/移动应用等方案，实现对非技术人员友好的部署流程。
* **更丰富的网站库：** 完善`sites.json`文件，涵盖全校各个网站。
* **易用的订阅管理：** 使用钉钉聊天，或开发Web端管理页面，在不接触`sites.json`的情况实现订阅管理。 
* **与校方合作：** 获取学校的服务器资源，乃至各网站接口，甚至将机器人内置到浙大钉中，彻底解决部署、定时运行等问题。




-----

## 📄 LICENSE

本项目采用 **GNU General Public License v3.0 (GPLv3)** 许可证。

根据 GPL v3.0 许可证的条款，任何使用、修改或分发本项目的代码，或基于本项目代码开发的衍生作品，**都必须**以相同许可证开源发布其源代码。

详细信息请参阅项目根目录下的 **`LICENSE`** 文件。