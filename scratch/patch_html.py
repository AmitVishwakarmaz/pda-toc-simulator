import sys, re

with open('app.py', encoding='utf-8') as f:
    content = f.read()

# Find the block to replace: from the TOPIC C comment through the return steps line
start_marker = '# TOPIC C: HTML/XML Tag Validation'
end_marker = '\n\n\n# '   # the triple newline before TOPIC D comment

si = content.find(start_marker)
ei = content.find(end_marker, si)

if si == -1 or ei == -1:
    print("Markers not found!", si, ei); sys.exit(1)

# Keep the two blank lines before TOPIC C (already in content before si)
new_block = '''# TOPIC C: HTML/XML Tag Validation
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

# Void/self-closing tags: never need a closing tag, stack unchanged
# d(q0, <br>, X) = (q0, X)
VOID_TAGS = {
    \'br\', \'img\', \'hr\', \'input\', \'meta\', \'link\', \'area\', \'base\',
    \'col\', \'embed\', \'param\', \'source\', \'track\', \'wbr\',
}

# Auto-close tags: implicitly close at end or when sibling of same type opens
# d(q0, e, <p>) = (q0, e)
AUTO_CLOSE_TAGS = {
    \'p\', \'li\', \'dt\', \'dd\', \'td\', \'th\', \'tr\', \'colgroup\',
    \'thead\', \'tbody\', \'tfoot\', \'option\', \'optgroup\', \'caption\',
}

def run_html(html_input: str):
    """
    Simulates PDA for nested HTML/XML tag validation.
    Handles void tags (br, img...) and auto-close tags (p, li...).
    """
    token_re = re.compile(r\'(<\\/[^>]+>|<[^/>][^>]*>|<[^>]*/\\s*>|[^<]+)\')
    raw_tokens = token_re.findall(html_input.strip())
    tokens = [t.strip() for t in raw_tokens if t.strip()]

    steps = []
    stack = [\'Z0\']
    state = \'q0\'

    steps.append({
        "step": 1,
        "state": state,
        "input_remaining": \' \'.join(tokens),
        "stack": list(reversed(stack)),
        "action": "Initial configuration",
        "arrow": "-- (start)",
        "valid": None,
        "tag_event": "init",
        "tag_name": None,
    })

    error = None
    for i, token in enumerate(tokens):
        rem = \' \'.join(tokens[i+1:]) if i+1 < len(tokens) else \'(empty)\'

        if token.startswith(\'</\'):
            # -- Closing tag --
            tag_name = re.sub(r\'[<>/\\s]\', \'\', token).lower()

            # Pop any auto-close tags sitting on top (unless they match)
            while len(stack) > 1 and stack[-1].lower() in AUTO_CLOSE_TAGS and stack[-1].lower() != tag_name:
                popped = stack.pop()
                cur_rem = token + (\' \' + rem if rem != \'(empty)\' else \'\')
                steps.append({
                    "step": len(steps) + 1,
                    "state": state,
                    "input_remaining": cur_rem,
                    "stack": list(reversed(stack)),
                    "action": "AUTO-CLOSE <{}> (implicit) -> POP".format(popped),
                    "arrow": "q0 -> q0 (auto-close)",
                    "valid": None,
                    "tag_event": "auto_close",
                    "tag_name": popped,
                })

            if len(stack) <= 1:
                error = "Closing tag </{}>: stack is empty".format(tag_name)
                steps.append({
                    "step": len(steps) + 1,
                    "state": "q_err",
                    "input_remaining": rem,
                    "stack": list(reversed(stack)),
                    "action": "READ \'</{}>\': ERROR stack empty -- no open tag to match".format(tag_name),
                    "arrow": "q0 -> q_err",
                    "valid": False,
                    "tag_event": "error",
                    "tag_name": tag_name,
                })
                break

            top = stack[-1]
            if top.lower() == tag_name:
                stack.pop()
                steps.append({
                    "step": len(steps) + 1,
                    "state": state,
                    "input_remaining": rem,
                    "stack": list(reversed(stack)),
                    "action": "READ \'</{}>\' -> MATCH top \'{}\' -> POP".format(tag_name, top),
                    "arrow": "q0 -> q0",
                    "valid": None,
                    "tag_event": "close_match",
                    "tag_name": tag_name,
                })
            else:
                error = "Mismatch: expected </{}> but got </{}>".format(top, tag_name)
                steps.append({
                    "step": len(steps) + 1,
                    "state": "q_err",
                    "input_remaining": rem,
                    "stack": list(reversed(stack)),
                    "action": "READ \'</{}>\': MISMATCH -- top is \'{}\' -> ERROR".format(tag_name, top),
                    "arrow": "q0 -> q_err",
                    "valid": False,
                    "tag_event": "error",
                    "tag_name": tag_name,
                })
                break

        elif token.startswith(\'<\'):
            # -- Opening or self-closing tag --
            m = re.match(r\'<([^\\s/>]+)\', token)
            tag_name = m.group(1).lower() if m else token
            is_self_closing = token.rstrip().endswith(\'/>\')

            if is_self_closing or tag_name in VOID_TAGS:
                # Void: d(q0, <br>, X) = (q0, X) -- stack unchanged
                steps.append({
                    "step": len(steps) + 1,
                    "state": state,
                    "input_remaining": rem,
                    "stack": list(reversed(stack)),
                    "action": "READ \'{}\' -> VOID/self-closing (stack unchanged)".format(token[:30]),
                    "arrow": "q0 -> q0 (void)",
                    "valid": None,
                    "tag_event": "void",
                    "tag_name": tag_name,
                })
            else:
                # Auto-close sibling: if same auto-close tag already on top, pop it first
                if len(stack) > 1 and stack[-1].lower() == tag_name and tag_name in AUTO_CLOSE_TAGS:
                    stack.pop()
                    cur_rem = token + (\' \' + rem if rem != \'(empty)\' else \'\')
                    steps.append({
                        "step": len(steps) + 1,
                        "state": state,
                        "input_remaining": cur_rem,
                        "stack": list(reversed(stack)),
                        "action": "AUTO-CLOSE previous <{}> (sibling opened) -> POP".format(tag_name),
                        "arrow": "q0 -> q0 (auto-close)",
                        "valid": None,
                        "tag_event": "auto_close",
                        "tag_name": tag_name,
                    })

                stack.append(tag_name)
                steps.append({
                    "step": len(steps) + 1,
                    "state": state,
                    "input_remaining": rem,
                    "stack": list(reversed(stack)),
                    "action": "READ \'{}\' -> PUSH \'{}\'".format(token[:30], tag_name),
                    "arrow": "q0 -> q0",
                    "valid": None,
                    "tag_event": "open",
                    "tag_name": tag_name,
                })
        else:
            # -- Text content --
            short = token[:24] + (\'...\' if len(token) > 24 else \'\')
            steps.append({
                "step": len(steps) + 1,
                "state": state,
                "input_remaining": rem,
                "stack": list(reversed(stack)),
                "action": "READ text \'{}\' -> stack unchanged".format(short),
                "arrow": "q0 -> q0",
                "valid": None,
                "tag_event": "text",
                "tag_name": None,
            })

    if not error:
        # Auto-close any remaining auto-close tags before final check
        while len(stack) > 1 and stack[-1].lower() in AUTO_CLOSE_TAGS:
            popped = stack.pop()
            steps.append({
                "step": len(steps) + 1,
                "state": state,
                "input_remaining": "(empty)",
                "stack": list(reversed(stack)),
                "action": "AUTO-CLOSE <{}> at end of input -> POP".format(popped),
                "arrow": "q0 -> q0 (auto-close)",
                "valid": None,
                "tag_event": "auto_close",
                "tag_name": popped,
            })

        if stack == [\'Z0\']:
            state = \'q_f\'
            steps.append({
                "step": len(steps) + 1,
                "state": state,
                "input_remaining": "(empty)",
                "stack": [\'Z0\'],
                "action": "Input exhausted, stack = [Z0] -> ACCEPT (well-formed)",
                "arrow": "q0 -> q_f",
                "valid": True,
                "tag_event": "accept",
                "tag_name": None,
            })
        else:
            unclosed = [s for s in stack if s != \'Z0\']
            steps.append({
                "step": len(steps) + 1,
                "state": "q_err",
                "input_remaining": "(empty)",
                "stack": list(reversed(stack)),
                "action": "Input exhausted -- unclosed tags remain: {} -> REJECT".format(unclosed),
                "arrow": "q0 -> q_err",
                "valid": False,
                "tag_event": "error",
                "tag_name": unclosed[0] if unclosed else None,
            })

    return steps
'''

# Replace the old block
new_content = content[:si] + new_block + content[ei:]

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Done. Lines:", new_content.count('\n'))
