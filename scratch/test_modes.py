import sys, os
sys.path.insert(0, os.path.abspath('.'))
import app

def test(name, text, mode, expected_valid):
    steps = app.run_html(text, mode=mode)
    last = steps[-1]
    actual_valid = (last['state'] == 'q_f' and last['valid'] is True)
    status = 'PASS' if actual_valid == expected_valid else 'FAIL'
    print(f"[{status}] {name} (mode={mode}) -> valid={actual_valid} (last action: {last['action'][:55]})")

test("User example in XML", "<div> <p> <b> text </b> </div>", "xml", False)
test("User example in HTML", "<div> <p> <b> text </b> </div>", "html", True)
test("Properly closed in XML", "<div> <p> <b> text </b> </p> </div>", "xml", True)
test("Void tag without slash in XML", "<root><br><item>text</item></root>", "xml", False)
test("Self-closing slash in XML", "<root><br/><item>text</item></root>", "xml", True)
test("HTML void and auto-close", "<div><p>text<br><p>next</div>", "html", True)
