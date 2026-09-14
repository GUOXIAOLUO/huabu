# Recommended UI Replica Wave

> 仅在仓库当前授权 Round/Gate 允许后执行。建议主迁移链稳定到 R10 完成后正式启动大规模 UI Replica Wave。

## UX-01 Design Tokens

- Canvas surface
- color/spacing/radius/elevation
- typography
- edge/selection tokens

## UX-02 Canvas Surface

- top-level chrome
- canvas controls
- low-noise background

## UX-03 NodeShell Replica

- header/body/footer
- status hierarchy
- presentation sizing

## UX-04 Edge / Port Replica

- thin edge
- low-noise port
- hover/selection

## UX-05 Floating Action Bar

- selection-driven actions
- Asset-first experience

## UX-06 Node Picker

- searchable catalog
- categories
- capability metadata

## UX-07 Connect-to-Create

- compatibility filtering
- create+edge canonical command

## UX-08 Parameter Popover

- ratio/resolution/count
- generic parameter summary
- advanced inspector handoff

## UX-09 Task / LLM Node

- TaskRichNode presentation
- Skill/Model/Input/Prompt/Output mode

## UX-10 Collection/Table

- table workspace
- typed collection presentation
- batch UX

## UX-11 Result Workspace

- grid/preview/selection/compare/materialization

## UX-12 Generic Generation Presentation

- retire Provider-specific visual branches where generic schema supports them

## UX-13 Comfy Workflow Builder

- workflow import/version
- input/output discovery
- semantic role mapping
- simplified node definition

## UX-14 Provider / Model Settings Replica

- Settings presentation only; preserve backend contracts

## UX-15 Browser Acceptance Gate

- reference-image review
- interaction acceptance
- architecture guards
- regression suite

## Migration rule

每一个 Classic replacement 都遵循：

```text
characterize current capability
 -> implement generic/shared replacement
 -> delegate existing path
 -> browser acceptance
 -> remove legacy responsibility only after Gate
```
