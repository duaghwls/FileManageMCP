# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Windows MCP (Model Context Protocol) server that provides file organization tools to LLMs. The server enables AI assistants to analyze directory structures, read files, and organize them according to Korean naming conventions (YYMMDD prefixes for files, NN_ prefixes for folders).

## Core Architecture

### Three-Layer Structure

1. **server.py** - FastMCP server entry point
   - Registers tools using `@mcp.tool()` decorators
   - Registers resources using `@mcp.resource()` decorators
   - Handles stdin/stdout MCP protocol communication
   - All tools are thin wrappers around functions in tools.py

2. **tools.py** - Business logic and file operations
   - Contains all tool implementation functions
   - Manages global `ToolConfig` with dry_run mode (default: enabled)
   - Split into three categories:
     - Configuration tools (set_dry_run, configure_workspace)
     - Analysis tools (list_directory, read_file_snippet, get_image_metadata, analyze_directory_structure)
     - Action tools (move_file, rename_file, create_folder, batch_rename_with_date)
   - All action tools respect dry_run mode

3. **utils.py** - Low-level utilities and safety checks
   - Path validation and sandboxing (`validate_path`, `is_path_in_sandbox`)
   - System folder protection (`is_forbidden_path`, `FORBIDDEN_PATHS`)
   - Encoding detection for Korean files (`read_file_with_encoding` - tries utf-8, cp949, euc-kr, latin-1)
   - Date formatting and folder naming validation
   - Directory depth checking (max 5 levels)

### Critical Design Patterns

**Dry Run Pattern**: All file modification tools check `config.dry_run` before actual operations. When true, they return simulation results instead of making changes.

**Sandbox Pattern**: `get_target_root()` returns `MCP_FILE_AGENT_ROOT` env var. If set, `validate_path()` ensures all operations stay within this root. Tools call `configure_workspace()` to set this at runtime.

**Path Validation Chain**: Every tool that touches files calls `validate_path()` which checks:
1. Forbidden system paths
2. Sandbox boundaries (if configured)
3. Path existence (if required)
4. Returns `PathValidationResult` with resolved Path or error

**Korean Encoding Support**: Files are read with multiple encoding attempts in `read_file_with_encoding()`. This is critical for Windows Korean environments where cp949/euc-kr are common.

## File Organization Rules

The server enforces two absolute rules:

1. **5-Level Rule**: Maximum directory depth is 5 levels from workspace root
2. **Number System**: Folders must use `NN_Name` format (00-99), where 99 is reserved for Archive

### Naming Conventions
- **Folders**: `NN_Name` format (e.g., `01_Project`, `02_Business`)
- **Files**: `YYMMDD_filename` format (e.g., `251202_report.docx`)
- **Versions**: Use `_v1.0` format (not "Final" or "최종")

## Development Commands

### Running the Server

```bash
# With uv (recommended)
uv run python server.py

# With standard Python
python server.py

# With virtual environment
.venv\Scripts\activate
python server.py
```

### Testing Tools

Since this is an MCP server, tools are tested through MCP clients (Cursor, Claude Desktop). There are no unit tests in the repository.

To test changes:
1. Modify the code
2. Restart the MCP server in your client
3. Use the client to invoke tools

## Important Implementation Notes

### When Adding New Tools

1. Add the implementation function to tools.py (not server.py)
2. Import it in server.py's import section
3. Create a wrapper function in server.py with `@mcp.tool()` decorator
4. Include comprehensive docstring (appears in client tool list)
5. If the tool modifies files, respect `config.dry_run`
6. Always use `validate_path()` for any path parameter

### Encoding Considerations

Windows Korean environments may use cp949 or euc-kr encoding. The `read_file_with_encoding()` function in utils.py handles this by trying multiple encodings in order: utf-8, utf-8-sig, cp949, euc-kr, latin-1. Never read files directly with `open()` - always use this utility function.

### Path Handling

Always work with `pathlib.Path` objects, not strings. Convert incoming string paths immediately with `Path(path).resolve()`. Use `validate_path()` before any file operations to ensure:
- The path is not in forbidden system folders
- The path is within the configured workspace (if set)
- The path exists (if required)

### Error Messages

All error messages follow the format `[ERROR] message` for consistency. Success messages use `[OK]`, warnings use `[WARNING]`, and dry-run simulations use `[DRY RUN]`. This formatting is expected by LLM clients parsing the results.

## MCP Resources

The server exposes two resources:

- `organization://rules` - Returns the file organization rules document
- `organization://workflow` - Returns the recommended workflow guide

These are read-only text resources that clients can fetch to understand the organization system.

## Common Pitfalls

1. **Don't bypass dry_run checks**: New action tools must respect `config.dry_run`
2. **Don't use open() directly**: Use `read_file_with_encoding()` for text files
3. **Don't skip path validation**: Always call `validate_path()` first
4. **Don't hardcode max_depth**: Use `config.max_depth` instead
5. **Don't modify server.py tool implementations**: Business logic belongs in tools.py

## Configuration

The server can be configured via:

1. **Environment variables**:
   - `MCP_FILE_AGENT_ROOT` - Workspace root path (sandboxing)

2. **Runtime configuration** (via tools):
   - `tool_set_dry_run(false)` - Disable safe mode
   - `tool_configure_workspace(path)` - Set workspace boundary

## Windows-Specific Notes

- The server is Windows-only (uses Windows-specific path handling and encoding)
- `sys.stderr` is wrapped with UTF-8 encoding to prevent crashes
- `stdout` is reserved for MCP protocol (never print to stdout)
- All logging/debugging must go to `stderr`
- File stat times: `st_ctime` is creation time on Windows (not Unix change time)
