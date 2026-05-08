import re, pathlib

js_dir = pathlib.Path('.venv/Lib/site-packages/streamlit/static/static/js')

for f in sorted(js_dir.glob('*.js'), key=lambda x: -x.stat().st_size)[:4]:
    js = f.read_text(encoding='utf-8', errors='ignore')
    found = []
    for m in re.finditer(r'data-baseweb', js):
        ctx = js[max(0, m.start()-40):m.start()+150]
        if 'select' in ctx.lower():
            found.append(repr(ctx[:180]))
            if len(found) >= 3:
                break
    if found:
        print(f'\n=== {f.name} ===')
        for h in found:
            print(f'  {h}')
