# 项目协作规则

- 先读../会话交接/CURRENT.md；稳定偏好按需读../会话交接/DECISIONS.md。只读本次相关合同和成果，不全文读取日志，不重新扫描项目。
- sources保持原样；不得修改工作空间内外的原件，不把摘要当来源。
- 统一人工核验入口为“人工核验入口.cmd”。原始披露Fact须由本人明确点击确认，才由程序写入evidence/review-state.json；开窗、选择条目、机器匹配、任务文字校对均不自动确认。
- 原始披露人工确认由review-state.json的记录和事件历史维护；confirmed-facts.json与Markdown为派生视图。后续使用调用scripts/review_store.py的ReviewStore(...).facts()核对最新来源，不只凭旧导出文件判Fact。
- 指定源PDF或候选内容改变，旧确认对当前材料失效，需本人重核。缺证、疑问、撤回保留Unknown及历史。
- 原始work/structured-data.json继续保留提取状态；不得把机器候选批量改成Fact，不能把来源核验扩大为机制成立。
- 姓名可待补，但确认方式、时间、位置、口径与支持边界自动保留。核验确认、复核签署和合同正式关闭分别记录，不代填签名。
- 分开Fact、Interpretation、Forecast、Decision、Unknown，不访问合同外网页/数据库，不混入期后信息或作买卖建议。
- 第四次可比性在核验入口独立确认，来源/两期原值绑定后才能复算。第一次通过不自动确认可比性，程序结果仍须本人核对。
- 含人工记录或手写修改时，旧生成脚本停止重建；不得覆盖evidence、人工notes或合同。需要重建时使用新的资料副本。
- 保存前检查差异，保留被排除候选、真实修正与Unknown，不强制回滚，不伪造学生核验或错误。
- 第四次复算结果按约定可由本人明确聊天确认；实际原话及所指上下文保存在evidence/change-review-state.json，不伪造窗口事件。变化Fact使用ReviewStore(...).change_facts()重新校验PDF、输入、原值Fact、可比性及公式结果；change-confirmed-facts.json仅为派生视图。

<!-- scope-acceptance:m01-disclosures:start -->
- M01本人已在聊天逐项引用核对的公司自述独立登记evidence/m01-disclosure-review.json，属于公司披露叙事核验，未写入原数值窗口权威。调用ReviewStore.m01_disclosure_facts()校验PDF、清单、真实答复和对应事件；导出不能单独证明Fact。该约定只覆盖M01-D01—D03；不把管理层原因解释确认为因果，不扩展原数值窗口规则。
- 本人已明确聊天确认M01计算表的输入、单位和结果；原输入JSON保留提取状态，当前确认由独立计算账本维护。均价使用匹配销售收入÷销量；不得以粒度限制否定产品组统计，也不得将它直接等同固定产品终端价格或可持续定价权。
<!-- scope-acceptance:m01-disclosures:end -->

<!-- scope-acceptance:m01-metric-confirmation:start -->
- M01计算结果本人明确聊天确认保存在evidence/m01-metric-review.json；原话、对应审阅版本及真实事件保留，不伪造窗口事件。使用ReviewStore.m01_metric_facts()重检PDF/清单、输入、原披露Fact绑定、计算脚本、公式、单位与结果；变化即Unknown并留历史。m01-metric-facts.json及计算表仅是派生视图。
- 可重运行calculate_m01_metrics.py以复算并保留当前有效确认；不得运行旧生成脚本重写人工历史。15项统计Fact不证明品牌因果、终端动销或可持续性；姓名签署继续留空。
<!-- scope-acceptance:m01-metric-confirmation:end -->

<!-- scope-acceptance:m01-cost-confirmation:start -->
- 本人M01成本聊天确认保存在evidence/m01-scale-review.json，使用ReviewStore.m01_scale_facts()重新校验PDF/清单、输入、已有Fact、计算及核验代码、公式和结果；变化回Unknown并留历史。M01-K01/K02为有范围的成本统计，K03只为原数及附条件算术，不能当实际生产成本Fact。
- 生产桥接state与五项假设继续Unknown；arithmetic_state可为Fact。原数值窗口账本及原候选提取状态不批量升级。calculate_m01_scale.py可复算并保留当前有效确认；不运行旧生成脚本重建人工历史。姓名签署仍空。
<!-- scope-acceptance:m01-cost-confirmation:end -->

<!-- scope-acceptance:lec03-three-dimensions:start -->
- 本人已在成本核验后明确维持品牌定价权暂定Interpretation；当前更新为evidence/m01-research-judgment-updates.json，原m01-research-judgment.json保留。M01/B01本人选定，I01本人明确授权Agent定义，见lec03-research-update.json；不反复询问已确定问题。
- 三维新逻辑尚待审阅；U01—U03只是定位候选Unknown，不属于39条有效记录。选题、维持判断或授权展开不新增Fact；五接口仍为当前事实权威。行业阶段、份额/相对优势和分部资本现金缺证，不混入外部信息或虚构Lec04—05合同。
<!-- scope-acceptance:lec03-three-dimensions:end -->
