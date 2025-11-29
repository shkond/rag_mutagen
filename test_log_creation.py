from pathlib import Path
repo = Path('server.py').resolve().parent
log = repo/'mcp_server.log'
log.parent.mkdir(parents=True, exist_ok=True)
with open(log, 'a', encoding='utf-8') as f:
    f.write('test log creation from test script\n')
print('created:', log)
