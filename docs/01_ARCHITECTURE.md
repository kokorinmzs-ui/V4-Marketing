# 01 — Архитектура системы

## 1. Общая архитектура

Marketing OS v4 состоит из четырёх основных слоёв:

```
┌─────────────────────────────────────────────┐
│          Frontend (Next.js 15 + TS)          │
│  Управление проектами, бриф, статус, экспорт  │
└──────────────────┬──────────────────────────┘
                   │ REST API
┌──────────────────▼──────────────────────────┐
│         Backend / Orchestrator (Node.js)      │
│  BriefService → PipelineEngine → ExportSvc   │
│  Queue: generation / repair / export (BullMQ) │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         AI Engine (Python 3.12)              │
│  27 Block Executors                          │
│  Validators (Schema, Business, Quality)      │
│  Repair Engine (≤3 попытки)                  │
│  Cross-Validation Engine                     │
│  Execution Planner                           │
│  HTML Renderer (Jinja2)                      │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│            Storage Layer                      │
│  PostgreSQL 16 + Redis + File Storage        │
└─────────────────────────────────────────────┘
```

## 2. Два слоя системы

### Intelligence Layer (внутренний)

- 27 блоков AI-анализа
- Не показывается клиенту
- Нужен системе для принятия решений
- Результат: `final_data.json`

### Execution Layer (клиентский)

- Преобразует анализ в ежедневные действия
- Готовые тексты, сценарии Reels, скрипты продаж
- Результат: `02-EXECUTION-DASHBOARD.html`

## 3. Поток данных

```
Brief → BriefNormalizer → normalized_brief.json
  → BLOCK 01 → Validate → Repair → ✓
  → BLOCK 02 → Validate → Repair → ✓
  → ...
  → BLOCK 27 → Validate → Repair → ✓
  → Cross Validation
  → final_data.json
  → Execution Planner
  → execution_view_model.json
  → HTML Renderer
  → 02-EXECUTION-DASHBOARD.html
  → Client Package (.zip)
```

## 4. AI Pipeline

### Принцип Step-by-Step

Следующий блок не генерируется, пока предыдущий не получил статус `PASSED`.

### Жизненный цикл блока

```
PREPARE → GENERATE → VALIDATE → (if failed) REPAIR → VALIDATE → STORE
```

- Максимум 3 попытки Repair
- После 3 попыток → `BLOCK FAILED`
- Каждый блок: `pending → running → repairing → passed | failed`

### Параллелизация

Независимые блоки могут выполняться параллельно:

- Блоки 01 (Ниша), 02 (Диагностика), 03 (Конкуренты) — параллельно
- Далее — последовательно по графу зависимостей

## 5. Prompt Architecture

4 уровня промптов:

1. **Master System Prompt** — загружается всегда, философия проекта
2. **Block Prompt** — для каждого из 27 блоков
3. **Repair Prompt** — только при ошибках валидации
4. **Execution Prompt** — только после `final_data.json`

### Контекстная память

Каждый блок получает:

- Master System Prompt
- Project Context (Memory Summary)
- Результаты предыдущих блоков (только нужные)
- Свой Block Prompt
- JSON Schema

## 6. Validation Architecture

5 уровней валидации:

1. **Schema Validation** — структура JSON, типы данных
2. **Business Validation** — маркетинговая логика
3. **Content Validation** — качество контента
4. **Execution Validation** — выполнимость задач
5. **Client Validation** — понятность клиенту

## 7. Quality Gates

### На уровне блока

- Stop Words Engine (4 категории запрещённых слов)
- Anti-Hallucination Engine
- Repetition Validator
- Pain → Offer Validator
- Content Logic Validator

### На уровне финальной сборки

- Cross-Validation (6 валидаторов связей)
- Export Validator
- Dashboard Validator

### На уровне HTML

- HTML Content Quality Gate
- Client Value Gate
- 30-Second Rule

## 8. Инфраструктура

### Docker Compose (dev)

```yaml
services:
  frontend    # Next.js
  backend     # Node.js API
  ai_engine   # Python
  postgres    # PostgreSQL 16
  redis       # Redis
```

### Production

Каждый сервис в отдельном Docker-контейнере.

## 9. Ключевые принципы

- **JSON First** — модель пишет только JSON, HTML генерирует код
- **Step by Step** — последовательная генерация с валидацией
- **Quality First** — жёсткая система Quality Gates
- **Offline First** — финальный HTML без сервера и интернета
- **No Water** — запрет на маркетинговую воду и абстракции
- **Client Simplicity** — результат понятен без маркетолога
