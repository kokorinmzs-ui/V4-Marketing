# Marketing OS v4

**«Бери и делай»** — AI-система, превращающая бриф бизнеса в интерактивный offline HTML-файл с готовым маркетинговым планом действий.

## Что делает система

```
Бриф клиента → 27 блоков AI-анализа → final_data.json → Execution Planner → `artifacts/dashboard.html`
```

Клиент открывает HTML двойным кликом и видит:

- Что сделать сегодня
- Что опубликовать
- Что снять (Reels с посекундным сценарием)
- Какую рекламу запустить (с бюджетом и KPI)
- Какие скрипты продаж использовать
- Что измерить
- Что делать, если сработало / не сработало

## Архитектура

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

## Два слоя системы

| Слой                               | Назначение                                                                                            | Кто видит               |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------- | ----------------------- |
| **Intelligence Layer** (27 блоков) | Глубокий AI-анализ: рынок, конкуренты, аватары, боли, офферы, воронки, контент, реклама, продажи, KPI | Только система          |
| **Execution Layer**                | Ежедневные задания с готовыми текстами, сценариями Reels, скриптами продаж, KPI                       | Клиент (HTML Dashboard) |

## Технологический стек

| Компонент      | Технология                                            |
| -------------- | ----------------------------------------------------- |
| Frontend       | Next.js 15, TypeScript, Tailwind + shadcn/ui, Zustand |
| Backend        | Node.js, Next.js API / FastAPI                        |
| AI Engine      | Python 3.12, Pydantic, Jinja2, httpx, tenacity        |
| LLM            | DeepSeek Chat (основной), OpenAI GPT (резервный)      |
| Database       | PostgreSQL 16 + Prisma ORM                            |
| Queue/Cache    | Redis + BullMQ                                        |
| HTML Dashboard | Offline vanilla HTML/CSS/JS                           |
| Infrastructure | Docker Compose, Docker                                |

## Структура проекта

```
marketing-os-v4/
├── frontend/          # Next.js 15 + TypeScript (UI для маркетолога)
├── backend/           # API + Orchestrator (Node.js)
├── ai_engine/         # Python 3.12 AI Engine
│   ├── blocks/        # 27 блоков Intelligence Layer
│   ├── prompts/       # Prompt Library
│   ├── validators/    # Валидаторы (Schema, Stop Words, Quality...)
│   ├── repair/        # Repair Loop Engine
│   ├── pipeline/      # Pipeline Engine
│   ├── providers/     # LLM провайдеры (DeepSeek, OpenAI)
│   ├── services/      # AIService
│   ├── planner/       # Execution Planner
│   └── exporters/     # HTML Renderer, ZIP Exporter
├── shared/            # Pydantic схемы, JSON контракты, константы
├── tests/             # Unit, Integration, Golden Briefs
├── infra/             # Docker Compose, Dockerfiles
├── docs/              # Документация
└── scripts/           # Вспомогательные скрипты
```

## Быстрый старт

### Предварительные требования

- Node.js 20+
- Python 3.12+
- Docker & Docker Compose
- API ключи DeepSeek и/или OpenAI

### Установка

```bash
# Клонировать репозиторий
git clone <repo-url>
cd marketing-os-v4

# Скопировать .env
cp .env.example .env
# Заполнить .env ключами API

# Запуск через Docker Compose (рекомендуется)
docker compose up

# Или запуск вручную
# AI Engine
cd ai_engine
pip install -r requirements.txt
python main.py

# Backend
cd backend
npm install
npm run dev

# Frontend
cd frontend
npm install
npm run dev
```

Открыть: http://localhost:3000

## Статус разработки

| Sprint | Status |
| --- | --- |
| Sprint 0 — Understanding & Architecture | ✅ Completed |
| Sprint 1 — Repository Skeleton & Docs | ✅ Completed |
| Sprint 2 — Shared Schemas & Contracts | ✅ Completed |
| Sprint 3 — Sprint 13 | ✅ Completed |
| Sprint 14 — Frontend Minimal UI | ⏳ Pending |

## Ключевые принципы

- **JSON First** — модель никогда не пишет HTML, только JSON
- **Step by Step** — следующий блок не генерируется, пока предыдущий не прошёл валидацию
- **Quality First** — жёсткая система Quality Gates на каждом этапе
- **Client Simplicity** — результат обязан быть понятен владельцу бизнеса без маркетолога
- **Offline First** — финальный HTML работает без сервера, без интернета, двойным кликом
- **No Water** — запрещены «развивайте соцсети», «уникальный подход», «повышайте вовлечённость»
- **Provider order** — `PRIMARY_LLM_PROVIDER=deepseek`, `FALLBACK_LLM_PROVIDER=openai`
- **Runtime mode** — тесты и фикстуры могут работать в `mock_mode`, но production-путь идёт через реальные провайдеры

## Документация

Подробная документация находится в каталоге [docs/](./docs/):

- [01 Архитектура](./docs/01_ARCHITECTURE.md)
- [02 Контракты данных](./docs/02_DATA_CONTRACTS.md)
- [03 Блоки Intelligence Layer](./docs/03_BLOCKS.md)
- [04 Система промптов](./docs/04_PROMPTS.md)
- [05 Валидаторы](./docs/05_VALIDATORS.md)
- [06 Execution Planner](./docs/06_EXECUTION_PLANNER.md)
- [07 HTML Dashboard](./docs/07_HTML_DASHBOARD.md)
- [08 Roadmap](./docs/08_ROADMAP.md)

## Source of Truth

- **NEW Marketing .docx** — Master Specification (25 томов)
- **ТЗ DeepSeek как разрабатывать .docx** — план спринтов и правила разработки

## Лицензия

Proprietary. Все права защищены.

