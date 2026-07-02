import codecs, os
base = r'C:\Users\Administrator\.codex\skills\gaussdb-data-engineer'
files = ['SKILL.md']
ref_dir = os.path.join(base, 'references')
files += [os.path.join('references', f) for f in os.listdir(ref_dir)]
for fname in files:
    fpath = os.path.join(base, fname)
    try:
        c = codecs.open(fpath, 'r', 'utf-8-sig').read()
        codecs.open(fpath, 'w', 'cp936').write(c)
        print(f'OK: {fname}')
    except Exception as e:
        print(f'FAIL: {fname}: {e}')
