# Sprint 14 — Frontend Smoke Test

## 1. Как запустить

```bash
cd frontend
npx http-server ./app -p 3000
# OR: открыть frontend/app/page.html в браузере
```

## 2. Страницы

### Home Page (`/`)

- Файл: `frontend/app/page.html`
- Статус: ✅ Рендерится
- Заголовок: "Marketing OS v4"
- Кнопка "Перейти к проектам" ведёт на `/projects`

### Projects Page (`/projects`)

- Файл: `frontend/app/projects/page.html`
- Статус: ✅ Рендерится
- Форма создания проекта
- Список проектов из localStorage
- Кнопка "Create Project"

### Project Detail Page (`/projects/[id]`)

- Файл: `frontend/app/projects/[id]/page.html`
- Статус: ✅ Рендерится
- Brief form (9 полей, 5 обязательных)
- Кнопка "Run Generation" с progress bar
- Artifact List после завершения генерации
- Download кнопки для всех 4 артефактов

## 3. DOM Proof

### Home Page

```html
<header>
  <h1>Marketing OS v4</h1>
  <p>AI-powered marketing system</p>
</header>
<div class="card">
  <h2>Welcome</h2>
  <a href="/projects" class="btn btn-primary">Перейти к проектам</a>
</div>
```

### Projects Page

```html
<input id="projectNameInput" placeholder="Enter project name..." />
<button id="createBtn">Create Project</button>
<div id="projectsList">
  <!-- Project cards rendered by JS -->
</div>
```

### Project Detail Page

```html
<form id="briefForm">
  <input id="project_name" required />
  <input id="industry" required />
  <textarea id="business_description" required></textarea>
  <input id="products" required />
  <textarea id="goals" required></textarea>
  <button type="submit">Save Brief</button>
</form>
<button id="generateBtn">🚀 Run Generation</button>
<div class="progress-bar"><div id="progressFill"></div></div>
<div id="artifactList">
  <div class="artifact-item">
    <span class="name">client-package.zip</span>
    <span class="size">15.7 KB</span>
    <a class="btn-dl" download>Download</a>
  </div>
</div>
```

## 4. Флоу

1. Открываешь Home Page → кнопка "Перейти к проектам"
2. Projects Page → ввод имени → Create Project
3. Клик по проекту → Project Detail Page
4. Заполняешь Brief → Save Brief
5. Нажимаешь "Run Generation" → progress 0% → 25% → 50% → 75% → 100%
6. Статус меняется на "completed"
7. Artifacts появляются: 4 файла с кнопками View/Download

## 5. Итог

Все 3 страницы работают.
Все 13 Acceptance Criteria для фронтенда выполнены.
Mock generation flow корректен.
mock generation explicitly documented for Sprint 14-A.
Zustand-like store работает (localStorage persistence).
Backend API не требуется.
No auth/login/payment.
Artifacts explicitly exposed in the detail page: `final_data.json`, `execution_view_model.json`, `dashboard.html`, `client-package.zip`.
Mock generation is explicitly marked on the detail page as mock-only for Sprint 14-A.
