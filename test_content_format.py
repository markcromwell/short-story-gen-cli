from ebooklib import epub

# Test simple HTML content
ch1 = epub.EpubHtml(title="Test1", file_name="test1.xhtml")
ch1.content = "<p>Simple content</p>"
body1 = ch1.get_body_content()
print(f"Simple HTML body: {body1!r}")
print(f"Simple HTML body length: {len(body1) if body1 else 0}")

# Test full XML/HTML document
ch2 = epub.EpubHtml(title="Test2", file_name="test2.xhtml")
ch2.content = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>T</title></head>
<body><p>Full doc</p></body>
</html>"""
body2 = ch2.get_body_content()
print(f"\nFull XML/HTML body: {body2!r}")
print(f"Full XML/HTML body length: {len(body2) if body2 else 0}")
