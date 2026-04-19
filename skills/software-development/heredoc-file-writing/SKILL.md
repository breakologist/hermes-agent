---
name: heredoc-file-writing
description: Write large Python files to disk when execute_code and write_file tools fail to include content. Uses terminal heredocs and chunked appending.
triggers:
  - execute_code returns "No code provided" despite including code
  - write_file returns 0 bytes written
  - need to write files larger than ~2KB
---

# Heredoc File Writing

## Problem
The `execute_code` and `write_file` tools sometimes fail to include the code/content parameter, resulting in empty files or "No code provided" errors. This is a known intermittent issue.

## Solution
Use the `terminal` tool with shell heredocs to write files reliably.

### Write initial file (overwrites)
```
terminal(command="cat > /path/to/file.py << 'EOF'\n#!/usr/bin/env python3\nprint('hello')\nEOF")
```

### Append to existing file
```
terminal(command="cat >> /path/to/file.py << 'EOF2'\ndef more(): pass\nEOF2")
```

### Verify after each chunk
```
terminal(command="python3 -c \"import py_compile; py_compile.compile('file.py', doraise=True); print('OK')\"")
terminal(command="wc -l file.py")
```

### Fix __main__ guard (curses apps)
```
terminal(command="python3 << 'FIX'\nwith open('file.py','r') as f: code=f.read()\ncode=code.replace('curses.wrapper(main)','if __name__ == \"__main__\":\\n    curses.wrapper(main)')\nwith open('file.py','w') as f: f.write(code)\nprint('Fixed')\nFIX")
```

## Rules
1. Use unique EOF markers per chunk if code contains literal EOF
2. Verify syntax with py_compile after every chunk
3. Check line count (wc -l) to confirm content arrived
4. Keep chunks under ~500 lines
5. Use quoted heredoc markers (<< 'MARKER') to prevent shell expansion
6. For Python-based writes, nest python3 -c inside terminal

## Chunked Building Pattern (for 500+ line files)

For large files (game engines, full applications), build in named chunks:

```bash
# Part 1: Overwrite with header + data
cat > /path/to/game.py << 'END1'
#!/usr/bin/env python3
import curses
# ... data structures ...
END1
echo "Part 1: $(wc -l < /path/to/game.py) lines"

# Part 2: Append classes
cat >> /path/to/game.py << 'END2'
class Player: ...
class Demon: ...
END2
echo "Part 2: $(wc -l < /path/to/game.py) lines"

# Part N: Final (rendering + main)
cat >> /path/to/game.py << 'ENDN'
def main(stdscr): ...
curses.wrapper(main)
ENDN

# Final verification
python3 -c "import py_compile; py_compile.compile('game.py', doraise=True); print('Syntax OK')"
echo "Complete: $(wc -l < game.py) lines"
```

## Curses App Fixes

### __main__ guard (critical for curses)
`curses.wrapper(main)` at module level breaks non-TTY imports. Always wrap:
```bash
python3 << 'FIX'
with open('game.py', 'r') as f: code = f.read()
code = code.replace('curses.wrapper(main)',
    'if __name__ == "__main__":\n    curses.wrapper(main)')
with open('game.py', 'w') as f: f.write(code)
FIX
```

### Import verification with curses mock
Since curses can't be imported outside a TTY, mock it to verify structure:
```python
import sys
sys.modules['curses'] = type(sys)('curses')
sys.modules['curses'].wrapper = lambda f: None
sys.modules['curses'].curs_set = lambda x: None
# ... add stubs for every curses function used ...
import my_game_module  # should import without errors
```

### __main__ guard detection
```bash
grep -n "curses.wrapper" game.py  # should be inside if __name__ guard
grep -n "if __name__" game.py     # verify guard exists
```

## Python-based targeted edits
For patching existing files (more reliable than sed for complex escaping):
```bash
python3 << 'PYEOF'
with open('file.py', 'r') as f: code = f.read()
code = code.replace('old_string', 'new_string')
with open('file.py', 'w') as f: f.write(code)
print('Patched')
PYEOF
```

## Pitfalls
- Shell escaping: use \\n for newlines in python -c strings
- Heredoc marker must be at start of line, no trailing whitespace
- If code contains the marker string, heredoc ends prematurely
- Large single heredocs may fail — split into chunks
- curses.wrapper() at module level blocks all non-TTY tool usage (execute_code, imports, etc.)
- Always verify with py_compile AND line count after each chunk