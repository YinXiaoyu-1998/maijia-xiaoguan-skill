# 麦家小馆 AI Skill

这是麦家小馆的 AI Skill 草稿。安装后，AI 助手可以通过配套的麦家 MCP 服务查询餐厅信息、外卖、打包食品、Wi-Fi、最新消息、推荐菜、菜品配方、到店自取入口，并通过内嵌的 `meituan-tablebooking` 组件处理订座预约流程。

> 当前仓库是可发布结构的草稿。餐厅事实、外部平台 ID、微信小程序链接和美团/大众点评订座接口仍为 placeholder，需要后续替换为麦家小馆真实信息。

## 项目关系

本 Skill 依赖兄弟项目 `maijia-xiaoguan-mcp`：

```text
MAIJIA_SKILL/
├── maijia-xiaoguan-skill/
└── maijia-xiaoguan-mcp/
```

开发态 MCP endpoint:

```text
http://localhost:3000/mcp
```

## 能力

| 能力 | 你可以问 | 来源 |
|------|----------|------|
| 餐厅信息 | "麦家小馆在哪？""几点开门？" | MCP |
| 外卖服务 | "能送外卖吗？""怎么点外卖？" | MCP |
| 打包食品 | "能打包吗？""带回家怎么吃？" | MCP |
| 店内 Wi-Fi | "Wi-Fi 密码多少？" | MCP |
| 最新消息 | "有什么新活动？" | MCP |
| 推荐菜 | "有什么好吃的？""今天吃什么？" | MCP |
| 到店自取 | "帮我来份菜到店取""提前点餐" | MCP |
| 菜品配方 | "麦家小馆的 XX 怎么做？" | MCP |
| 在线订座 | "帮我订个座""预约今晚 7 点 4 个人" | 内嵌 Skill |

## 在线订座预约

本 Skill 内嵌了 `meituan-tablebooking` 订座预约组件，位于 `references/meituan-tablebooking/`。

支持的操作：

| 操作 | 说明 |
|------|------|
| 查询订座状态 | 查看门店是否支持订座、可选日期/时段/桌型 |
| 创建预订 | 选择门店、人数、日期、时间和可选桌型 |
| 查询预订 | 查看当前或最近订座记录 |
| 取消预订 | 取消已有订座记录 |

当前订座接口为 placeholder。组件会保留正常美团 Passport 授权流程形态，但在真实 booking endpoint 配置完成前，不会向 placeholder endpoint 发起 HTTP 请求。

## 目录结构

```text
maijia-xiaoguan-skill/
├── SKILL.md
├── skill.json
├── references/
│   └── meituan-tablebooking/
│       ├── SKILL.md
│       ├── scripts/
│       │   └── mt_tablebooking.py
│       └── references/
│           └── meituan-passport-user-auth/
├── README.md
└── LICENSE
```

## License

MIT
