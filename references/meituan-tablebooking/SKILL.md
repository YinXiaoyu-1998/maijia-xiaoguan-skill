---
name: meituan-tablebooking
description: |
  【强制调用】当用户提到任何与餐厅订座、预约、预订座位、查可订时段、取消订座相关的内容时，必须调用本 Skill。
  需要点评门店 ID（shop_id），如用户未提供则由主 Skill 根据门店名称映射。
  流程：index 查可订信息 → 跟用户确认门店、人数、日期、时间和可选桌型 → book_table 创建预订 → booking_detail/booking_cancel。
  脚本返回格式化文案，直接展示给用户即可。

  触发词: "订座", "预约", "预订", "预订座位", "订个座", "预约座位", "查可订", "取消订座", "查询预订", "booking"

allowed-tools: Bash(python3:*)

metadata:
  skillhub.creator: "maijia-placeholder"
  skillhub.version: "V0"
  skillhub.high_sensitive: "false"

skill-dependencies:
  meituan-passport-user-auth:
    client_id: "<MEITUAN_TABLEBOOKING_CLIENT_ID_PLACEHOLDER>"
    env: "prod"
---

# 美团/大众点评订座预约

> 当前为麦家小馆订座能力草稿。鉴权流程按真实美团 Passport 形态保留；订座接口 URL 与 endpoint 仍为 placeholder，配置真实 endpoint 前不会向 placeholder endpoint 发起 HTTP 请求。

脚本路径：当前 Skill 目录下 `scripts/mt_tablebooking.py`。所有命令返回格式化文案，直接展示给用户即可。

## 鉴权

本 Skill 内嵌了 `meituan-passport-user-auth` Skill，位于 `<skill_dir>/references/meituan-passport-user-auth/`。

**鉴权优先级**（从高到低）：

1. 环境变量：`MT_TABLEBOOKING_TOKEN=<token>`
2. 命令参数：`--token <token>`
3. 自动授权：通过内嵌 `meituan-passport-user-auth` 安装/调用 `pt-passport`

**订座 client_id**：

- 默认：`<MEITUAN_TABLEBOOKING_CLIENT_ID_PLACEHOLDER>`
- 可通过环境变量 `MT_TABLEBOOKING_CLIENT_ID` 或命令参数 `--client-id` 覆盖

在真实 `client_id` 配置前，自动授权会提示占位符未配置。

## 命令

### 1. 查询订座状态

```bash
python3 <skill_dir>/scripts/mt_tablebooking.py index <shop_id> --date <YYYY-MM-DD>
```

返回门店是否支持订座、可订日期/时段/桌型等信息。当前 endpoint 为 placeholder 时，返回未配置提示。

### 2. 创建预订

**前置条件**：必须先调 `index` 获取可订信息。

创建预订前必须向用户确认：

- 门店
- 就餐人数
- 日期
- 时间
- 桌型或包间（如可选）

```bash
python3 <skill_dir>/scripts/mt_tablebooking.py book_table <shop_id> \
  --people-count <N> \
  --date <YYYY-MM-DD> \
  --time <HH:mm> \
  --table-type-id <ID>
```

`--table-type-id` 在接口未要求时可省略。

### 3. 查询预订

```bash
python3 <skill_dir>/scripts/mt_tablebooking.py booking_detail <shop_id>
```

### 4. 取消预订

取消前必须跟用户确认。

```bash
python3 <skill_dir>/scripts/mt_tablebooking.py booking_cancel <shop_id>
```

## 典型工作流

1. `index` → 获取可订日期、时段和桌型
2. 根据用户输入确认门店、人数、日期、时间和桌型
3. 参数确认后 → `book_table`
4. 需要时 `booking_detail` 查预订，`booking_cancel` 取消

## 错误处理

- `client_id 仍为 placeholder` → 提示维护者配置 `MT_TABLEBOOKING_CLIENT_ID`
- `订座接口尚未配置` → 告知用户当前 Skill 尚未接入真实订座接口
- `当前无预订记录` → 用户尚未创建预订
- 网络超时 / 连接失败 → 检查网络，稍后重试；若持续失败建议前往美团/大众点评确认

## 声明

- 本 Skill 将以用户自身账号执行订座操作。
- 创建预订和取消预订是潜在真实业务操作，请确认后再执行。
- Token 仅用于当次 API 请求，不应输出到回复正文或日志。
