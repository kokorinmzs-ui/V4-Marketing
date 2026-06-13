# 02 — Контракты данных

## 1. Главный принцип

Все компоненты системы общаются только через JSON. Запрещено: Markdown, HTML, текстовые отчёты, свободный текст.

## 2. Поток контрактов

```
Brief → brief.json → Normalizer → normalized_brief.json
  → Intelligence Layer → final_data.json
  → Execution Planner → execution_view_model.json
  → HTML Renderer → `artifacts/dashboard.html`
```

## 3. brief.json

Точка входа в систему.

### Схема

```json
{
  "project_id": "string",
  "project_name": "string",
  "industry": "string",
  "business_description": "string",
  "region": "string",
  "target_markets": ["string"],
  "products": ["string"],
  "services": ["string"],
  "pricing": {},
  "website": "string",
  "social_links": ["string"],
  "current_marketing": {},
  "current_sales": {},
  "goals": ["string"],
  "budget": {},
  "constraints": ["string"],
  "additional_notes": "string"
}
```

### Обязательные поля

- `project_name`
- `industry`
- `business_description`

### Quality Gate

Если отсутствуют `industry` или `project_name` → `BRIEF FAILED`.

## 4. normalized_brief.json

После нормализации. Убирает мусор, приводит к единому виду.

Пример: `"Фотостудия"`, `"Фото студия"`, `"photo studio"` → `"photography_studio"`

## 5. final_data.json

Главный файл системы. Содержит результаты всех 27 блоков Intelligence Layer.

### Структура

```json
{
  "schema_version": "4.0",
  "project_id": "string",
  "market_analysis": {},
  "business_diagnosis": {},
  "competitors": {},
  "platform": {},
  "portfolio_owner": {},
  "product_system": {},
  "flagship_product": {},
  "product_ladder": {},
  "lead_magnets": {},
  "audience": {},
  "avatars": {},
  "psychotypes": {},
  "pains": {},
  "triggers": {},
  "offers": {},
  "funnels": {},
  "advertising": {},
  "content_plan": {},
  "reels": {},
  "blog_articles": {},
  "posts": {},
  "visual_briefs": {},
  "sales_scripts": {},
  "kpi": {},
  "first_7_days": {},
  "launch_plan": {},
  "quality_report": {}
}
```

### Запрещено

Пустые объекты `{}`. Если блок пуст → `FAILED`.

## 6. Market Analysis Schema

```json
{
  "market_overview": "string",
  "market_size": "string",
  "seasonality": ["string"],
  "buying_triggers": ["string"],
  "buying_barriers": ["string"],
  "growth_opportunities": ["string"],
  "channels": ["string"],
  "risks": ["string"]
}
```

## 7. Business Diagnosis Schema

```json
{
  "constraints": ["string"],
  "quick_wins": ["string"],
  "growth_barriers": ["string"],
  "focus_areas": ["string"]
}
```

Минимум: 5 проблем, 5 быстрых улучшений.

## 8. Competitor Schema

Минимум 10 конкурентов.

```json
{
  "competitors": [
    {
      "name": "string",
      "offer": "string",
      "pricing": "string",
      "channels": ["string"],
      "strengths": ["string"],
      "weaknesses": ["string"],
      "lead_magnets": ["string"]
    }
  ],
  "advantages": ["string"],
  "gaps": ["string"]
}
```

Запрещено: `"нет информации"`, `"не найдено"`, `"ручная проверка"`.

Если данных нет: `{"status": "insufficient_data", "assumption": ""}`.

## 9. Avatar Schema

Минимум 5 аватаров.

```json
{
  "avatars": [
    {
      "avatar_id": "string",
      "name": "string",
      "age": "number",
      "occupation": "string",
      "income": "string",
      "interests": ["string"],
      "goals": ["string"],
      "fears": ["string"],
      "pains": ["string"],
      "buying_motivation": ["string"],
      "trust_triggers": ["string"],
      "channels": ["string"]
    }
  ]
}
```

Обязательные поля: `name`, `income`, `goals`, `fears`.

Проверка: `avatar_similarity_score < 70%`.

## 10. Pain Schema

Минимум 10 болей на аватара.

```json
{
  "pain_id": "string",
  "avatar_id": "string",
  "pain": "string",
  "severity": "string",
  "emotion": "string",
  "consequence": "string",
  "solution": "string",
  "offer": "string",
  "cta": "string",
  "metric": "string"
}
```

Проверка: каждая боль обязана иметь `solution`, `offer`, `cta`.

## 11. Offer Schema

```json
{
  "offer_id": "string",
  "avatar_id": "string",
  "pain_id": "string",
  "headline": "string",
  "value": "string",
  "cta": "string"
}
```

Проверка: `pain_id` → `offer_id` обязательная связь. Оффер должен закрывать конкретную боль.

## 12. Funnel Schema

```json
{
  "stage": "string",
  "client_state": "string",
  "content": "string",
  "cta": "string",
  "kpi": "string",
  "next_step": "string"
}
```

Минимум: 5 этапов. Каждый этап обязан вести к следующему.

## 13. Advertising Schema

```json
{
  "platform": "string",
  "audience": "string",
  "creative": "string",
  "offer": "string",
  "budget": "string",
  "test_duration": "string",
  "kpi": "string",
  "success_threshold": "string",
  "stop_threshold": "string",
  "scale_threshold": "string"
}
```

Запрещено: бюджет 5000+ на первом запуске. Всегда: тест → анализ → масштабирование.

## 14. Content Plan Schema

Минимум 30 дней.

```json
{
  "day": 1,
  "avatar_id": "string",
  "pain_id": "string",
  "offer_id": "string",
  "platform": "string",
  "format": "string",
  "cta": "string",
  "kpi": "string"
}
```

Проверка: 30 уникальных дней, нет контента без цели.

## 15. Reels Schema

```json
{
  "archetype": "string",
  "hook": "string",
  "problem": "string",
  "insight": "string",
  "proof": "string",
  "frame_1": "string",
  "frame_2": "string",
  "frame_3": "string",
  "frame_4": "string",
  "voiceover": "string",
  "on_screen_text": "string",
  "cta": "string"
}
```

Проверка: нельзя пропускать кадры. Archetype rotation.

## 16. Sales Schema

```json
{
  "scenario": "string",
  "goal": "string",
  "message": "string",
  "next_step": "string"
}
```

Сценарии: первый ответ, ответ на цену, ответ на сомнения, дожим, повторное касание, запрос отзыва, повторная продажа.

## 17. KPI Schema

```json
{
  "action": "string",
  "metric": "string",
  "success_threshold": "string",
  "warning_threshold": "string",
  "fail_threshold": "string",
  "if_success": "string",
  "if_warning": "string",
  "if_fail": "string"
}
```

Обязательное правило: все KPI должны быть числовыми.

Запрещено: `"много"`, `"мало"`, `"хорошо"`, `"плохо"`, `"высокий CTR"`.

## 18. execution_view_model.json

Самый важный контракт. Получается из `final_data.json`.

### Структура

```json
{
  "schema_version": "4.0",
  "project": {
    "name": "string",
    "industry": "string",
    "goal": "string"
  },
  "today": {
    "day": 1,
    "phase": "string",
    "missions": []
  },
  "days": [],
  "missions": [],
  "content_tasks": [],
  "ads_tasks": [],
  "sales_tasks": [],
  "kpi_tasks": [],
  "gamification": {
    "xp": 0,
    "level": "string",
    "progress_percent": 0,
    "completed_tasks": 0,
    "total_tasks": 0
  }
}
```

## 19. Daily Task Schema

```json
{
  "day": 1,
  "title": "string",
  "objective": "string",
  "difficulty": "string",
  "estimated_time": "string",
  "steps": ["string"],
  "ready_text": "string",
  "cta": "string",
  "kpi": "string",
  "success_threshold": "string",
  "warning_threshold": "string",
  "fail_threshold": "string",
  "if_success": "string",
  "if_fail": "string"
}
```

Главное правило: каждая задача должна быть выполнима человеком без маркетолога.

## 20. Версионирование схем

Каждый контракт имеет поле `schema_version: "4.0"`. При несовместимости → `SCHEMA FAILED`.

## 21. Правила валидации контрактов

- Все поля используют Pydantic-модели
- Никаких `dict[str, Any]`
- Обязательные поля проверяются строго
- Типы данных проверяются (age — всегда `int`, не `"34"`)
- Пустые объекты в `final_data.json` → `FAILED`
