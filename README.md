# Flexberry MarkItDown MCP Server

[![GitHub](https://img.shields.io/badge/GitHub-Flexberry%2Fflexberry--markitdown--mcp-blue)](https://github.com/Flexberry/flexberry-markitdown-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://img.shields.io/pypi/v/flexberry-markitdown-mcp)](https://pypi.org/project/flexberry-markitdown-mcp/)

MCP-сервер для двунаправленной конвертации документов:

- **Любой формат → Markdown** (через Microsoft MarkItDown)
- **Markdown → PDF** (через Playwright / headless Chromium — подход из vscode-markdown-pdf)

Использует:

- [Microsoft MarkItDown](https://github.com/microsoft/markitdown) — конвертация любых форматов в Markdown
- Подход [vscode-markdown-pdf](https://github.com/showzs/vscode-markdown-pdf) — генерация PDF через headless Chromium

## Установка — одна команда

```bash
pip install flexberry-markitdown-mcp
```

Всё! При первом вызове `convert_to_pdf` Chromium скачается автоматически (как в vscode-markdown-pdf).

### Дополнительные опции

```bash
# Легковесный бэкенд без браузера (не поддерживает JS-рендеринг)
pip install flexberry-markitdown-mcp[weasyprint]

# Для разработки
pip install flexberry-markitdown-mcp[dev]
```

## Возможности

### Конвертация в Markdown (`convert_to_markdown`)

- 30+ форматов: PDF, DOCX, PPTX, XLSX, HTML, изображения (OCR), аудио (транскрипция), EPUB, ZIP...
- Поддержка кириллицы в именах файлов и содержимом
- Атомарная запись (временный файл + переименование)

### Конвертация в PDF (`convert_to_pdf`)

- **Playwright** (по умолчанию) — headless Chromium, как в vscode-markdown-pdf
  - Chromium скачивается автоматически при первом использовании
  - Поддержка JavaScript-рендеринга (Mermaid, PlantUML и т.д.)
  - Колонтитулы с номерами страниц
- **WeasyPrint** (опционально) — чистый Python, без браузера
- GitHub-стиль оформления (таблицы, код, блок-схемы)
- Подсветка синтаксиса через Pygments
- Настраиваемый формат страницы, поля, CSS

## Настройка MCP-клиента

### Claude Desktop / RooCode / Cursor

```json
{
  "mcpServers": {
    "flexberry-markitdown": {
      "command": "python3",
      "args": ["-m", "flexberry_markitdown_mcp.server"]
    }
  }
}
```

### Через uv

```json
{
  "mcpServers": {
    "flexberry-markitdown": {
      "command": "uv",
      "args": [
        "--directory", "/path/to/flexberry-markitdown-mcp",
        "run", "flexberry-markitdown-mcp"
      ]
    }
  }
}
```

## Инструменты

### `convert_to_markdown`

Конвертирует файл любого поддерживаемого формата в Markdown.

| Параметр     | Тип     | Обязательный | Описание                                     |
| ------------ | ------- | :----------: | -------------------------------------------- |
| `file_path`  | string  |      ✅      | Абсолютный путь к файлу                      |
| `output_path`| string  |      ❌      | Пользовательский путь вывода                 |
| `overwrite`  | boolean |      ❌      | Перезаписать существующий (по умолч.: false) |

### `convert_to_pdf`

Конвертирует Markdown-файл в PDF. Бэкенд по умолчанию — **Playwright** (как в vscode-markdown-pdf).

| Параметр                  | Тип     | Обязательный | Описание                                          |
| ------------------------- | ------- | :----------: | ------------------------------------------------- |
| `file_path`               | string  |      ✅      | Абсолютный путь к .md файлу                       |
| `output_path`             | string  |      ❌      | Пользовательский путь вывода PDF                  |
| `backend`                 | string  |      ❌      | `"playwright"` (по умолч.) или `"weasyprint"`     |
| `overwrite`               | boolean |      ❌      | Перезаписать существующий (по умолч.: false)      |
| `custom_css`              | string  |      ❌      | Дополнительный CSS                                |
| `include_default_styles`  | boolean |      ❌      | Включить встроенные стили (по умолч.: true)       |
| `format`                  | string  |      ❌      | Формат бумаги: A4, Letter и т.д. (по умолч.: A4)  |
| `margin_top`              | string  |      ❌      | Верхнее поле (по умолч.: 1.5cm)                   |
| `margin_bottom`           | string  |      ❌      | Нижнее поле (по умолч.: 1cm)                      |
| `margin_left`             | string  |      ❌      | Левое поле (по умолч.: 1cm)                       |
| `margin_right`            | string  |      ❌      | Правое поле (по умолч.: 1cm)                      |
| `print_background`        | boolean |      ❌      | Печатать фон (по умолч.: true)                    |
| `display_header_footer`   | boolean |      ❌      | Колонтитулы (по умолч.: true, Playwright)         |

### `get_supported_formats`

Список поддерживаемых форматов и доступные PDF-бэкенды.

### `check_file_exists`

Проверяет существование файла и возвращает информацию.

### `list_directory`

Показывает содержимое директории.

## Архитектура

```text
┌──────────────────────────────────────────────────────┐
│                   MCP Server (stdio)                  │
├──────────────────────────────────────────────────────┤
│                                                       │
│  convert_to_markdown          convert_to_pdf          │
│  ┌───────────────┐            ┌──────────────────┐   │
│  │  MarkItDown   │            │  markdown-it-py  │   │
│  │  (any→MD)     │            │  (MD→HTML)       │   │
│  └───────┬───────┘            └────────┬─────────┘   │
│          │                             │              │
│          ▼                             ▼              │
│  ┌───────────────┐            ┌──────────────────┐   │
│  │  Atomic write │            │  HTML template   │   │
│  │  (MD to disk) │            │  + GitHub CSS    │   │
│  └───────────────┘            └────────┬─────────┘   │
│                                        │              │
│                              ┌─────────┴──────────┐  │
│                              ▼                    ▼  │
│                     ┌──────────────┐  ┌────────────┐ │
│                     │  Playwright  │  │ WeasyPrint │ │
│                     │  (DEFAULT)   │  │ (optional) │ │
│                     │  Chromium    │  │ Pure Python│ │
│                     │  auto-d/l    │  │ No JS      │ │
│                     └──────┬───────┘  └─────┬──────┘ │
│                            ▼                ▼        │
│                     ┌─────────────────────────────┐  │
│                     │      PDF saved to disk      │  │
│                     └─────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

## Сравнение бэкендов PDF

| Характеристика    | Playwright (по умолч.)                 | WeasyPrint (опционально)        |
| ----------------- | -------------------------------------- | ------------------------------- |
| Установка         | Автоматически при `pip install`        | `pip install ...[weasyprint]`   |
| Chromium          | Автозагрузка при первом запуске        | Не нужен                        |
| JavaScript        | ✅ Полная поддержка                    | ❌                              |
| Mermaid/PlantUML  | ✅                                     | ❌                              |
| Колонтитулы       | ✅ Номера страниц                      | Через CSS @page                 |
| Рекомендация      | Все документы                          | Легковесный fallback            |

## Журналирование

Журналы сервера сохраняются в:

- Linux: `~/.flexberry-markitdown-mcp/server.log`
- Windows: `C:\Users\<user>\.flexberry-markitdown-mcp\server.log`

## Устранение неполадок

### Ошибка: "MarkItDown not installed"

```bash
pip install flexberry-markitdown-mcp
```

### Ошибка: "MCP module not found"

```bash
pip install flexberry-markitdown-mcp
```

### Проблемы с кириллицей в Windows

Убедитесь, что в терминале используется кодировка UTF-8. Сервер автоматически устанавливает UTF-8 для stdin/stdout/stderr.

### OCR не работает для изображений

Установите Tesseract:

- Windows: загрузите с <https://github.com/UB-Mannheim/tesseract/wiki>
- Linux: `sudo apt install tesseract-ocr` (Ubuntu/Debian)

Для русского языка установите языковой пакет:

- Windows: выберите русский язык во время установки
- Linux: `sudo apt install tesseract-ocr-rus`

### Транскрипция аудио не работает

MarkItDown использует Azure Speech Services для транскрипции. Убедитесь, что переменные среды настроены.

### Chromium не скачивается автоматически

```bash
playwright install chromium
```

## Разработка

### Запуск тестов

```bash
pip install -e ".[dev]"
pytest
```

### Структура проекта

```text
flexberry-markitdown-mcp/
├── src/
│   └── flexberry_markitdown_mcp/
│       ├── __init__.py
│       ├── converter.py     # MD → PDF конвертация
│       ├── server.py        # MCP сервер
│       └── styles.py        # CSS стили для PDF
├── tests/
│   └── test_converter.py
├── pyproject.toml
└── README.md
```

## Лицензия

MIT
