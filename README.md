# Flexberry MarkItDown MCP Server

MCP-сервер для двунаправленной конвертации документов:
- **Любой формат → Markdown** (через Microsoft MarkItDown)
- **Markdown → PDF** (через Playwright / headless Chromium — как в vscode-markdown-pdf)

Основан на репозиториях:
- [flexberry-markitdown-mcp](https://github.com/Flexberry/flexberry-markitdown-mcp) — PDF → MD
- [vscode-markdown-pdf](https://github.com/showzs/vscode-markdown-pdf) — концепция MD → PDF

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
        "--directory", "/path/to/flexberry-markitdown-mcp-with-pdf",
        "run", "flexberry-markitdown-mcp"
      ]
    }
  }
}
```

## Инструменты

### `convert_to_markdown`
Конвертирует файл любого поддерживаемого формата в Markdown.

| Параметр | Тип | Обязательный | Описание |
|----------|-----|:---:|----------|
| `file_path` | string | ✅ | Абсолютный путь к файлу |
| `output_path` | string | ❌ | Пользовательский путь вывода |
| `overwrite` | boolean | ❌ | Перезаписать существующий (по умолчанию: false) |

### `convert_to_pdf`
Конвертирует Markdown-файл в PDF. Бэкенд по умолчанию — **Playwright** (как в vscode-markdown-pdf).

| Параметр | Тип | Обязательный | Описание |
|----------|-----|:---:|----------|
| `file_path` | string | ✅ | Абсолютный путь к .md файлу |
| `output_path` | string | ❌ | Пользовательский путь вывода PDF |
| `backend` | string | ❌ | `"playwright"` (по умолч.) или `"weasyprint"` |
| `overwrite` | boolean | ❌ | Перезаписать существующий (по умолчанию: false) |
| `custom_css` | string | ❌ | Дополнительный CSS |
| `include_default_styles` | boolean | ❌ | Включить встроенные стили (по умолчанию: true) |
| `format` | string | ❌ | Формат бумаги: A4, Letter и т.д. (по умолч.: A4) |
| `margin_top` | string | ❌ | Верхнее поле (по умолч.: 1.5cm) |
| `margin_bottom` | string | ❌ | Нижнее поле (по умолч.: 1cm) |
| `margin_left` | string | ❌ | Левое поле (по умолч.: 1cm) |
| `margin_right` | string | ❌ | Правое поле (по умолч.: 1cm) |
| `print_background` | boolean | ❌ | Печатать фон (по умолч.: true) |
| `display_header_footer` | boolean | ❌ | Колонтитулы (по умолч.: true, Playwright) |

### `get_supported_formats`
Список поддерживаемых форматов и доступные PDF-бэкенды.

### `check_file_exists`
Проверяет существование файла и возвращает информацию.

### `list_directory`
Показывает содержимое директории.

## Архитектура

```
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

| Характеристика | Playwright (по умолч.) | WeasyPrint (опционально) |
|---|---|---|
| Установка | Автоматически при `pip install` | `pip install ...[weasyprint]` |
| Chromium | Автозагрузка при первом запуске | Не нужен |
| JavaScript | ✅ Полная поддержка | ❌ |
| Mermaid/PlantUML | ✅ | ❌ |
| Колонтитулы | ✅ Номера страниц | Через CSS @page |
| Рекомендация | Все документы | Легковесный fallback |

## Лицензия

MIT
