# Video Replica Acceptance Checklist

此清单用于每个 UX/UI Task Card 的验收。不能只看截图，必须同时验证架构与交互。

## A. Canvas

- [ ] 背景低噪、近白、无重装饰。
- [ ] 常驻全局控件数量接近视频的克制程度。
- [ ] pan/zoom/select 不回退。
- [ ] semantic zoom 正常。
- [ ] 多选、拖动、删除等既有能力不回退。

## B. Node Shell

- [ ] Header 轻量，没有厚重 Provider 色块。
- [ ] Card 圆角/边框/阴影接近参考视频。
- [ ] 默认 Ready/Done 状态不过度抢眼。
- [ ] Running/Error 状态清晰。
- [ ] Footer 信息结构统一。
- [ ] Card 未塞入 Workspace 级复杂 UI。

## C. Ports / Edges

- [ ] 默认 edge 细且浅。
- [ ] selected/hover 清晰但不过度。
- [ ] port 默认低存在感。
- [ ] connect-to-create 可用。
- [ ] compatibility filter 使用正式类型/兼容边界，而非纯 UI hardcode。

## D. Node Picker

- [ ] 支持搜索。
- [ ] 支持分类。
- [ ] 显示兼容节点。
- [ ] 新 package/definition 在不修改 Canvas source 的前提下可进入 catalog（目标态）。
- [ ] 选择后走 canonical NodeCreation/GraphMutation。

## E. Parameter Popover

- [ ] 高频参数仍可快速操作。
- [ ] ratio/resolution 等能像参考视频一样在轻量浮层选择。
- [ ] Card 只显示摘要。
- [ ] 高级参数可进入 Inspector。

## F. Task/LLM

- [ ] 支持 resource inputs。
- [ ] Prompt 区清晰。
- [ ] Skill 与 Model 分离。
- [ ] Output mode 可表达 text/list/structured（按能力）。
- [ ] 不将 LLM vendor 固化为 NodeKind。

## G. Collection

- [ ] table presentation 可用。
- [ ] typed columns/rows 不丢。
- [ ] 能驱动批量执行。
- [ ] 批量失败/取消/重试不依赖前端裸循环。

## H. Result

- [ ] Thumbnail grid。
- [ ] Preview。
- [ ] Selection。
- [ ] Compare。
- [ ] Result -> Collection。
- [ ] Result -> Canvas/Resource materialization。
- [ ] UI 看起来是一套统一 Result experience。

## I. ComfyUI

- [ ] workflow 版本明确。
- [ ] input role mapping 可配置。
- [ ] Workbench node 只暴露映射参数。
- [ ] 不把 Comfy 全图复制进 Unified Canvas。
- [ ] local/cloud connection 不需要改变 Canvas node architecture。

## J. Architecture Regression

- [ ] 没有新增第二套 Canvas Runtime。
- [ ] 没有把 WholeHouse 业务塞入 Core Canvas。
- [ ] 没有新增永久 Provider-specific NodeKind（除非架构文档明确授权）。
- [ ] 没有把 secret 持久化进节点。
- [ ] 没有绕过 NodeCreation/Mutation/GraphMutation。
- [ ] 没有扩大 `classic-*` 新业务责任。
- [ ] Legacy capability 未经 Gate 不被盲删。

## K. Pixel/Interaction Review

每个卡至少附：

1. 实现截图。
2. 对应 REF 图片编号。
3. 差异说明。
4. 若故意不 1:1，说明是因何架构/可用性约束。
5. 浏览器实际交互验收结果。
