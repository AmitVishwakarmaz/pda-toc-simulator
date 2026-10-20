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
