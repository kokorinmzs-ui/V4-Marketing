"""Generate 27 block prompt files for Marketing OS v4."""
import os

base = r"c:\Users\Professional\Desktop\Marketing OS v4\ai_engine\prompts\blocks"
os.makedirs(base, exist_ok=True)

blocks = [
    ("01", "market_analysis", "Анализ ниши", "Понять рынок. Не компанию. Не продукт. Именно рынок."),
    ("02", "business_diagnosis", "Диагностика бизнеса", "Найти что мешает расти."),
    ("03", "competitors", "Анализ конкурентов", "Минимум 10 конкурентов. Понять почему покупают у них."),
    ("04", "platform", "Маркетинговая платформа", "Собрать основу бренда: позиционирование, УТП, RTB."),
    ("05", "owner_portrait", "Портрет собственника", "Понять как владелец усиливает продажи."),
    ("06", "product_system", "Продуктовая линейка", "Разложить бизнес на роли: Lead Magnet..Referral."),
    ("07", "flagship", "Флагманский продукт", "Выделить главный продукт бизнеса."),
    ("08", "product_ladder", "Раскладка продуктовой линейки", "Связать продукты: Lead Magnet -> Repeat."),
    ("09", "lead_magnets", "Стартовые лид-магниты", "Минимум 10 лид-магнитов."),
    ("10", "audience", "Анализ ЦА", "Разделить рынок на сегменты решений."),
    ("11", "avatars", "Аватары клиентов", "Минимум 5 аватаров. Создать людей, не аудиторию."),
    ("12", "psychotypes", "Психотипы", "Понять как человек принимает решение."),
    ("13", "pains", "Боли аватаров", "Минимум 10 болей на аватара (всего 50)."),
    ("14", "triggers", "Маркетинговые триггеры", "Минимум 10 триггеров на аватара."),
    ("15", "offers", "Офферы", "Минимум 10 офферов на аватара (всего 50)."),
    ("16", "funnels", "Автоворонка", "Построить путь клиента."),
    ("17", "advertising", "Рекламная стратегия", "Каналы: VK, Telegram, Яндекс."),
    ("18", "content_plan", "Контент-план", "30 дней действий."),
    ("19", "reels", "Reels", "Минимум 30 Reels с shot list."),
    ("20", "blog_articles", "Блог-статьи", "Минимум 30 статей."),
    ("21", "posts", "Посты для всех площадок", "Минимум 30 готовых постов."),
    ("22", "visual_briefs", "Визуальные ТЗ", "Для каждого материала: кадры, ракурс, свет."),
    ("23", "sales_scripts", "Скрипты продаж", "Первый ответ, цена, сомнения, дожим."),
    ("24", "kpi", "KPI Метрики", "Success/Warning/Fail числовые пороги."),
    ("25", "first_7_days", "План первых 7 дней", "Убрать паралич клиента."),
    ("26", "launch_plan", "Единый план запуска", "Собрать все блоки в систему."),
    ("27", "quality_control", "Контроль качества", "Финальная проверка всех блоков."),
]

TEMPLATE = '''"""
BLOCK {num} — {title}
{goal}
"""

VERSION = "1.0.0"

BLOCK_{num}_{slug_upper}_PROMPT = """
# BLOCK {num} — {title}

## ЦЕЛЬ БЛОКА
{goal}

## ВХОДНЫЕ ДАННЫЕ
Проектный контекст + результаты предыдущих блоков (только необходимые).

## ВЫХОДНЫЕ ДАННЫЕ (JSON)
Верни ТОЛЬКО JSON в формате:
{{
  "status": "success",
  "data": {{ ... поля блока согласно схеме ... }}
}}

## ЧТО ЗАПРЕЩЕНО
- Маркетинговая вода без доказательств
- Выдумывать факты и цифры
- Писать "нет информации", "ручная проверка", "не найдено"
- Анализировать данные других блоков
- Писать markdown или объяснения

## ЧТО ОБЯЗАТЕЛЬНО
- Только JSON на выходе
- Каждое поле заполнено или явно пустое ("")
- Конкретные, проверяемые утверждения
- Связь с аватарами/болями где применимо
- Числовые KPI где применимо

## JSON SCHEMA HINT
Следуй структуре, определённой в shared/schemas/blocks.py для этого блока.

## QUALITY RULES
- Confidence score для неподтверждённых данных
- Отсутствие повторений
- Отсутствие стоп-слов из global_stop_words.json
- Связность с другими блоками (avatar -> pain -> offer -> CTA)
"""
'''

init_imports = []
for num, slug, title, goal in blocks:
    slug_upper = slug.upper()
    name = f"block_{num}_{slug}_prompt.py"
    content = TEMPLATE.format(num=num, title=title, goal=goal, slug_upper=slug_upper)
    path = os.path.join(base, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"OK: {name}")
    init_imports.append(
        f"from ai_engine.prompts.blocks.block_{num}_{slug}_prompt import BLOCK_{num}_{slug_upper}_PROMPT"
    )

# Write __init__.py
init_path = os.path.join(base, "__init__.py")
with open(init_path, "w", encoding="utf-8") as f:
    for imp in init_imports:
        f.write(imp + "\n")
print(f"OK: __init__.py ({len(init_imports)} imports)")
print("DONE: all 27 block prompts created")