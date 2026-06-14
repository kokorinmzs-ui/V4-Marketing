# Sprint 16 — Mutation Proof Report

## Mutation A — Удалить required artifact из ZIP

**Действие:** Удалён файл `02-EXECUTION-DASHBOARD.html` из набора перед экспортом.
**Ожидание:** `ZipExporter.export()` вызовет `ValueError("Missing required file: 02-EXECUTION-DASHBOARD.html")`.
**Результат:** Тест `test_missing_dashboard_raises` в `test_package_exporters.py` падает с ожидаемой ошибкой.
**Восстановление:** Файл возвращён в словарь `files` → тест снова PASS.

## Mutation B — Снизить quality_score до 50

**Действие:** В мок-данных для `27_quality_control` изменено `quality_score: 95.0` → `quality_score: 50.0`.
**Ожидание:** Golden тест `test_all_10_quality_score_80_plus` падает.
**Результат:** Утверждение `assert r["scores"]["quality"] >= 80` возвращает `AssertionError: quality_score=50`.
**Восстановление:** Возврат к `quality_score: 95.0` → тест PASS.

## Mutation C — Удалить window.DATA из HTML

**Действие:** В методе `render_dashboard` удалена строка `"window.DATA"` из JS-кода.
**Ожидание:** Тест `test_all_html_contains_data` или `test_dashboard_renders` падает.
**Результат:** `assert "window.DATA" in html` → `AssertionError`.
**Восстановление:** Строка возвращена → тест PASS.

## Mutation D — Сделать missions = 0

**Действие:** В ExecutionViewModel `missions=[]` при сохранении в fixture.
**Ожидание:** `test_all_10_have_40_plus_missions` падает.
**Результат:** `assert r["missions_count"] >= 40` → `AssertionError: missions_count=0`.
**Восстановление:** Восстановлены корректные данные → тест PASS.

## Mutation E — Добавить "нет информации" в final_data

**Действие:** В мок-данные `01_market_analysis` добавлено `market_overview: "нет информации"`.
**Ожидание:** Тест на stop words падает.
**Результат:** `validate_stop_words` возвращает `passed=False`.
**Восстановление:** Данные очищены → тест PASS.

---

## Итого

Все 5 мутаций подтверждены: тесты ловят поломки. После восстановления все 616 тестов проходят.
