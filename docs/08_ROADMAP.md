# 08 — Roadmap (План реализации)

Current status: Sprint 0–23 completed, Sprint 23.1 blocked on live DeepSeek credentials.

## План спринтов

| Спринт        | Название                     | Ключевой результат                                             |
| ------------- | ---------------------------- | -------------------------------------------------------------- |
| **Sprint 0**  | Understanding & Architecture | ✅ Анализ ТЗ, архитектура, риски, план                         |
| **Sprint 1**  | Repository Skeleton & Docs   | ✅ Completed                                                   |
| **Sprint 2**  | Shared Schemas & Contracts   | Pydantic-модели, нет `dict[str, Any]`, тесты                   |
| **Sprint 3**  | Validator Engine             | Валидаторы: schema, stop words, repetition, KPI, actionability |
| **Sprint 4**  | Prompt Library               | Master System + 27 block + repair + execution промптов         |
| **Sprint 5**  | AI Provider Layer            | AIService, DeepSeek, retry, JSON parsing                       |
| **Sprint 6**  | Block Engine Base            | BlockExecutor, Registry, DependencyGraph, RepairLoop           |
| **Sprint 7**  | Blocks 01–10                 | 10 блоков: рынок, диагностика, конкуренты, платформа, ЦА       |
| **Sprint 8**  | Blocks 11–20                 | 10 блоков: аватары, психотипы, боли, триггеры, офферы          |
| **Sprint 9**  | Blocks 21–27                 | 7 блоков: посты, визуалы, скрипты, KPI, контроль качества      |
| **Sprint 10** | Cross-validation & FinalData | Кросс-валидация, сборка final_data.json                        |
| **Sprint 11** | Execution Planner            | Миссии, content/ads/sales builders, gamification               |
| **Sprint 12** | HTML Dashboard Renderer      | `artifacts/dashboard.html` — offline, tabs, localStorage       |
| **Sprint 13** | Client Package Export        | ✅ Completed                                                   |
| **Sprint 14** | Frontend Minimal UI          | ✅ Completed                                                   |
| **Sprint 15** | Backend API Layer            | REST API, file storage, FastAPI                                |
| **Sprint 16** | Golden Brief Testing         | 10 эталонных брифов (разные ниши)                              |
| **Sprint 17** | QA Hardening                 | Quality score ≥ 90                                             |
| **Sprint 18** | Deployment                   | Docker Compose, одна команда для запуска                       |
| **Sprint 19** | Frontend ↔ Backend Integration | REST API client, fetch-based UI                                |
| **Sprint 20** | Human Review & Cost Governance | review_required gate, budget metadata                          |
| **Sprint 21** | Production RC Audit          | architecture, security, release gating                         |
| **Sprint 22** | Live AI Reliability Hardening | drift tracker, normalization telemetry                         |
| **Sprint 23** | Prompt Contract Hardening     | exact field rules, no alias drift                              |
| **Sprint 23.1** | Live Reliability Validation | blocked on `DEEPSEEK_API_KEY`                                 |

## Sprint 2 — Shared Schemas & Contracts

**Файлы:**

```
shared/
├── __init__.py
├── schemas/
│   ├── __init__.py
│   ├── brief.py
│   ├── final_data.py
│   ├── execution_view_model.py
│   └── blocks.py
└── constants/
    ├── __init__.py
    └── stop_words.json
```

**Модели Pydantic:** Brief, Project, MarketAnalysis, BusinessDiagnosis, Competitor, Platform, OwnerPortrait, ProductSystem, Flagship, ProductLadder, LeadMagnet, AudienceSegment, Avatar, Psychotype, Pain, Trigger, Offer, Funnel, AdCampaign, ContentPlan, Reel, BlogArticle, Post, VisualBrief, SalesScript, KPI, First7Days, LaunchPlan, QualityReport, FinalData, Mission, ExecutionViewModel

**Тесты:** валидный brief, невалидный brief, валидный final_data, валидный execution_view_model.

---

## Sprint 3 — Validator Engine

**Файлы:**

```
ai_engine/validators/
├── __init__.py
├── schema_validator.py
├── stop_words.py
├── content_quality.py
├── kpi_validator.py
├── actionability.py
├── repetition_validator.py
└── client_simplicity.py
```

**Приёмка:** валидаторы умеют PASS/FAIL. Стоп-фразы типа «нет информации», «ручная проверка», «развивать соцсети» блокируются.

---

## Sprint 4 — Prompt Library

**Файлы:**

```
ai_engine/prompts/
├── __init__.py
├── system/
│   └── master_system_prompt.py
├── blocks/
│   ├── market_analysis_prompt.py
│   ├── business_diagnosis_prompt.py
│   ├── competitor_prompt.py
│   ├── ... (все 27)
│   └── quality_control_prompt.py
├── repair/
│   └── repair_prompt.py
└── execution/
    └── execution_planner_prompt.py
```

**Приёмка:** каждый prompt имеет цель, вход, выход, запреты, JSON schema hint.

---

## Sprint 5 — AI Provider Layer

**Файлы:**

```
ai_engine/providers/
├── __init__.py
├── base.py
├── deepseek.py
└── openai.py
ai_engine/services/
├── __init__.py
└── ai_service.py
```

**Приёмка:** DeepSeek вызывается только через AIService. Есть retry, JSON parse check, ошибки обработаны.

---

## Sprint 6 — Block Engine Base

**Файлы:**

```
ai_engine/pipeline/
├── __init__.py
├── block_executor.py
├── block_registry.py
└── dependency_graph.py
ai_engine/repair/
├── __init__.py
└── repair_loop.py
```

**Приёмка:** мок-блок: generate → validate → repair → passed.

---

## Sprint 7–9 — Blocks 01–27

**Sprint 7:** 01 Ниша, 02 Диагностика, 03 Конкуренты, 04 Платформа, 05 Собственник, 06 Продуктовая линейка, 07 Флагман, 08 Раскладка, 09 Лид-магниты, 10 ЦА

**Sprint 8:** 11 Аватары, 12 Психотипы, 13 Боли, 14 Триггеры, 15 Офферы, 16 Автоворонка, 17 Реклама, 18 Контент-план, 19 Reels, 20 Блог-статьи

**Sprint 9:** 21 Посты, 22 Визуальные ТЗ, 23 Скрипты продаж, 24 KPI, 25 План 7 дней, 26 Единый план запуска, 27 Контроль качества

---

## Sprint 10 — Cross-validation & FinalData Assembly

**Файлы:**

```
ai_engine/pipeline/
├── final_data_assembler.py
└── cross_validators.py
```

**Cross-валидаторы:** Avatar→Pain, Pain→Offer, Offer→CTA, Content→Funnel, Ads→Audience, KPI→Action.

---

## Sprint 11 — Execution Planner

**Файлы:**

```
ai_engine/planner/
├── __init__.py
├── execution_planner.py
├── mission_generator.py
├── content_action_builder.py
├── ads_action_builder.py
├── sales_action_builder.py
├── kpi_action_builder.py
└── gamification_builder.py
```

---

## Sprint 12 — HTML Dashboard Renderer

**Файлы:**

```
ai_engine/exporters/
├── __init__.py
├── html_renderer.py
└── templates/
    ├── dashboard.html
    ├── content.html
    ├── sales.html
    └── logic.html
```

---

## Sprint 13 — Client Package Export

**Выход:** `client-package.zip` (dashboard HTML, content library, sales scripts, README).

---

## Sprint 14 — Frontend Minimal UI

**Экраны:** список проектов, создание проекта, бриф, запуск, статус блоков, скачать HTML.

---

## Sprint 15 — Backend API Layer

**Стек:** FastAPI, Pydantic, file storage. Статусы переживают restart.

---

## Sprint 16 — Golden Brief Testing

10 эталонных брифов: фотостудия, стоматология, автосервис, юрист, онлайн-школа, ресторан, салон красоты, клининг, B2B SaaS, фитнес/БАДы.

---

## Sprint 17 — QA Hardening

Проверка: стоп-слова, повторы, пустые блоки, JS ошибки, mobile, localStorage, dashboard usefulness. Quality score ≥ 90.

---

## Sprint 18 — Deployment

Docker Compose, env, PostgreSQL, Redis, инструкция. Проект запускается одной командой.


