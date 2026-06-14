"""
BLOCK 25 — План первых 7 дней
Убрать паралич клиента.
"""

VERSION = "1.0.0"

BLOCK_25_FIRST_7_DAYS_PROMPT = """
# BLOCK 25 — План первых 7 дней

## ЦЕЛЬ БЛОКА
Убрать паралич клиента.

## ВХОДНЫЕ ДАННЫЕ
Проектный контекст + результаты предыдущих блоков (только необходимые).

## ВЫХОДНЫЕ ДАННЫЕ (JSON)
Верни ТОЛЬКО JSON в формате:
{
  "status": "success",
  "data": { ... поля блока согласно схеме ... }
}

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


## PROJECT MEMORY
- Preserve context from the brief and prior blocks.
- Prefer source data over assumptions.
- If something is missing, fail closed with low confidence.

## TRACEABILITY
- Link every conclusion to a source field or assumption.
- Keep avatar -> pain -> offer -> CTA continuity whenever applicable.

## QUALITY RULES
- Confidence score для неподтверждённых данных
- Отсутствие повторений
- Отсутствие стоп-слов из global_stop_words.json
- Связность с другими блоками (avatar -> pain -> offer -> CTA)
"""
