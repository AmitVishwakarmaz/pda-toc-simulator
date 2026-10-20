import sys, os
sys.path.insert(0, os.path.abspath('.'))
import app

def test(name, text, mode, expected_valid):
    steps = app.run_html(text, mode=mode)
    last = steps[-1]
    actual_valid = (last['state'] == 'q_f' and last['valid'] is True)
    status = 'PASS' if actual_valid == expected_valid else 'FAIL'
    print(f"[{status}] {name} (mode={mode}) -> valid={actual_valid} (last action: {last['action'][:55]})")

test("User example unclosed p in XML", "<div> <p> <b> text </b> </div>", "xml", False)
test("HTML unclosed p before close div rejected in DPDA", "<div> <p> <b> text </b> </div>", "html", False)
test("Properly closed in XML", "<div> <p> <b> text </b> </p> </div>", "xml", True)
test("Void tag without slash in XML", "<root><br><item>text</item></root>", "xml", False)
test("Self-closing slash in XML", "<root><br/><item>text</item></root>", "xml", True)
test("HTML DPDA void and sibling self-loop with cleanup at $", "<p>text<br><p>next", "html", True)
test("Raw root text before tags in XML", "raw text <catalog><book>Guide</book></catalog>", "xml", False)
test("Raw root text after tags in XML", "<catalog><book>Guide</book></catalog> trailing text", "xml", False)
test("Only raw text in XML", "just raw text without elements", "xml", False)
test("Raw root text before tags in HTML", "raw text <div><p>Guide</p></div>", "html", True)
test("Raw root text after tags in HTML", "<div><p>Guide</p></div> trailing text", "html", True)
test("Valid text inside tag in XML", "<catalog><book>Guide</book></catalog>", "xml", True)
test("Multiple roots in XML", "<root1></root1><root2></root2>", "xml", False)
test("Multiple self-closing roots in XML", "<root1/><root2/>", "xml", False)
test("Multiple roots in HTML", "<p>first</p><p>second</p>", "html", True)
test("Single self-closing root in XML", "<root/>", "xml", True)
test("Single root with nested elements in XML", "<catalog><book><title>XML</title></book></catalog>", "xml", True)
test("Trailing tag after root closed in XML", "<root></root><extra>", "xml", False)

# HTML DPDA tests for end-marker ($) and intermediate cleanup state (q1)
s1 = app.run_html("<p>first<p>second", mode="html")
arrows1 = [x['arrow'] for x in s1]
assert "δ(q0, <p>, p) = (q0, p)" in arrows1, "Self-loop on q0 missing"
assert "δ(q0, $, p) = (q1, ε)" in arrows1, "Transition q0 -> q1 on $ missing"
assert "δ(q1, ε, Z0) = (qf, Z0)" in arrows1, "Transition q1 -> qf on ε missing"
print("[PASS] HTML DPDA sibling <p> self-loop and cleanup state q1 verified!")

s2 = app.run_html("<p>text</p>", mode="html")
arrows2 = [x['arrow'] for x in s2]
assert "δ(q0, $, Z0) = (qf, Z0)" in arrows2, "Direct q0 -> qf on $ missing"
print("[PASS] HTML DPDA direct accept d(q0, $, Z0) = (qf, Z0) verified!")

s3 = app.run_html("<div><p>text", mode="html")
assert s3[-1]['state'] == 'q_err' and s3[-1]['valid'] is False, "Unclosed div should be rejected"
print("[PASS] HTML DPDA unclosed div rejection verified!")
