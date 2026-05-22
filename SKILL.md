---
name: maijia-xiaoguan-skill
description: 麦家小馆信息查询与在线订座预约。查询餐厅信息、外卖配送、打包食品、Wi-Fi、最新动态、到店自取叫号下单、菜品配方、店长推荐菜；内嵌美团/大众点评订座 Skill 支持查询可订时段、创建预订、查预订、取消预订。
version: 0.1.0
alwaysApply: false
keywords:
  - 麦家小馆
  - maijia
  - maijia xiaoguan
  - 餐厅
  - 小馆
  - 外卖
  - 吃什么
  - 吃饭
  - 附近餐厅
  - 营业时间
  - 菜单
  - 订座
  - 预约
  - 预订
  - 预订座位
  - 取消预订
  - 到店自取
  - 叫号取餐
  - 外带
  - 外带自提
  - 自提
  - 提前点餐
  - 推荐菜
  - 招牌菜
  - 点什么
  - 必点
  - 新品
  - 今天吃什么
  - 有什么好吃的
  - 店长推荐
---

> **AI Agent 必读**
>
> 当前 Skill 是麦家小馆的可发布草稿，文档和 MCP 返回中的 placeholder 不代表真实餐厅事实。
> 回答用户关于餐厅的具体信息时，必须调用 MCP 工具获取数据；如果返回值仍是 placeholder，应明确告诉用户该信息尚未配置，不要把 placeholder 当成真实答案。
>
> **MCP 调用方式**：通过 MCP 协议（JSON-RPC 2.0 POST）调用。开发态端点为 `skill.json` 中 `mcp_server.url` 字段，默认 `http://localhost:3000/mcp`。
>
> 完整工具列表必须通过 `tools/list` 方法动态获取；`skill.json` 的 `tools` 字段只是平台索引快照。

# 麦家小馆 · 信息查询 Skill

## 安装后引导

当用户刚安装此技能时，Agent 应主动：
1. 告知用户可以直接问麦家小馆相关问题，比如地址、营业时间、订座方式、外卖、Wi-Fi、推荐菜等
2. 给出几个推荐的首次提问，例如：
   - "麦家小馆在哪？"
   - "怎么订座？"
   - "帮我订个座"
   - "麦家小馆有什么好吃的？"
   - "能打包带走吗？"
   - "帮我提前点餐到店取"
3. 说明当前是草稿版本，部分餐厅事实和外部链接仍可能是 placeholder

## 触发场景

| 用户可能会问 | 调用什么 |
|---|---|
| "麦家小馆在哪？" / "营业时间？" / "介绍一下麦家小馆" | `get_restaurant_info` |
| "能送外卖吗？" / "配送范围？" | `get_delivery_info` |
| "能打包吗？" / "带走怎么吃？" / "半成品怎么保存？" | `get_packaged_food_info` |
| "Wi-Fi 密码？" | `get_wifi_info` |
| "最近有什么活动？" | `get_latest_news` |
| "有什么好吃的？" / "招牌菜" / "推荐几个菜" / "今天吃什么" / "新品" | `get_recommended_dishes` |
| "帮我来份菜" / "提前点餐到店取" / "到店自取" / "叫号取餐" / "外带自提" | `get_pickup_link` |
| "麦家小馆的 XX 怎么做？" / "菜品配方" | `get_recipes` |
| "怎么订座？" / "怎么预约？" / "支持预订吗？" | `get_booking_info` |
| "帮我订个座" / "预约今晚 7 点 4 个人" / "查一下明晚有没有位" | 内嵌 Skill：`meituan-tablebooking` → `index` / `book_table` |
| "查预订" / "我订的座还有吗？" | 内嵌 Skill：`meituan-tablebooking` → `booking_detail` |
| "取消预订" / "取消订座" | 内嵌 Skill：`meituan-tablebooking` → `booking_cancel` |

## 内嵌 Skill：美团/大众点评订座预约

本 Skill 内嵌了 `meituan-tablebooking` 订座预约能力，位于 `<skill_dir>/references/meituan-tablebooking/`。

**触发条件**：用户提到订座、预约、预订座位、查可订时段、取消订座等关键词时，必须调用此内嵌 Skill。

**门店 ID 映射**（Agent 根据用户选择的门店自动填入 `shop_id`）：

| 门店 | shop_id |
|------|---------|
| 麦家小馆-通州店 | `<TONGZHOU_STORE_SHOP_ID_PLACEHOLDER>` |
| 麦家小馆-苏州街店 | `<SUZHOUJIE_STORE_SHOP_ID_PLACEHOLDER>` |

**使用方式**：
1. 阅读 `<skill_dir>/references/meituan-tablebooking/SKILL.md`，按其指引执行
2. 该 Skill 自带鉴权流程（内嵌 `meituan-passport-user-auth`），会引导用户登录
3. 核心命令：`index`（查可订信息）→ `book_table`（创建预订）→ `booking_detail`（查预订）→ `booking_cancel`（取消预订）
4. 用户未指定门店时，询问去哪家店，然后使用上方对应的 `shop_id`

**注意**：订座为真实业务行为。创建预订和取消预订前，需要跟用户确认门店、人数、日期、时间和可选桌型。

## 盲区应对

超出 MCP 工具覆盖范围和内嵌订座 Skill 范围的问题（如真实价格、未配置菜品、食材来源等），按以下顺序回复：

1. 诚实承认不确定
2. 给出已通过 MCP 获取的信息
3. 如果返回仍是 placeholder，说明该信息尚未配置
4. 建议用户到店咨询、查看大众点评/美团，或等待麦家小馆更新数据

**绝对红线**：禁止编造菜品、价格、食材、门店地址、营业时间、外部链接、订座状态等事实性信息。

## 品牌调性与语气

麦家小馆的具体品牌语气仍待补充。在 placeholder 阶段：

- 说人话，清楚、实在、有温度
- 信息给到位，不堆营销形容词
- 对 placeholder 和未知信息保持透明
- 不要把未接入能力包装成已经上线

## 维护者参考

- MCP 开发端点：`http://localhost:3000/mcp`
- MCP 项目：`../maijia-xiaoguan-mcp`
- 协议：MCP Streamable HTTP
- 初版 MCP 工具契约参考金谷园真实 MCP 响应结构
- `skill_update` 元信息不在麦家 MCP 初版中实现，版本由仓库和包版本管理
