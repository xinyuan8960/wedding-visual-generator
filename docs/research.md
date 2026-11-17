# 调研报告：婚礼视觉生成器 — 第一阶段

日期：2026-11-17
范围：仅调研，未写任何生成逻辑代码。本报告基于对以下仓库的克隆与源码阅读：

| 项目 | 仓库 | License |
|---|---|---|
| Logo Designer Skill | `neonwatty/logo-designer-skill` | MIT |
| Logo Design Skill | `kaankiziltug/logo-design-skill` | MIT（库中 1,432 个第三方 logo 样本**不**在此 MIT 许可范围内，见下） |
| Logo Generator Skill | `op7418/logo-generator-skill` | MIT（README 声明，无独立 LICENSE 文件） |
| VTracer | `visioncortex/vtracer` | MIT |
| linedraw | `LingDong-/linedraw` | MIT |
| vec2art | （无公开源码仓库，见下） | 不适用 |

一个重要澄清：用户问卷中提到的"遵循开放 Agent Skills 格式、纯 Markdown + 无依赖 Python 工具、含 SVG 构建/审计/导出"的"Logo Design Skill"，核实后对应的是 **`kaankiziltug/logo-design-skill`**，而不是 `neonwatty` 的项目（neonwatty 的也是 Agent Skills 格式，但更偏交互式"访谈-探索-迭代-导出"四阶段流程，依赖 Claude Code 的 Task 并行子代理，而不是独立可运行的 Python 工具链）。两者都值得借鉴，但借鉴点不同，下面分别说明。

---

## 1. 逐项目结构、SKILL.md 组织方式、许可证

### 1.1 `neonwatty/logo-designer-skill`（MIT，作者 Jeremy Watt）

```
logo-designer-skill/
├── .claude-plugin/plugin.json      # Claude Code 插件元数据
├── skills/logo-designer/
│   ├── SKILL.md                    # 唯一的技能定义文件
│   └── scripts/
│       ├── export.sh               # SVG→PNG，自动探测 resvg/inkscape/rsvg-convert/sharp
│       └── lineage-handoff.mjs     # 对接一个外部"Lineage"画布审核工具的可选集成
├── docs/plans/…                    # 设计与实现计划文档（给维护者看的）
├── examples/<project>/{concepts,iterations}/*.svg + showcase.html
├── tests/*.test.mjs
└── site/                           # GitHub Pages 展示站
```

**SKILL.md 组织方式**：五阶段线性流程 —
`Phase 1 访谈`（用 `AskUserQuestion` 结构化提问，最多 4 题/批，按上下文跳过已知项）→
`Phase 2 探索`（并行派发 3–5 个 Task 子代理，每个子代理各写一份 `concepts/concept-N.svg`，再生成 `preview.html` 并排展示）→
`Phase 3 精炼`（单条反馈直接改写；"批量变体"需求再次用并行 Task）→
`Phase 4 导出`（固定尺寸 16/32/48/192/512/1024/2048px，bash 脚本自动探测可用渲染器）→
`Phase 5 仓库集成`（可选，把最终 logo 写回目标项目的 favicon/manifest 等位置并开 PR）。

**值得注意的工程细节**：
- SVG 编写规范写在 SKILL.md 正文里（viewBox 规则、不用外部字体、小尺寸可读性要求、`stroke-width` ≥6 等），是"轻编排 + 规则文档"模式，不是把规则写进代码里强制校验——**规则是给模型读的提示，不是给机器跑的测试**。这是和 kaankiziltug 方案的关键差异。
- 导出脚本做了优雅降级：按 `resvg → npx @aspect-build/resvg → sharp → inkscape → rsvg-convert` 顺序探测，找不到任何工具就给出清晰的安装提示而不是报错退出。这个降级链模式值得直接搬。
- 有一段"Lineage 画布评审"的可选集成（通过 npm 脚本把一个 JSON "receipt" 传给 `lineage-handoff.mjs`），默认关闭，只有用户显式要求且提供对接命令才触发。这是三方工具集成，与我们的项目无关，不借鉴。

### 1.2 `kaankiziltug/logo-design-skill`（MIT，1.4.5 版）

```
logo-design-skill/
├── .claude-plugin/{plugin.json, marketplace.json}
├── TRADEMARKS.md                    # 单独声明：库里 1,432 个第三方 logo 不受本仓库 MIT 许可覆盖
├── skills/logo-design/
│   ├── SKILL.md                     # 技能入口：模式选择表 + 7 阶段工作流 + 原则 + 红线 + 索引表
│   ├── references/*.md              # 14 个按主题拆分的参考文档（按需读取，不常驻上下文）
│   ├── scripts/*.py                 # 8 个"无依赖"纯标准库 Python 脚本
│   ├── templates/*.json|md          # 规格/指南模板
│   └── assets/library/              # 1,432 个分类好的参考 SVG + catalog.json + classifications.json
├── evals/evals.json                 # 质量评测集
└── tests/*.py
```

**SKILL.md 组织方式**：不是线性阶段，而是先给一张"用户想要什么 → 用哪种模式 → 从哪个阶段开始"的路由表（新 logo / 点评 / 改版 / 体系 / 仅导出变体），再是 Phase 1–7 的完整设计流程（访谈→研究竞品套路→概念→SVG 构建→测试精炼→**概念检查点暂停**→客户展示→交付kit），每个阶段末尾都指向对应的 `references/*.md` 做深入说明，SKILL.md 本身保持精简（不到 250 行）。这是"薄编排 + 按需加载的参考文档 + 确定性脚本"三层架构，和用户在项目说明里要求的"`SKILL.md` 只做薄编排"高度一致。

**最值得复用的是 `scripts/` 里的确定性工具链**（全部标准库 Python，零第三方依赖）：

| 脚本 | 功能 | 对应我们的需求 |
|---|---|---|
| `svg_audit.py` | 检查 viewBox、是否有 `<text>`/`<image>`/filter、颜色数、渐变、"假挖空"（白色图形叠在深色图形上造成的视觉漏洞）、anchor 点数相对参考库分位数、**近似角度检测**（0.3°–3° 偏离 15° 整数倍角度会被标出）、**小尺寸细节检测**（小于画布 1/48 的子形状会在缩小后消失）、留白/居中、生成 0–100 启发式评分 | 直接对应用户要求的"质检模块：最小线宽、元素重叠、对比度、出血线，不用视觉判断" |
| `export_variants.py` | 生成黑版/白版/品牌单色版/方形/favicon/app-icon 等变体；`--web-icons` 一次产出 favicon.ico + PNG 全套 + webmanifest | 对应导出阶段 |
| `render_png.py` | SVG→PNG，自动挑选 cairosvg/rsvg-convert/Inkscape/headless Chrome/macOS Quick Look 中可用的一种；还能截图 HTML 预览页 | 对应"确定性渲染"环节 |
| `preview_sheet.py` | 生成 HTML 测试表：多尺寸梯子、16/32px 像素级测试、反色、模糊、镜像/旋转检查、与竞品并排"货架测试" | 对应质检/评测集的可视化部分（人工复核用，非自动判定） |
| `presentation_board.py` | 按 JSON spec 生成客户展示稿，含行业相关的 mockup | 超出我们范围（请柬/展示稿暂不做） |
| `search_library.py` / `build_catalog.py` | 在 1,432 个分类好的参考 SVG 库里按类型/技法/几何/行业检索，用于"研究竞品套路、避免撞脸" | **不能直接复用这个库本身**（见版权小节），但"先检索同类参考、列出该行业的俗套元素再刻意避开"这个*方法*值得搬进婚礼 logo 的调研阶段（例如先列出"婚礼 logo 常见俗套：心形、鸽子、交织的戒指"，再要求设计避开或给出新形式） |

**许可证细节（重要）**：仓库本身 MIT，但 `assets/library/svg/` 下 1,432 个真实公司/项目 logo 是示例/参考用途，`TRADEMARKS.md` 明确声明这些文件**不受 MIT 许可覆盖**，仅供"研究学习，禁止描摹/复制"。这正好印证了用户项目里"不实现描摹/矢量化别人 logo 的功能""模板只存参数不存几何数据"的约束方向是对的——哪怘是对标的开源项目，也要把参考库和可再分发代码的许可证分开处理。

### 1.3 `op7418/logo-generator-skill`

```
logo-generator-skill/
├── SKILL.md                  # 无 frontmatter 之外没有插件化包装，更接近"裸技能"
├── .env.example               # GEMINI_API_KEY / GEMINI_API_BASE_URL / GEMINI_MODEL
├── scripts/
│   ├── svg_to_png.py          # 依赖 cairosvg
│   └── generate_showcase.py   # 调用 Gemini "Nano Banana" 图像生成 API 给 logo 配展示背景
├── references/{design_patterns.md, background_styles.md, webgl_backgrounds.md}
└── assets/{showcase_template.html, background_library.html}
```

五阶段流程（信息收集→模式匹配生成 SVG→迭代→**用 Gemini 图像模型生成"高端展示图"**→交付）。SVG 本身由模型直接按"已知几何图案（同心圆点、几何图形+线条装饰、节点网络等）"手写，**没有任何确定性质检或测试脚本**，核心差异化功能（多种工作室级背景）完全依赖 Gemini 图像生成 API，需要 API Key，按用户的"不依赖需要 API key 的图像生成"硬性要求，这个项目**只能作对照，不能复用其生成路径**。唯一有参考价值的是 `references/design_patterns.md` 里归纳的几何图案词汇表（点阵、线系统、节点网络等命名方式），可以作为我们"元素母题类型"枚举值的命名参考。

---

## 2. 复用清单 vs 自写清单

### 复用清单（结构/模式，而非代码原样拷贝——四个仓库都是 MIT，可以参考实现方式后用自己的代码重写，涉及具体函数体照搬的要在来源声明里标注并保留署名）

1. **仓库骨架**：`SKILL.md`（薄编排）+ `scripts/`（确定性无依赖脚本）+ `references/*.md`（按需加载的深度文档）+ `templates/`（spec 模板）+ `tests/` 的五件套分法，直接采用 kaankiziltug 的划分方式。
2. **SVG→PNG 渲染器降级链**：按"原生二进制 → npx 包 → 系统库 → GUI 工具"顺序探测可用渲染器，找不到就给出清晰的安装建议而非报错退出（neonwatty 的 `export.sh`、kaankiziltug 的 `render_png.py` 都是这个模式）。
3. **确定性质检脚本的检查项清单**（不是代码，是检查项本身）：viewBox 合法性、禁止 `<text>`/嵌入栅格/filter、颜色数上限、渐变使用提示、近似角度检测、小尺寸细节消失检测、留白/居中偏差、白色"假挖空"检测、0–100 启发式评分。这些检查项直接对应用户要求的"最小线宽、元素重叠、对比度、出血线"，可以按婚礼 logo 的场景取舍后重写成我们自己的 `qa.py`。
4. **"检查点暂停"交互模式**：kaankiziltug 方案在"展示概念 → 等用户选方向 → 才构建完整交付包"之间设了一个强制暂停点，避免在用户还没选定方向时就把所有变体都做成高精度交付品，浪费算力/token。这个交互设计值得搬到我们的问卷→spec→渲染流程里（例如先出黑白简版 3 个方向预览，用户选定后才跑完整质检+多格式导出)。
5. **研究竞品套路再刻意避开的方法论**（而非具体检索代码）：先列出该品类的视觉俗套（婚礼场景大概是：交织的心形、鸽子、戒指叠加、无衬线手写体+花体混搭），再要求设计给出不落入俗套的处理，写进我们的问卷后处理提示词或 spec 生成的系统提示里。
6. **图案词汇命名方式**参考 op7418 的 `design_patterns.md`，用于设计我们"装饰母题类型"枚举（如 `interlocking-initials` / `botanical-frame` / `banner-ribbon` 等），仅取命名思路，不取其几何图案实现（其实现是直接硬编码 SVG 片段喂给模型抄，和我们"模板只存参数"的约束冲突，不能照搬实现）。
7. **许可证与来源声明的写法**：参照 kaankiziltug 的 `TRADEMARKS.md`，如果我们后续也建一个"参考图案库"用于学习排版规律，必须把"库本身的许可证"和"仓库代码的许可证"分开声明。

### 自写清单（必须自己做，没有现成可搬的参照）

1. **婚礼专属问卷 schema**：四个参照项目的问卷都是"品牌/产品向"（格式、风格方向、颜色），没有任何一个处理"双方姓名（中英文）、纪念日期、多场景地点、照片 vs 姓名两种设计依据、风格滑杆（极简↔华丽/现代↔古典/东方↔西方/手写感↔印刷感）、使用场景决定的尺寸简化版"这类婚礼特有结构。需要我们自己设计。
2. **姓名 monogram / 双名字排版算法**：四个项目都没有真正的"字体轮廓级别排版"——neonwatty 和 op7418 让模型直接手写 SVG 文字路径或用系统字体 `<text>`；kaankiziltug 要求"construct letterforms as paths"但没有给出自动化脚本，靠模型手工画字母路径。用户的设计决策 1（禁止模型直接手写长 SVG、必须确定性代码）意味着我们需要自己用 fontTools 取字形轮廓、自己写双字母交织/同心圆环绕/徽章布局的几何算法，这部分完全是空白，没有现成实现可抄。
3. **同一 spec 字节级确定性输出 + 随机种子控制变体**：四个参照项目都没有这个概念——它们的"随机性"来自模型每次生成不同的 SVG 文本，完全不可复现。我们需要自己设计"seed → 确定性布局参数 → 确定性渲染"的管线，并写回归测试（例如同一 spec+seed 跑两次 diff 字节相同）。
4. **无 LLM 模式（直接写 spec.yaml 出图）**：四个项目全部假设有一个 agent/模型在循环里（neonwatty/kaankiziltug 靠模型驱动流程和 SVG 构建判断，op7418 更进一步依赖 Gemini 图像生成）。没有一个支持"纯手写配置、零模型参与"的路径，这是我们独有的约束，需要自己保证 CLI 可以完全脱离 LLM 跑通。
5. **照片剪影抽象流水线（模式二）**：见下一节详细评估，这是最大的技术空白区。
6. **色卡/风格参数到视觉参数的映射**（极简↔华丽、东方↔西方这种滑杆到具体的线宽比例/留白比例/字体选择的映射规则）：完全没有参照，需要我们自己定义映射表并通过评测集验证。
7. **问卷 schema 校验 + 版权合规护栏**（禁止存储参考图几何数据、`.gitignore` 规则、模板许可证清单生成）：这是我们项目独有的硬性约束，参照项目都没有这类限制（它们允许用户传参考图给模型"提取颜色/字体风格"，也没有刻意区分"可公开复用的参数"和"不可复制的几何数据"）。

---

## 3. 模式二（合照→剪影简笔画）技术路线评估

用户设想的可靠路线："剪影分割 + 轮廓简化 + 曲线拟合 + 统一线宽"，**全部用确定性代码，不碰人脸五官**。评估如下：

### VTracer（`visioncortex/vtracer`，Rust，MIT，1.0 版）

- **能做到什么**：把任意位图矢量化为 SVG。核心是"区域分割（`--clustering color-cluster|bw|watershed`）→ 曲线拟合（`--mode pixel|polygon|spline`）→ 颜色拟合 → 路径优化"四段可插拔流水线，提供 Rust/Python/Node 三种库绑定，也有独立 CLI。关键能力点：
  - `--clustering bw` + `--adaptive`（Bradley–Roth 自适应二值化）：适合把"剪影后的黑白图"转成干净的矢量轮廓，这正是我们需要的"轮廓简化"那一步。
  - `--simplify <tolerance>`：曲线简化（减少贝塞尔节点数，可控制平滑度），对应用户想要的"曲线拟合"步骤，而且是确定性的数值参数，可以被 spec 控制、可复现。
  - `--filter-speckle`：丢弃小于 N 像素的斑点，有助于去掉剪影分割后的噪点。
  - `--palette` / `--max-colors`：如果以后需要限定色卡（用户说色卡暂不做，但这个能力留着备用）。
- **做不到什么（诚实标出局限）**：
  - VTracer **不做"剪影分割"**，它假设输入已经是前景/背景分离好的图（或者直接把整张照片按颜色聚类分区）。如果直接把一张合照丢给它，输出会是"把照片里所有色块都矢量化"的复杂矢量画，不是"一个人形剪影轮廓"——分割这一步必须我们自己先做（人像/人体分割模型，如 `rembg`/`mediapipe` selfie segmentation，或 OpenCV 的传统前景提取）。
  - VTracer 不保证"统一线宽"：它输出的是填充区域（`fill`），不是描边（`stroke`）。如果要"统一线宽的简笔画"效果，需要我们自己在矢量化之后，对轮廓路径做"向内等距偏移再做差集"或者改用描边渲染，VTracer 本身没有这个后处理。
  - 不提供"简笔画风格化"（比如把真实轮廓转成几笔连贯的线条）——它追求的是忠实于原图的矢量化，不是艺术化简化。

### linedraw（`LingDong-/linedraw`，Python 2/3，MIT，2017 年项目，已多年不活跃）

- **能做到什么**：面向绘图机（pen plotter）的线稿转换，核心是"轮廓提取（OpenCV `findContours`）+ 多边形简化（`--contour_simplify`）+ 可选的 hatch 阴影线（用 Perlin 噪声做"素描感"）+ 笔画顺序优化"，输出是"polyline 列表"（`[[(x,y),...],...]`），而不是 SVG 路径曲线——也就是说它天然是"直线段序列"，不是贝塞尔曲线。这对我们想要的"曲线拟合"反而是反向的：它简化为折线，我们还需要再拟合成平滑曲线（可以用 `scipy` 或手写 Catmull-Rom/贝塞尔拟合把折线平滑化）。
- **做不到什么**：同样不做人像分割；`--contour_simplify` 的简化算法比较原始（基于 OpenCV 的 `approxPolyDP`，Douglas-Peucker 类型），可控但谈不上"艺术化"；依赖已停更的 Python 2/3 混用代码，部分 API（如 `scipy.misc.imread`）在新版 scipy 中已移除，**直接拿来跑可能需要先修复依赖**，不建议直接拿它的 `linedraw.py` 做生产依赖，更适合只借用它"OpenCV 轮廓提取 + Douglas-Peucker 简化"这个思路，自己用现代库（OpenCV + Shapely/Pillow）重写。

### vec2art（`vec2art.com`，闭源 SaaS，WASM+Rust）

- 没有公开源码仓库（搜索确认组织/仓库名均不存在，官网只链接社媒和打赏页，无 GitHub 链接）。只能从产品页描述的技术栈做**间接评估**：官网自述支持"edge detection、centerline tracing、superpixel segmentation、stippling"四种风格化矢量化模式，强调"手绘质感"而非忠实复刻。这说明"照片→风格化矢量线稿"这条路径在工程上是可行的（有产品验证了），但**我们没有源码可借�ACM，只能把它当作"目标效果的参考案例"，技术实现要自己从零基于 OpenCV/VTracer 搭**。不建议为了对标它而引入额外的 Rust/WASM 工具链，Python/OpenCV 的确定性流水线足够满足婚礼 logo 的简笔画需求。

### 结论：建议的流水线组合

```
照片 → 人像/人体分割（rembg 或 mediapipe，输出 alpha mask）
     → 二值化剪影（阈值化 mask）
     → OpenCV findContours 提取外轮廓（借鉴 linedraw 思路，而非直接用其代码）
     → Douglas-Peucker 简化（cv2.approxPolyDP 或 Shapely simplify，tolerance 由 spec 控制）
     → 轮廓点序列拟合成平滑贝塞尔曲线（自己写 Catmull-Rom→cubic Bézier 转换，纯数学、确定性）
     → 统一描边渲染（stroke-width 由 spec 控制，fill=none）
     → （可选）VTracer 仅用于"剪影本身要不要填充色块"的场景，而不是人像细节
```

这条路线里，VTracer 负责的是"如果想要填充剪影"这一支路（黑白剪影本来就是一个大色块，用它的 `--clustering bw --adaptive` 可以把剪影位图直接转成一个干净的矢量填充区域，这部分**可以直接复用它的 Python 绑定**），而"分割"和"曲线拟合+统一线宽"这两段核心能力市面上没有现成的、符合我们确定性/无版权风险要求的工具，需要自己基于 OpenCV + 自写几何代码实现。**人像分割模型（rembg 等）本身是训练好的网络，不是"确定性几何代码"，这点需要和您确认是否在"全部确定性代码"的红线之内**——如果红线要求连分割这一步都不能用预训练模型，那需要换成纯传统 CV 方法（如 GrabCut + 手动/半自动抠图），分割精度会明显下降，这是一个需要您来定的权衡，我没有在这份报告里替您做决定。

---

## 4. 建议的仓库结构、spec.schema.json 草案、问卷 schema 草案

### 4.1 建议的仓库结构（骨架阶段落地，不是现在就建全部文件）

```
wedding-visual-generator/
├── SKILL.md                      # 薄编排：指向 CLI 命令 + 问卷流程说明
├── AGENTS.md                     # 给 Codex 等非 Claude agent 的同等说明
├── README.md                     # 含成本对比表、架构图、来源声明
├── pyproject.toml
├── src/wedding_visual/
│   ├── __init__.py
│   ├── cli.py                    # `python -m wedding_visual ...` 入口
│   ├── spec.py                   # spec.json/yaml 的加载与 schema 校验
│   ├── layout/                   # 确定性排版算法（monogram、双名字、剪影）
│   ├── render/                   # SVG 渲染（resvg/cairosvg 封装、PNG/PDF 导出）
│   ├── qa/                       # 质检脚本（借鉴 kaankiziltug 的检查项清单）
│   └── templates/                # 模板参数 JSON（不含任何他人几何数据）
├── schema/
│   ├── spec.schema.json
│   └── questionnaire.schema.json
├── fonts/                        # 仅 OFL 等开源许可字体 + 来源说明
├── tests/
│   ├── test_determinism.py       # 同 spec+seed 字节级 diff
│   └── test_qa.py
├── eval/
│   └── cases/                    # 10 组不同名字的评测用例（占位名）
├── docs/
│   ├── research.md               # 本文件
│   └── sources.md                # 来源与许可声明（参照 kaankiziltug 的 TRADEMARKS.md 写法）
├── private/                      # .gitignore：用户真实参考图/合照
└── .gitignore                    # private/, refs/, __pycache__ 等
```

### 4.2 `spec.schema.json` 草案（仅勾勒核心字段，字段名和枚举值待下一阶段细化）

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "WeddingVisualSpec",
  "type": "object",
  "required": ["version", "seed", "design_basis", "names", "layout"],
  "properties": {
    "version": { "type": "string", "const": "0.1" },
    "seed": { "type": "integer", "description": "控制确定性变体的随机种子" },
    "design_basis": { "type": "string", "enum": ["names", "photo"] },
    "names": {
      "type": "object",
      "properties": {
        "partner_a": { "type": "object", "properties": {
          "latin": { "type": "string" }, "cjk": { "type": "string" } } },
        "partner_b": { "type": "object", "properties": {
          "latin": { "type": "string" }, "cjk": { "type": "string" } } },
        "date": { "type": "string", "format": "date" }
      }
    },
    "style": {
      "type": "object",
      "description": "问卷滑杆值，0-1 区间，用于映射到排版/线宽/留白参数",
      "properties": {
        "minimal_to_ornate": { "type": "number", "minimum": 0, "maximum": 1 },
        "modern_to_classic": { "type": "number", "minimum": 0, "maximum": 1 },
        "eastern_to_western": { "type": "number", "minimum": 0, "maximum": 1 },
        "handwritten_to_print": { "type": "number", "minimum": 0, "maximum": 1 }
      }
    },
    "layout": {
      "type": "object",
      "required": ["template_id"],
      "properties": {
        "template_id": { "type": "string", "description": "引用 templates/ 下的参数化模板，不内联几何数据" },
        "monogram_arrangement": { "type": "string", "enum": ["interlocking", "stacked", "circular-badge", "side-by-side"] },
        "stroke_width_ratio": { "type": "number" },
        "whitespace_ratio": { "type": "number" }
      }
    },
    "photo_silhouette": {
      "type": "object",
      "description": "仅 design_basis=photo 时使用",
      "properties": {
        "source_ref": { "type": "string", "description": "指向 private/ 下的本地文件，不入库" },
        "simplify_tolerance": { "type": "number" },
        "stroke_width": { "type": "number" }
      }
    },
    "usage_targets": {
      "type": "array",
      "items": { "type": "string", "enum": ["invitation", "e-invite", "stage-backdrop", "merchandise"] }
    },
    "fonts": {
      "type": "object",
      "properties": {
        "primary": { "type": "string" }, "secondary": { "type": "string" }
      }
    },
    "avoid_elements": { "type": "array", "items": { "type": "string" } }
  }
}
```

### 4.3 问卷 schema 草案（问卷 → spec 的中间层，字段对应 LLM 窄边界任务的输出）

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "WeddingQuestionnaireAnswers",
  "type": "object",
  "required": ["partner_a_name", "partner_b_name", "date", "design_basis"],
  "properties": {
    "partner_a_name": { "type": "object", "properties": { "latin": {"type": "string"}, "cjk": {"type": "string"} } },
    "partner_b_name": { "type": "object", "properties": { "latin": {"type": "string"}, "cjk": {"type": "string"} } },
    "date": { "type": "string", "format": "date" },
    "venues": { "type": "array", "items": { "type": "string" }, "description": "可多个场景地点" },
    "design_basis": { "type": "string", "enum": ["names", "photo"] },
    "photo_ref": { "type": "string", "description": "本地路径，仅在 design_basis=photo 时必填，不提交到仓库" },
    "style_sliders": {
      "type": "object",
      "properties": {
        "minimal_to_ornate": { "type": "number", "minimum": 0, "maximum": 1 },
        "modern_to_classic": { "type": "number", "minimum": 0, "maximum": 1 },
        "eastern_to_western": { "type": "number", "minimum": 0, "maximum": 1 },
        "handwritten_to_print": { "type": "number", "minimum": 0, "maximum": 1 }
      }
    },
    "usage_targets": { "type": "array", "items": { "type": "string", "enum": ["invitation", "e-invite", "stage-backdrop", "merchandise"] } },
    "preferred_elements": { "type": "array", "items": { "type": "string" } },
    "avoid_elements": { "type": "array", "items": { "type": "string" } },
    "reference_images": {
      "type": "array",
      "items": { "type": "string" },
      "description": "仅用于提取风格参数（如 style_sliders 的估计值），不描摹几何"
    }
  }
}
```

---

## 待您确认的问题（不自行拍板）

1. **模式二的"分割"步骤是否允许使用预训练模型**（如 `rembg`）？如果用户的"全部确定性代码"红线是严格的，分割这一步必须换成传统 CV 方法（GrabCut 等），精度会下降，这是一个需要您决定的权衡。
2. 是否认可把 **`kaankiziltug/logo-design-skill` 的 `scripts/` 检查项清单**作为我们 `qa/` 模块的设计参照（重写代码，只借鉴检查项和评分思路）？
3. 是否同意跳过 `op7418/logo-generator-skill` 和 `vec2art` 的任何代码复用（二者分别依赖 Gemini API 和完全闭源），仅作为"反面对照"和"目标效果参考"写进 README 的成本对比表？

调研用的克隆仓库已放在系统临时目录（`/private/tmp/.../scratchpad/research/`），不会进入本仓库；README 的来源声明章节会在骨架阶段正式引用本报告的许可证信息。

请确认后我再进入"阶段 1：脚手架 + spec schema + 测试框架"。
