# 商品折扣、划线价与公告

后续新站默认仅从 **10%、15%、20%、25% OFF 四档**为每站等概率随机选择一次并固定，不从 10–25 的连续整数范围取值。同站所有参与商品、全部 CSV、顶部公告和价格界面使用同一档；不按商品／CSV 各抽一档，也不在顾客访问时随机改价。多站可抽中相同折扣，公告措辞可变化。用户本次明确指定其他比例或不促销时优先。只作用于本次新建／明确指定成品，更新技能不自动修改历史 ZIP、CSV 或后台。

## 先保存本站计划

在本次工作目录的 design.json、promotion-intent.json 或批量 discount-plan.json 保存抽取结果、站点、售价倍率、参考价性质、币种及公告文本。新站可用 `random.choice([10, 15, 20, 25])` 选定；同站继续构建或重跑时读取已保存结果，不重新抽取。10%、15%、20%、25% OFF 分别对应 multiplier=0.90、0.85、0.80、0.75；不能把“售价 85%”写成“85% OFF”。比例和文案可跨站变化，同一站保持一致。

没有价格依据的纯模板保留可编辑中性公告，默认不宣称优惠已生效。完成当前 CSV 定价和核对后，才启用准确含本站百分比的优惠条；schema default、preset、保存 header-group 一致。参考截图的首单、优惠码、免邮和限时承诺分别核对，不自动搬用。

## 原价必须有依据

- 来源是批发报价时，不把采购成本充作零售原价。补查该 SKU 的有效常规零售参考／MSRP，或按已授权范围换成有依据的商品；不能为凑折扣抬价或反推原价。
- 参考价来自其他零售商／MSRP时，保留来源并如实说明性质，不暗示本站曾按该价成交。确认币种、单位与包件数；美元符号本身不能证明 USD。
- 来源价格区间不合适时按授权重新选品；不能悄悄清空 Compare-at、去掉优惠条或改成单价后称促销完成。确实缺依据时说明具体未完成项。

## 逐规格计算一次

- 对原始有价变体，已有合法且较高的 Compare-at price 时以它为参考，否则用修改前有效 Price。先保存原文件／哈希，来源性质仍须独立核对。
- 售价 = 参考原价 × 本站 multiplier，使用 Decimal 和 ROUND_HALF_UP 按币种最小单位舍入；Compare-at price 保留该参考价且严格高于售价。不能对旧折后价再次打折。
- 例：参考价 100.00、本站折扣 15%，则 Price=85.00、Compare-at=100.00；再次执行同一计划仍应得到 85.00。改成 20% 时从 100.00 重算为 80.00，不计算 85.00×0.80。
- Shopify 新表头 Price／Compare-at price 与兼容旧表头 Variant Price／Variant Compare At Price 均可；不另造“Discount price”列。额外图片续行不填写价格或库存，不制造假规格。
- 可用 `python scripts/reprice_products.py --input ORIGINAL.csv --output NEW.csv --multiplier 0.85`。倍率必须显式提供，工具保留其他字段、表头顺序与图片续行并拒绝覆盖现有输出；它不证明来源参考价或实际导入。

## 一起完成公告、数据和所有价格界面

首页／集合／搜索卡片、快速查看、详情、规格切换、吸底购买和购物车读取当前 Shopify 真实变体的双价。不能把不同规格的低售价和高参考价拼成优惠；无有效较高参考价时不显示虚假划线价。手机与暗色区域保证两价可读，不靠隐藏参考价解决拥挤。

Liquid／CSS／JavaScript 不再乘倍率，不额外创建相同自动折扣或优惠码；购物车数量、单价、行价、合计及结账沿用原生实际售价。顶部文案可以是“15% off the everyday edit”“Explore the collection · 20% off”“Your next favorites, now 25% off”，每站文案须与本站已选档位及所有 CSV 一致。仅全目录符合才称 storewide，不虚造倒计时、限时或结账折扣。

## 批量与“所有 CSV”

按本次授权目录重新盘点全部实际成品及嵌套副本，包括未编号目录和多份 csv1…csv10。排除来源、工作、历史备份和素材整合包；保留逐路径分母、原件与哈希。不能只验第一文件或每商品第一规格。

逐站读取本站计划，对全部在售有价变体核对倍率、较高参考价及主题公告。已经正确的文件保持原字节；修正与无需改动分别记录。较旧更深优惠改为本次折扣后售价可能提高，应按参考价重算如实说明，不称所有商品继续降价。修改已有站时不重置其经营资料、文件名或 CSV 份数，不回改范围外历史站。

## 验收

```text
python scripts/promotion_audit.py --csv csv1.csv --csv csv2.csv --theme THEME_DIR --multiplier 0.85 --report WORK/promotion-audit.json
```

为每站显式传其倍率，实际交付有十份就传全部十份；不能把示例 0.85 固定给全部站。脚本核对每规格数学、已启用公告、default、preset，并扫描内页保存文本和 locale 中的优惠短语，尤其详情／快速查看的 reference-price note，防止旧 30% 文案残留。启用本站促销时同步该价格说明，不能只换横幅。脚本不验证参考价真实性、来源库存、Markets 或实际导入。另实际看桌面／手机的公告、双价、切换规格与购物车，独立从原始数据重算，不只复用导出中间值。

新后台商品不会自动继承本地优惠。只上传 ZIP 不更新产品价格，需导入对应新版 CSV；已有商品按实际需要勾选 Overwrite products with matching handles 并保留正确选项列。页面只显示单价时分别检查 CSV、主题 compare-at 条件／对比度与真实后台／Markets，不能未查就归因给用户。后台未操作时明确本地验证范围，不声称已在线显示或结账验证。

官方依据：[商品促销价格](https://help.shopify.com/en/manual/products/details/product-pricing/sale-pricing)、[CSV 字段](https://help.shopify.com/en/manual/products/import-export/using-csv)。
