# Skill catalog

These are reusable Kestrel procedures, stored centrally. Read the description and
load only the matching `SKILL.md`. They depend on the surrounding repository and
are not standalone installed host plugins.

| Skill | Trigger |
| --- | --- |
| [kestrel-recall](kestrel-recall/SKILL.md) | Begin or resume a project task; retrieve relevant shared context |
| [kestrel-remember](kestrel-remember/SKILL.md) | Save a useful lesson, decision, project profile, or resumable handoff |
| [kestrel-html-conformance](kestrel-html-conformance/SKILL.md) | Lesson 1: create, edit, generate, or ship HTML; validate final artifacts with the official Nu Html Checker and require a verified zero-error gate |

## Core mathematics (independent curriculum)

Load **only** the relevant module; consult [the mathematics curriculum](../docs/MATH_CURRICULUM.md) for dependencies, assumptions, and the deferred audio integration plan.

| Skill | Trigger |
| --- | --- |
| [math-numerical-analysis](math-numerical-analysis/SKILL.md) | Floating point, error budgets, cancellation, overflow, conditioning and precision |
| [math-verification](math-verification/SKILL.md) | Independent numerical oracles, analytic fixtures, invariants, error bounds and regression evidence |
| [math-dimensional-analysis](math-dimensional-analysis/SKILL.md) | Physical quantities, units, rates, scaling, sample time and dimensional consistency |
| [math-linear-algebra](math-linear-algebra/SKILL.md) | Vectors, matrix operations, coordinate transforms, solves and conditioning |
| [math-complex-numbers](math-complex-numbers/SKILL.md) | Complex arithmetic, polar representations, conjugates, Euler exponentials and phasors |
| [math-probability-statistics](math-probability-statistics/SKILL.md) | Sampling, estimators, distributions, variability and uncertainty |


## PixiJS v8 — official upstream skill package

For PixiJS tasks, **load [pixijs](pixijs/SKILL.md) first**; it routes to the specialized modules below. Load only the modules relevant to the task. These are PixiJS-framework skills, not general JavaScript/TypeScript training. Kestrel's HTML validation and mathematics skills remain applicable. Source revision, license, and update procedure: [PixiJS upstream provenance](../third_party/pixijs-skills/UPSTREAM.md).

| Skill | Trigger |
| --- | --- |
| [pixijs](pixijs/SKILL.md) | Router: use first for any PixiJS v8 task |
| [pixijs-accessibility](pixijs-accessibility/SKILL.md) | Keyboard interaction, screen readers, accessible canvas |
| [pixijs-application](pixijs-application/SKILL.md) | Initialize, resize, run, and destroy Application |
| [pixijs-assets](pixijs-assets/SKILL.md) | Load images, manifests, fonts, spritesheets, and other assets |
| [pixijs-blend-modes](pixijs-blend-modes/SKILL.md) | Compositing and advanced blend modes |
| [pixijs-color](pixijs-color/SKILL.md) | Color parsing, conversion, tint, and premultiplication |
| [pixijs-core-concepts](pixijs-core-concepts/SKILL.md) | Rendering pipeline, render targets, and renderer choices |
| [pixijs-create](pixijs-create/SKILL.md) | Set up new PixiJS applications and TypeScript projects |
| [pixijs-custom-rendering](pixijs-custom-rendering/SKILL.md) | Shaders, uniforms, custom filters, and GPU rendering |
| [pixijs-environments](pixijs-environments/SKILL.md) | Workers, SSR, Node, CSP, and runtime environments |
| [pixijs-events](pixijs-events/SKILL.md) | Pointer/touch/wheel input, dragging, and hit areas |
| [pixijs-filters](pixijs-filters/SKILL.md) | Image effects and filter chains |
| [pixijs-html-source](pixijs-html-source/SKILL.md) | Experimental rendering of live HTML sources |
| [pixijs-math](pixijs-math/SKILL.md) | PixiJS geometry, transforms, coordinates, and hit testing |
| [pixijs-migration-v8](pixijs-migration-v8/SKILL.md) | Upgrade PixiJS v7 code to v8 |
| [pixijs-performance](pixijs-performance/SKILL.md) | Frame pacing, GPU memory, pooling, and profiling |
| [pixijs-scene-container](pixijs-scene-container/SKILL.md) | Container hierarchies, transforms, and bounds |
| [pixijs-scene-core-concepts](pixijs-scene-core-concepts/SKILL.md) | Scene graph, masks, groups, layers, and culling |
| [pixijs-scene-dom-container](pixijs-scene-dom-container/SKILL.md) | HTML overlays and DOMContainer |
| [pixijs-scene-gif](pixijs-scene-gif/SKILL.md) | Animated GIF sources and playback |
| [pixijs-scene-graphics](pixijs-scene-graphics/SKILL.md) | Vector paths, drawing commands, fills, and strokes |
| [pixijs-scene-mesh](pixijs-scene-mesh/SKILL.md) | Mesh geometry, planes, ropes, and perspective |
| [pixijs-scene-particle-container](pixijs-scene-particle-container/SKILL.md) | Large numbers of lightweight particles |
| [pixijs-scene-sprite](pixijs-scene-sprite/SKILL.md) | Sprites, animation, nine-slice, and tiling |
| [pixijs-scene-text](pixijs-scene-text/SKILL.md) | Canvas text, BitmapText, HTMLText, and styles |
| [pixijs-ticker](pixijs-ticker/SKILL.md) | Animation tick callbacks, delta time, and FPS control |

Add future procedures here as they become useful. Keep project-specific recipes
explicit about their applicability and verified revision. A skill may suggest a
method; it does not supply permission to execute it or override project instructions.
