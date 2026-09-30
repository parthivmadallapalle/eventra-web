with open("index.html", "r", encoding="utf-8", errors="ignore") as f:
    c = f.read()

idx = c.find("function setupRoleNavigation")
print(c[idx+600:idx+1800].encode('ascii', errors='replace').decode())
