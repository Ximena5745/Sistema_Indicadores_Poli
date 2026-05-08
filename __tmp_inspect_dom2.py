import re, pathlib

js = pathlib.Path('.venv/Lib/site-packages/streamlit/static/static/js/src.BnXM6qiK.js').read_text(encoding='utf-8', errors='ignore')

# All data-testid values
matches = re.findall(r'data-testid[`:"]+([a-zA-Z0-9_-]+)', js)
unique = sorted(set(matches))

border_ids = [m for m in unique if any(k in m.lower() for k in ('border','container','block','vertical','wrapper'))]
print('Border/container testids:')
for t in border_ids:
    print(' ', t)

# Find context around container with border
idx = js.find('stVerticalBlock')
print('\nContext around stVerticalBlock:')
print(repr(js[max(0,idx-200):idx+400]))
