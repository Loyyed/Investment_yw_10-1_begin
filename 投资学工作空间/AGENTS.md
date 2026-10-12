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
- 本人本轮已审核8d3e80f版本第3节逻辑、第4节数据与三路径并授权突破本地MD范围核准补证、完善内容验收，真实原话见evidence/lec03-content-review.json；不再要求重复内容认可。
- 本轮允许Agent核准2020—2024原年度报告和现金细分补充，以独立evidence/lec03-agent-facts.json绑定授权/PDF/代码/输入/结果，使用ReviewStore.lec03_agent_facts()重检。verifier必须Agent、human_confirmation必须false；不能伪造本人窗口事件，不批量改原候选，不替代旧39条人工域权威。
- 旧U01—U03定位候选保留历史状态，新Agent组核准其相应披露；年度组与旧证据重叠，不报成55个独立Fact。资料和计算变化即重检，新授权不使机制/阶段变为Fact。
- 任务五项成果与前10项内容条件已核准，签署按本人此前约定留空；原条款及实际核验/修正历史保留。品牌定价权与广义成熟期为Interpretation，真实生产成本、壁垒独有性及完整分部资本现金等仍Unknown。
<!-- scope-acceptance:lec03-three-dimensions:end -->

## 2026-10-10本轮授权与研究入口（更新旧签署/网络限制）

- 主交接为../会话交接/01_课件学习与证券分析方法.md和02_任务合同与操作流程.md；当前任务反馈docs/20261010-contract-feedback.md，过程work/INDEX.md。
- 本人允许认定旧有效记录，不重复人工确认，也允许具体质疑、返工、重新核验计算；旧事实不免于检验。来源变化仍按原API规则处理，原人工核验actor与时间不改名。
- 本人明确授权执行人与复核人均签lxy，日期2026-10-10；Agent按真实授权填写并注明同人，不宣称独立审阅。该授权只覆盖本轮已执行副本和签署账本，不伪造新亲查、窗口事件、教师批准或新机制认可。
- 新第五次两份原稿的新增学生亲查条款按实际保留差异，用户认可旧记录不冒充新事件。各版合同、年度变化、研究审阅和正式签署分别记录。
- 网络可用于解释和新闻旁证，单独标来源/日期/支持边界；核心数据以获准本地原稿为准，不拿网页摘要补Unknown。
- 原件/权威账本/候选不覆盖，旧阶段提示保留历史。研究流程六步导航为辅助，不因文件存在、计算通过或签署自动判Fact/机制成立。

- 2026-10-12本轮用户继续此前要求并纳入四份补充文件；执行/复核同人lxy签署按当天2026-10-12另记，旧签署/确认历史保留。当前反馈docs/20261012-supplement-feedback.md；新附件数据/解释不扩旧授权Fact范围。必须登记修正与冲突的旧值/位置、核查计算、处理、影响及Unknown；第七新增学生亲查与新机制裁决未发生不伪造。
