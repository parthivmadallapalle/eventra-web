with open("server/server.js", "r", encoding="utf-8", errors="ignore") as f:
    c = f.read()

idx = c.find("app.post('/api/events'")
if idx == -1:
    idx = c.find("'/api/events'")
print("--- POST /api/events ---")
print(c[idx:idx+800].encode('ascii', errors='replace').decode())

idx_pay = c.find("app.post('/api/payments/create-order'")
print("--- POST /api/payments/create-order ---")
print(c[idx_pay:idx_pay+600].encode('ascii', errors='replace').decode())

idx_spon = c.find("app.post('/api/sponsorships'")
print("--- POST /api/sponsorships ---")
print(c[idx_spon:idx_spon+600].encode('ascii', errors='replace').decode())
