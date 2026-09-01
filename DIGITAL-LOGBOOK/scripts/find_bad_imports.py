import glob, re
bad=[]
for p in glob.glob('**/*.py', recursive=True):
    try:
        with open(p, 'r', encoding='utf-8', errors='replace') as f:
            for i,l in enumerate(f, start=1):
                if re.search(r"\bfrom\b.*\bfrom\b", l) or re.search(r"\bimport\b.*\bfrom\b", l) or 'reversefrom' in l:
                    bad.append((p,i,l.rstrip()))
    except Exception:
        pass
print(len(bad))
for p,i,l in bad:
    print(p+':'+str(i)+': '+l)
