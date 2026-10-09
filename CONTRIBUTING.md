# 贡献指南

本项目的核心资产是**数据**，而数据质量取决于每一个贡献者是否诚实。

## 最重要的原则

> **宁可标注「未核实」，也不要填入不确定的数值。**
>
> 用户会依据这些数据做真实的用电决策，**错误的数据比没有数据更糟**。

## 最需要的贡献

| 优先级 | 任务 |
|---|---|
| 🔥🔥 最高 | **核实存疑数据**：湖北（`unverified`）、四川电价值（`null`）、内蒙古蒙东实施状态 |
| 🔥🔥 最高 | **补充逐省阶梯电价**：多数省份的 `tiers` 仍不完整 |
| 🔥 高 | 补充同一省内的其他用户类型（如居民充电桩、电采暖的独立价格） |
| 🔥 高 | 追踪政策变动：电价以年度为周期调整，需定期复核 `effective_date` |
| 中 | 补充「无峰谷」省份的例外情形与替代方案 |

## 新增一个省份

1. 阅读 [`schema/tariff.schema.json`](schema/tariff.schema.json)
2. 以政府 / 发改委 / 电网公司官网的**原文**为准（不要用自媒体汇总）
3. 复制一个结构最接近的现有文件作为模板
4. 新建 `data/{省份拼音}.json`
5. 在 `data/index.json` 的 `provinces` 数组中加入对应条目，并更新 `count`
6. 运行 `python scripts/validate.py` 确认通过
7. 提交 PR，并在描述中附上官方来源链接

## 可信度标注规范

必须如实选择 `confidence`：

| 取值 | 适用情形 |
|---|---|
| `official` | 政府 / 发改委 / 电网公司官网原文 |
| `official-media` | 官方媒体（如「上海发布」）转载的官方文件 |
| `unverified` | 自媒体汇总、论坛问答等，**未找到官方原文** |

**不要把自媒体来源标为 `official`。** 这是项目最不可接受的错误。

## 字段填写要求

- `source.url` 必须是可以打开的真实链接
- `effective_date` 填写政策生效日期；若只知道「至少从某日起适用」，填写已知最早日期并在 `notes` 说明
- `accessed_date` 填写你核对数据的日期
- 电价值未知时填 `null`，**不要填 0，也不要凭比例推算后当成官方值**
- 若确需推算（如广东按官方比价换算峰谷单价），必须写入 `price_derivation` 字段明确说明

## 数据校验

提交前请本地运行：

```bash
python scripts/validate.py
```

CI 会在 PR 上自动运行相同校验。

## 提交信息格式

```
data(<省份>): <描述>

示例：
data(zhejiang): add residential TOU tariff from official source
data(hubei): mark as unverified pending official document
fix(guangdong): correct valley period start time
```

## 关于时效性

电价政策会调整。如果你发现某省数据已过期：

1. 找到新的官方文件
2. 更新 `effective_date` 与数值
3. 在 `notes` 中说明变更内容
4. 提交 PR

如果你的省份**仍在执行旧政策**，请不要修改——以官方现行文件为准。
