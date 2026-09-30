import shutil

# Source of truth for HTML structure is index-modular.html

with open('p:/coding.c/c programes/eventra-web/index-modular.html', 'r', encoding='utf-8') as f:
    html = f.read()

with open('p:/coding.c/c programes/eventra-web/styles.css', 'r', encoding='utf-8') as f:
    css = f.read()

with open('p:/coding.c/c programes/eventra-web/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Replace css link with inlined style
css_tag = '<style>\n' + css + '\n</style>'
html_combined = html.replace('<link rel="stylesheet" href="styles.css">', css_tag)

# Replace script tag with inlined script
js_tag = '<script>\n' + js + '\n</script>'
html_combined = html_combined.replace('<script src="app.js"></script>', js_tag)

with open('p:/coding.c/c programes/eventra-web/index.html', 'w', encoding='utf-8') as f:
    f.write(html_combined)

with open('p:/coding.c/c programes/eventra-web/eventra-standalone.html', 'w', encoding='utf-8') as f:
    f.write(html_combined)

print('Successfully created standalone index.html and eventra-standalone.html!')
print('Combined size in bytes:', len(html_combined.encode('utf-8')))
