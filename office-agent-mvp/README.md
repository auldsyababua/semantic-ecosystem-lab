# Office Assistant MVP

A Windows-only desktop application that uses LLM (GPT-4) to automate Microsoft Office tasks through a simple chat interface.

## Features

- **Chat Interface**: Interactive Tkinter GUI with persistent chat history
- **Four Office Automation Actions**:
  1. **Generate PowerPoint**: Create presentations from natural language prompts
  2. **Draft Word Report**: Generate formatted Word documents
  3. **Summarize Excel**: Get plain-text summaries of data
  4. **Generate Excel File**: Create Excel spreadsheets from descriptions

## Requirements

- **Operating System**: Windows 10/11
- **Python**: 3.8 or higher
- **Microsoft Office**: Excel, Word, and PowerPoint installed
- **OpenAI API Key**: Required for LLM functionality

## Installation

### 1. Clone or Download

Place the `office-agent-mvp` folder on your Windows machine.

### 2. Install Python Dependencies

Open Command Prompt or PowerShell in the `office-agent-mvp` directory:

```bash
pip install -r requirements.txt
```

This installs:
- `openai` - OpenAI Python SDK
- `pywin32` - Windows COM automation for Office
- `pyinstaller` - For packaging to .exe

### 3. Configure OpenAI API Key

Create a `.env` file in the `office-agent-mvp` directory:

```
OPENAI_API_KEY=your-api-key-here
```

Or set it as an environment variable:

```bash
set OPENAI_API_KEY=your-api-key-here
```

## Running the Application

### From Source

Navigate to the project directory and run:

```bash
python -m app.main
```

The application window will open with:
- Chat history display
- Input box for messages
- Send button
- Four action buttons for Office automation

## Using the Application

### General Chat

1. Type your message in the input box
2. Click "Send" or press Enter
3. The LLM will respond in the chat history

### Office Actions

1. Type your prompt in the input box (e.g., "Create a presentation about AI trends")
2. Click one of the four action buttons:
   - **Generate PowerPoint**: Creates a .pptx with slides
   - **Draft Word Report**: Creates a formatted .docx document
   - **Summarize Excel**: Returns a text summary (no file created)
   - **Generate Excel File**: Creates a .xlsx with data
3. The Office application will open visibly with your generated content

### Example Prompts

**Generate PowerPoint**:
```
Create a 5-slide presentation on renewable energy sources
```

**Draft Word Report**:
```
Write a quarterly sales report for Q4 2024
```

**Summarize Excel**:
```
Summarize the key metrics for a sales dashboard with revenue, units sold, and growth rate
```

**Generate Excel File**:
```
Create a monthly budget tracker with categories: Rent, Food, Transport, Entertainment, and Savings
```

## Packaging as .exe

To create a standalone executable:

```bash
pyinstaller --onefile --windowed app/main.py -n OfficeAssistant
```

The `.exe` will be created in the `dist` folder.

**Notes**:
- The `--windowed` flag prevents a console window from appearing
- The `--onefile` flag bundles everything into a single executable
- The resulting .exe can run on any Windows machine without Python installed
- Microsoft Office must still be installed on the target machine
- You'll need to set the `OPENAI_API_KEY` environment variable on the target machine

## Architecture

```
office-agent-mvp/
├── app/
│   ├── __init__.py          # Package marker
│   ├── config.py            # Configuration and API key loading
│   ├── llm_client.py        # OpenAI API wrapper
│   ├── office_actions.py    # Four Office automation functions
│   ├── gui.py               # Tkinter GUI implementation
│   └── main.py              # Application entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Technical Details

### LLM Configuration

- **Model**: gpt-4.1-mini
- **Temperature**: 0.3 (for consistent, focused outputs)
- **Format**: Standard chat completions API

### Office Automation

All Office applications are controlled via COM automation using `win32com.client`:
- Applications launch visibly
- Files remain open after creation (not saved automatically)
- User has full control to edit, save, or discard

### Error Handling

- API errors display in error dialogs
- Failed operations show descriptive error messages
- Application remains responsive during long operations (background threads)

## Troubleshooting

**"OPENAI_API_KEY not found"**:
- Ensure `.env` file exists in the project root, or
- Set the environment variable system-wide

**"COM Error" or Office application issues**:
- Verify Microsoft Office is installed and activated
- Try opening Office applications manually to ensure they work
- Restart the application

**PyInstaller .exe doesn't work**:
- Ensure the target machine has Microsoft Office installed
- Set `OPENAI_API_KEY` as a system environment variable
- Run from Command Prompt to see any error messages

## Limitations

- **Windows only** (requires pywin32 and Microsoft Office)
- **Single conversation context** (no conversation history saved between sessions)
- **No file saving** (Office apps open with content, user must save manually)
- **Requires active internet connection** for LLM API calls

## License

This is a minimal viable product (MVP) for demonstration purposes.
