# config/sites.json 字段说明

本文档用于帮助项目参与者理解并添加 `config/sites.json` 中的站点/栏目配置项。文档包含字段说明、示例、调试建议以及开发者提示。

---

## 概览

`config/sites.json` 是一个站点配置数组。每一项描述一个站点或栏目（site 或 channel）的抓取配置。项目支持两种抓取模式：`html`（HTML 页面解析）和 `api`（JSON 接口）。

---

## 顶层站点条目示例（最小）

```json
{
  "name": "示例站点-通知",
  "mode": "html",
  "max_count": 10,
  "html_config": {
    "url": "https://example.com/list",
    "base_link_url": "https://example.com/",
    "selectors": {
      "list_selector": "ul.items li",
      "title_selector": "a.title",
      "date_selector": "span.date"
    }
  }
}
```

### 字段详解

- `name` (string)
  - 站点或栏目的可读名称，用于日志显示和识别。

- `mode` (string) — 必填
  - 抓取模式：`"html"` 或 `"api"`（不区分大小写）。
  - `html`：解析 HTML 列表页面。
  - `api`：请求 JSON 接口并解析响应。

- `max_count` (integer) — 可选/推荐必填
  - 单个 URL 或栏目每次抓取返回的最大条目数。
  - 一般为单个页面的所有通知数。
  - 若不提供，handler 会使用内部默认（通常为 5）。代码中通常使用 `channel_task.get("max_count", 5)`。

---

## HTML 模式（`html_config`）

`html_config` 为对象，常见字段：

- `url` (string 或 array)
  - 列表页 URL，支持字符串或字符串数组（字符串数组仅用于新通知可能在多页的情况，例如置顶通知高达两三页的本科生院官网）。

- `base_link_url` (string)
  - 用于拼接详情页链接的基础 URL。当列表只给出相对链接或 API 返回 id 时，使用该字段构造完整链接。

- `selectors` (object)
  - `list_selector` (string) — 必填：定位包含每条记录的父元素（例如 `ul li`）。
  - `title_selector` (string | null) — 定位标题元素（例如 `a.title`）。
  - `date_selector` (string | null) — 定位日期元素；为 `null` 时可配合 `date_regex` 使用。
  - `date_regex` (object) — 可选：如日期不作为单个元素存在。从 HTML 片段中用正则提取并用 `format` 重组日期。
    - `pattern`：正则（需包含捕获组）。注意 JSON 中 `\` 需转义。
    - `format`：格式串，使用 `$1`、`$2` 等占位符替换捕获组。

示例（含 date_regex）：

```json
"selectors": {
  "list_selector": "ul.items li",
  "title_selector": "a.title",
  "date_selector": null,
  "date_regex": {
    "pattern": "<h3>\\s*(\\d{1,2})\\s*</h3>.*?<p>\\s*(\\d{4}-\\d{2})\\s*</p>",
    "format": "$2-$1"
  }
}
```

---

## API 模式（`api_config`）

用于描述如何从 JSON 接口中提取记录。常见字段：

- `url` (string 或 array)
  - API 地址或地址数组。

- `base_link_url` (string)
  - 用于拼接详情页的基础地址，例如 `https://site/detail?id=`。

- `data_path` (array of string|int) — 可选
  - 在 JSON 响应中定位到记录列表的路径，例如 `["data", "records"]`。

- `fields_map` (object) — 推荐/必填
  - 指定记录对象中对应的字段名：
    - `title`：标题字段。
    - `date`：日期字段。
    - `link_key`：用于拼接或直接返回的链接字段名。

构造 link 的常见逻辑：
- 若存在 `base_link_url` 且 `link_key` 有值 -> `base_link_url + record[link_key]`。
- 若 `record[link_key]` 是完整 URL 且 `base_link_url` 为空 -> 直接使用该 URL。
- 若 `link_key` 缺失且 `base_link_url` 存在 -> 使用 `base_link_url` 作为入口页链接。

---

## channels（多栏目）

对于有多栏目的网站，请使用这一结构。

通过 `channels` 数组定义多个栏目，每个 channel 可包含 `channel_name` 与 `url`。也可包含其他上级标签的字段，以在本 channel 中覆盖上级标签对应字段。

```json
"channels": [
  { "channel_name": "党建工作", "url": "http://.../dwgz/list.htm" },
  { "channel_name": "综合事务", "url": "http://.../51192/list.psp" }
]
```