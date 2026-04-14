# Flexberry MarkItDown MCP Server

[![GitHub](https://img.shields.io/badge/GitHub-Flexberry%2Fflexberry--markitdown--mcp-blue)](https://github.com/Flexberry/flexberry-markitdown-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

MCP сервер для конвертации файлов в Markdown с использованием библиотеки MarkItDown от Microsoft.

## Особенности

- 🔄 **Конвертация файлов** различных форматов в Markdown
- 📁 **Большие файлы** — результат сохраняется на диск, не загружается в контекст LLM
- 🌍 **Поддержка кириллицы** в документах и именах файлов
- 💻 **Кроссплатформенность** — Windows и Linux
- 🔧 **Интеграция с RooCode** через Model Context Protocol

## Поддерживаемые форматы

| Категория | Форматы |
|-----------|---------|
| Документы | PDF, DOCX, DOC, PPTX, PPT, XLSX, XLS |
| Веб | HTML, HTM, XML, URL |
| Данные | CSV, JSON |
| Текст | MD, RST, TXT |
| Изображения (OCR) | PNG, JPG, JPEG, GIF, BMP, TIFF, WEBP |
| Аудио (транскрипция) | MP3, WAV, M4A, OGG, FLAC |
| Архивы | ZIP |
| Электронные книги | EPUB |

> ⚠️ Для OCR изображений требуется установка Tesseract. Для транскрипции аудио требуется поддержка в системе.

## Установка

### Вариант 1: Установка через pip (рекомендуется)

```bash
# Клонируйте репозиторий
git clone https://github.com/Flexberry/flexberry-markitdown-mcp.git
cd flexberry-markitdown-mcp

# Создайте виртуальное окружение (опционально, но рекомендуется)
python -m venv .venv

# Активируйте виртуальное окружение
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Установите зависимости
pip install -e .
```

### Вариант 2: Установка зависимостей напрямую

```bash
pip install mcp markitdown
```

## Настройка RooCode

### Конфигурация для Windows

Добавьте в настройки RooCode (файл `mcp_settings.json` или через интерфейс):

```json
{
  "mcpServers": {
    "flexberry-markitdown": {
      "command": "python",
      "args": ["-m", "flexberry_markitdown_mcp.server"],
      "cwd": "C:\\path\\to\\flexberry-markitdown-mcp"
    }
  }
}
```

Или с виртуальным окружением:

```json
{
  "mcpServers": {
    "flexberry-markitdown": {
      "command": "C:\\path\\to\\flexberry-markitdown-mcp\\.venv\\Scripts\\python.exe",
      "args": ["-m", "flexberry_markitdown_mcp.server"],
      "cwd": "C:\\path\\to\\flexberry-markitdown-mcp"
    }
  }
}
```

### Конфигурация для Linux

```json
{
  "mcpServers": {
    "flexberry-markitdown": {
      "command": "python3",
      "args": ["-m", "flexberry_markitdown_mcp.server"],
      "cwd": "/home/user/flexberry-markitdown-mcp"
    }
  }
}
```

Или с виртуальным окружением:

```json
{
  "mcpServers": {
    "flexberry-markitdown": {
      "command": "/home/user/flexberry-markitdown-mcp/.venv/bin/python",
      "args": ["-m", "flexberry_markitdown_mcp.server"],
      "cwd": "/home/user/flexberry-markitdown-mcp"
    }
  }
}
```

### Универсальная конфигурация (через uv)

Если вы используете [uv](https://github.com/astral-sh/uv):

```json
{
  "mcpServers": {
    "flexberry-markitdown": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/flexberry-markitdown-mcp",
        "run",
        "flexberry-markitdown-mcp"
      ]
    }
  }
}
```

## Доступные инструменты

### `convert_to_markdown`

Конвертирует файл в Markdown и сохраняет результат рядом с исходным файлом.

**Параметры:**
- `file_path` (обязательно) — путь к файлу для конвертации
- `output_path` (опционально) — кастомный путь для сохранения результата
- `overwrite` (опционально, по умолчанию `false`) — перезаписать существующий файл

**Пример использования в RooCode:**
```
Конвертируй файл /home/user/documents/отчёт.pdf в Markdown
```

### `get_supported_formats`

Возвращает список поддерживаемых форматов файлов.

### `check_file_exists`

Проверяет существование файла и возвращает информацию о нём.

## Примеры использования

### Конвертация PDF с кириллицей

```
Конвертируй файл C:\Документы\Отчёт 2024.pdf в Markdown
```

Результат будет сохранён в `C:\Документы\Отчёт 2024.md`

### Конвертация с перезаписью

```
Конвертируй файл /home/user/report.docx с перезаписью существующего
```

### Конвертация в указанное место

```
Сконвертируй presentation.pptx и сохрани результат в /tmp/output.md
```

## Обработка больших файлов

Сервер специально разработан для работы с файлами любого размера:

1. Файл конвертируется через MarkItDown
2. Результат сохраняется на диск рядом с исходным файлом
3. В контекст LLM возвращается только информация о пути и размере

Это позволяет работать с файлами, которые в 100 раз превышают лимит контекста LLM.

## Логирование

Логи сервера сохраняются в:
- Linux: `~/.flexberry-markitdown-mcp/server.log`
- Windows: `C:\Users\<user>\.flexberry-markitdown-mcp\server.log`

## Решение проблем

### Ошибка: "MarkItDown not installed"

```bash
pip install markitdown
```

### Ошибка: "MCP module not found"

```bash
pip install mcp
```

### Проблемы с кириллицей в Windows

Убедитесь, что в терминале установлена кодировка UTF-8. Сервер автоматически настраивает UTF-8 для stdin/stdout/stderr.

### OCR не работает для изображений

Установите Tesseract:
- Windows: скачайте с https://github.com/UB-Mannheim/tesseract/wiki
- Linux: `sudo apt install tesseract-ocr` (Ubuntu/Debian)

Для русского языка установите языковой пакет:
- Windows: при установке выберите русский язык
- Linux: `sudo apt install tesseract-ocr-rus`

### Аудио транскрипция не работает

MarkItDown использует Azure Speech Services для транскрипции. Убедитесь, что настроены соответствующие переменные окружения.

## Разработка

### Запуск тестов

```bash
pip install -e ".[dev]"
pytest
```

### Структура проекта

```
flexberry-markitdown-mcp/
├── src/
│   └── flexberry_markitdown_mcp/
│       ├── __init__.py
│       └── server.py
├── pyproject.toml
├── README.md
├── install.sh
├── install.bat
└── roocode-config-examples.json
```

## Лицензия

MIT License

---

Разработано командой [Flexberry](https://github.com/Flexberry).
