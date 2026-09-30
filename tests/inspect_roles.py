with open("index.html", "r", encoding="utf-8", errors="ignore") as f:
    c = f.read()

import re
idx = c.find("function switchView")
if idx != -1:
    print(c[idx:idx+800].encode('ascii', errors='replace').decode())

idx_setup = c.find("setupNav")
if idx_setup != -1:
    print(c[idx_setup:idx_setup+1000].encode('ascii', errors='replace').decode())
