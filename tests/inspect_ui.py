import re

with open("index.html", "r", encoding="utf-8", errors="ignore") as f:
    c = f.read()

matches = re.findall(r'<button[^>]+id=["\']nav-btn-[^"\']+["\'][^>]*>', c)
for m in matches:
    print(m)

# Find switchView or navigation handling
print("\n--- Navigation Handler ---")
idx = c.find("nav-btn-")
if idx != -1:
    print(c[idx-50:idx+400])

idx_sw = c.find("switchView")
if idx_sw != -1:
    print(c[idx_sw:idx_sw+500])
else:
    print("switchView not found, searching data-view listeners...")
    idx_dv = c.find("data-view")
    if idx_dv != -1:
        print(c[idx_dv-100:idx_dv+300])
