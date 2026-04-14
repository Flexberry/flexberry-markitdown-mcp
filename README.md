# Flexberry MarkItDown MCP Server

[![GitHub](https://img.shields.io/badge/GitHub-Flexberry%2Fflexberry--markitdown--mcp-blue)](https://github.com/Flexberry/flexberry-markitdown-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://img.shields.io/pypi/v/flexberry-markitdown-mcp)](https://pypi.org/project/flexberry-markitdown-mcp/)

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

### Вариант 1: Установка из PyPI (рекомендуется)

```bash
# Установка через pip
pip install flexberry-markitdown-mcp

# Установка с зависимостями для разработки
pip install flexberry-markitdown-mcp[dev]
```

### Вариант 2: Установка из исходного кода

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

### Вариант 3: Использование установочного скрипта

#### Linux/macOS:
```bash
chmod +x install.sh
./install.sh
```

#### Windows:
```cmd
install.bat
```

## Настройка RooCode

### Конфигурация для Windows

Добавьте в настройки RooCode (файл `mcp_settings.json` или через интерфейс):

```json
{
  "mcpServers": {
    "flexberry-markitdown": {
      "command": "python",
      "args": ["-m", "flexberry_markitdown_mcp.server"]
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
      "args": ["-m", "flexberry_markitdown_mcp.server"]
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

Если используется [uv](https://github.com/astral-sh/uv):

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
- `file_path` (обязательный) — путь к файлу для конвертации
- `output_path` (опциональный) — пользовательский путь для сохранения результата
- `overwrite` (опциональный, по умолчанию `false`) — перезаписать существующий файл

**Пример использования в RooCode:**
```
Convert file /home/user/documents/report.pdf to Markdown
```

### `get_supported_formats`

Возвращает список поддерживаемых форматов файлов.

### `check_file_exists`

Проверяет существование файла и возвращает информацию о нем.

## Примеры использования

### Конвертация PDF с кириллицей

```
Convert file C:\Documents\Report 2024.pdf to Markdown
```

Результат будет сохранен в `C:\Documents\Report 2024.md`

### Конвертация с перезаписью

```
Convert file /home/user/report.docx with overwrite existing
```

### Конвертация в указанное место

```
Convert presentation.pptx and save result to /tmp/output.md
```

## Обработка больших файлов

Сервер разработан для работы с файлами любого размера:

1. Файл конвертируется через MarkItDown
2. Результат сохраняется на диск рядом с исходным файлом
3. В контекст LLM возвращается только информация о пути и размере

Это позволяет работать с файлами, которые в 100 раз превышают лимит контекста LLM.

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
- Windows: загрузите с https://github.com/UB-Mannheim/tesseract/wiki
- Linux: `sudo apt install tesseract-ocr` (Ubuntu/Debian)

Для русского языка установите языковой пакет:
- Windows: выберите русский язык во время установки
- Linux: `sudo apt install tesseract-ocr-rus`

### Транскрипция аудио не работает

MarkItDown использует Azure Speech Services для транскрипции. Убедитесь, что переменные среды настроены.

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
├── uninstall.sh
├── uninstall.bat
└── roocode-config-examples.json
```

## Лицензия

MIT License

---

Разработано командой [Flexberry](https://github.com/Flexberry).
