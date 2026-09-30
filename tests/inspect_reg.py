with open("index.html", "r", encoding="utf-8", errors="ignore") as f:
    c = f.read()

import re
matches = [m.start() for m in re.finditer(r'selectedRole\s*=', c)]
for pos in matches:
    print("--- Match at", pos, "---")
    print(c[pos-100:pos+300].encode('ascii', errors='replace').decode())
