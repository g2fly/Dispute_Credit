import difflib
import html
from typing import List, Tuple

import streamlit as st

st.set_page_config(page_title="3‑Way Diff Checker", layout="wide")

# ------------------ NEW TOP SECTION ------------------
st.markdown("""
**Instructions**

- **Video:** https://www.youtube.com/watch?v=ZwybFZpOPmY  
- **Download credit report** from **www.annualcreditreport.com**  
- **Upload into GPT** to get a **"JSON DIFF"** of each credit report  
- **Add each JSON into Diff Checker below**
""")
# -----------------------------------------------------

st.title("🔍 3‑Way Diff Checker")
st.write("Paste three texts below. The app will colorfully highlight differences and produce a tri‑diff summary.")

colA, colB, colC = st.columns(3)
with colA:
    text_a = st.text_area("Text A (baseline)", height=260, key="a")
with colB:
    text_b = st.text_area("Text B", height=260, key="b")
with colC:
    text_c = st.text_area("Text C", height=260, key="c")

mode = st.radio(
    "Diff granularity",
    ["line", "word", "char"],
    index=1,
    help="How to split the input before diffing. Word usually reads best."
)

def tokenize(text: str, mode: str):
    if mode == "line":
        return text.splitlines(keepends=True)
    elif mode == "word":
        import re
        return re.findall(r"\s+|\S+", text)
    else:  # char
        return list(text)

def color_span(txt: str, color: str, title: str = "") -> str:
    txt = html.escape(txt)
    style = {
        "add": "background-color: #d4f8d4;",
        "del": "background-color: #ffd6d6; text-decoration: line-through;",
        "chg": "background-color: #fff3bf;",
        "same": "color: #888;"
    }[color]
    return f'<span style="{style}" title="{html.escape(title)}">{txt}</span>'

def opcodes_to_html(a_tokens, b_tokens, opcodes):
    out = []
    for tag, i1, i2, j1, j2 in opcodes:
        a_chunk = "".join(a_tokens[i1:i2])
        b_chunk = "".join(b_tokens[j1:j2])

        if tag == "equal":
            out.append(color_span(b_chunk, "same"))
        elif tag == "replace":
            out.append(color_span(b_chunk, "chg", title=f"A: {a_chunk} → B: {b_chunk}"))
        elif tag == "delete":
            out.append(color_span(a_chunk, "del", title=f"Deleted from A: {a_chunk}"))
        elif tag == "insert":
            out.append(color_span(b_chunk, "add", title=f"Inserted in B: {b_chunk}"))
    return "".join(out)

def diff_pair(label_left: str, left: str, label_right: str, right: str, mode: str) -> str:
    a_toks = tokenize(left, mode)
    b_toks = tokenize(right, mode)
    sm = difflib.SequenceMatcher(None, a_toks, b_toks)
    html_body = opcodes_to_html(a_toks, b_toks, sm.get_opcodes())
    return f"""
<h3>{html.escape(label_left)} vs {html.escape(label_right)}</h3>
<div style="white-space: pre-wrap; font-family: monospace; line-height: 1.5;">
{html_body}
</div>
<hr/>
"""

def tri_summary(a: str, b: str, c: str) -> str:
    a_lines = a.splitlines()
    b_lines = b.splitlines()
    c_lines = c.splitlines()

    max_len = max(len(a_lines), len(b_lines), len(c_lines))
    rows = []
    for i in range(max_len):
        la = a_lines[i] if i < len(a_lines) else ""
        lb = b_lines[i] if i < len(b_lines) else ""
        lc = c_lines[i] if i < len(c_lines) else ""
        unique = len(set([la, lb, lc]))
        if unique > 1:
            rows.append((i + 1, la, lb, lc, unique))

    if not rows:
        return "<p><strong>No multi-way line-level differences detected.</strong></p>"

    table_rows = []
    for (ln, la, lb, lc, uniq) in rows:
        if uniq == 2:
            badge = '<span style="background:#4dabf7;color:#fff;padding:2px 6px;border-radius:6px;font-size:0.8em;">one differs</span>'
        else:
            badge = '<span style="background:#f03e3e;color:#fff;padding:2px 6px;border-radius:6px;font-size:0.8em;">all differ</span>'

        tr = f"""
<tr>
  <td style="color:#999;">{ln}</td>
  <td><pre style="white-space: pre-wrap; margin:0;">{html.escape(la)}</pre></td>
  <td><pre style="white-space: pre-wrap; margin:0;">{html.escape(lb)}</pre></td>
  <td><pre style="white-space: pre-wrap; margin:0;">{html.escape(lc)}</pre></td>
  <td>{badge}</td>
</tr>
"""
        table_rows.append(tr)

    return f"""
<table style="width:100%; border-collapse: collapse; table-layout: fixed;">
  <thead>
    <tr style="text-align:left; border-bottom:1px solid #ccc;">
      <th style="width:50px;">#</th>
      <th>Text A</th>
      <th>Text B</th>
      <th>Text C</th>
      <th style="width:120px;">Diff Type</th>
    </tr>
  </thead>
  <tbody>
    {''.join(table_rows)}
  </tbody>
</table>
"""

if st.button("Run diff", type="primary"):
    if not (text_a or text_b or text_c):
        st.warning("Please enter at least one non-empty text.")
        st.stop()

    sections = []
    sections.append("<h2>Pairwise Colored Diffs</h2>")
    sections.append(diff_pair("A", text_a, "B", text_b, mode))
    sections.append(diff_pair("A", text_a, "C", text_c, mode))
    sections.append(diff_pair("B", text_b, "C", text_c, mode))

    sections.append("<h2 style='margin-top:2rem;'>Tri‑Diff Summary (line‑level)</h2>")
    sections.append("<p>Shows lines where not all three match. Use this to quickly spot unique vs. all‑different lines.</p>")
    sections.append(tri_summary(text_a, text_b, text_c))

    final_html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>3‑Way Diff</title>
</head>
<body style="font-family: system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Oxygen, Ubuntu, Cantarell, Helvetica Neue, sans-serif; padding: 20px;">
  {''.join(sections)}
</body>
</html>
"""

    st.markdown(final_html, unsafe_allow_html=True)
    st.download_button(
        "Download HTML report",
        data=final_html,
        file_name="3_way_diff.html",
        mime="text/html"
    )
