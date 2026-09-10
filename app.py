from flask import Flask, request, jsonify, render_template
import re
import os

app = Flask(__name__)

# ─────────────────────────────────────────────
# TOPIC A: Postfix Arithmetic Expression Eval
# ─────────────────────────────────────────────

def run_arithmetic(expression: str):
    """
    Simulates PDA evaluation of a postfix expression.
    Tokens are space-separated. The end-marker $ is optional.
    Returns list of step dicts.
    """
    tokens = expression.strip().split()
    if tokens and tokens[-1] == '$':
        tokens = tokens[:-1]

    steps = []
    stack = ['Z0']
    state = 'q0'

    full_tokens = tokens[:]

    # Initial config snapshot
    steps.append({
        "step": 1,
        "state": state,
        "input_remaining": ' '.join(full_tokens) + ' $',
        "stack": list(reversed(stack)),
        "action": "Initial configuration",
        "arrow": "-- (start)",
    })

    operators = {'+', '-', '*', 'x', 'X', '/', '%'}

    for i, token in enumerate(full_tokens):
        remaining_after = full_tokens[i+1:]
        rem_str = ' '.join(remaining_after) + ' $' if remaining_after else '$'

        def is_number(t):
            try:
                float(t)
                return True
            except ValueError:
                return False

        if is_number(token):
            stack.append(float(token))
            steps.append({
                "step": len(steps) + 1,
                "state": state,
                "input_remaining": rem_str,
                "stack": list(reversed(stack)),
                "action": "READ '{}' -> PUSH {}".format(token, token),
                "arrow": "q0 -> q0",
            })
        elif token in operators or token in ('+', '-'):
            if len(stack) < 3:
                raise ValueError("Not enough operands for operator '{}'".format(token))

            y1 = stack.pop()
            state = 'q_op'
            y1d = int(y1) if isinstance(y1, float) and y1 == int(y1) else round(y1, 4)
            steps.append({
                "step": len(steps) + 1,
                "state": state,
                "input_remaining": rem_str,
                "stack": list(reversed(stack)),
                "action": "READ '{}' -> POP {} (Y1 = top operand)".format(token, y1d),
                "arrow": "q0 -> q_op",
            })

            y2 = stack.pop()
            if token == '+':
                result = y2 + y1
            elif token == '-':
                result = y2 - y1
            elif token in ('*', 'x', 'X'):
                result = y2 * y1
            elif token in ('/', '%'):
                if y1 == 0:
                    raise ValueError("Division by zero")
                result = y2 / y1
            else:
                result = y2 + y1

            y2d = int(y2) if isinstance(y2, float) and y2 == int(y2) else round(y2, 4)
            rd = int(result) if isinstance(result, float) and result == int(result) else round(result, 4)
            stack.append(result)
            state = 'q0'
            steps.append({
                "step": len(steps) + 1,
                "state": state,
                "input_remaining": rem_str,
                "stack": list(reversed(stack)),
                "action": "POP {} (Y2) -> Compute {} {} {} = {} -> PUSH {}".format(y2d, y2d, token, y1d, rd, rd),
                "arrow": "q_op -> q0",
            })
        else:
            raise ValueError("Unrecognised token: '{}'".format(token))

    # End marker $
    if len(stack) == 2:
        final = stack[-1]
        fd = int(final) if isinstance(final, float) and final == int(final) else round(final, 4)
        state = 'q_f'
        steps.append({
            "step": len(steps) + 1,
            "state": state,
            "input_remaining": "(empty)",
            "stack": [str(fd), 'Z0'],
            "action": "READ '$' -> Final answer = {} -> ACCEPT".format(fd),
            "arrow": "q0 -> q_f",
        })
    else:
        raise ValueError("Expression is invalid -- stack does not have exactly one result")

    return steps


# ─────────────────────────────────────────────
# TOPIC B: Tower of Hanoi PDA
# ─────────────────────────────────────────────

def run_hanoi(n: int, source: str, dest: str, aux: str):
    """
    Simulates the PDA for Tower of Hanoi.
    Stack holds R() and M() frames; we expand top frame each step.
    Also tracks physical peg states for visualization.
    """
    if n < 1 or n > 7:
        raise ValueError("n must be between 1 and 7")

    steps = []
    moves_emitted = []
    state = 'q0'
    stack = ['Z0']

    # Physical peg state: dict peg -> list of disk nums (index 0 = bottom)
    pegs = {'A': [], 'B': [], 'C': []}
    pegs[source] = list(range(n, 0, -1))  # largest disk at bottom

    def peg_snap():
        return {'A': list(pegs['A']), 'B': list(pegs['B']), 'C': list(pegs['C'])}

    def snap(action, extra="", last_move=None):
        steps.append({
            "step": len(steps) + 1,
            "state": state,
            "stack": list(reversed(stack)),
            "action": action,
            "moves_so_far": list(moves_emitted),
            "note": extra,
            "peg_state": peg_snap(),
            "last_move": last_move,
            "total_disks": n,
            "source_peg": source,
            "dest_peg": dest,
            "aux_peg": aux,
        })

    snap("Initial configuration -- input: ({}, {}, {}, {})".format(n, source, dest, aux))

    stack.append("R({},{},{},{})".format(n, source, dest, aux))
    state = 'q1'
    snap("READ ({},{},{},{}) -> PUSH R({},{},{},{})".format(n, source, dest, aux, n, source, dest, aux),
         "d(q0,input,Z0) -> (q1, R.Z0)")

    MAX_STEPS = 500
    while len(stack) > 1 and len(steps) < MAX_STEPS:
        top = stack[-1]
        if top == 'Z0':
            break

        if top.startswith('R('):
            inner = top[2:-1]
            parts = inner.split(',')
            fn, fs, fd, fa = int(parts[0]), parts[1], parts[2], parts[3]

            if fn == 1:
                stack.pop()
                move_str = "Move disk 1: {} -> {}".format(fs, fd)
                moves_emitted.append(move_str)
                # Update physical pegs
                disk = pegs[fs].pop()
                pegs[fd].append(disk)
                snap("POP R(1,{},{},{}) -> EMIT: {}".format(fs, fd, fa, move_str),
                     "d(q1,e,R(1,S,D,A)) -> (q1,e)",
                     last_move={"disk": disk, "from": fs, "to": fd})
            else:
                stack.pop()
                stack.append("R({},{},{},{})".format(fn-1, fa, fd, fs))
                stack.append("M({},{},{})".format(fn, fs, fd))
                stack.append("R({},{},{},{})".format(fn-1, fs, fa, fd))
                snap(
                    "POP R({},{},{},{}) -> PUSH R({},{},{},{}), M({},{},{}), R({},{},{},{})".format(
                        fn, fs, fd, fa,
                        fn-1, fs, fa, fd,
                        fn, fs, fd,
                        fn-1, fa, fd, fs
                    ),
                    "d(q1,e,R(n,S,D,A)) -> push 3 sub-tasks"
                )

        elif top.startswith('M('):
            inner = top[2:-1]
            parts = inner.split(',')
            mn, ms, md = int(parts[0]), parts[1], parts[2]
            stack.pop()
            move_str = "Move disk {}: {} -> {}".format(mn, ms, md)
            moves_emitted.append(move_str)
            # Update physical pegs
            disk = pegs[ms].pop()
            pegs[md].append(disk)
            snap("POP M({},{},{}) -> EMIT: {}".format(mn, ms, md, move_str),
                 "d(q1,e,M(n,S,D)) -> (q1,e)",
                 last_move={"disk": disk, "from": ms, "to": md})
        else:
            break

    state = 'q_f'
    snap("Stack has only Z0 -- READ '$' -> ACCEPT. Total moves: {}".format(len(moves_emitted)),
         "d(q1,$,Z0) -> (q_f,Z0)")

    return steps


# ─────────────────────────────────────────────
# TOPIC C: HTML/XML Tag Validation
# ─────────────────────────────────────────────

# Void/self-closing tags: never need a closing tag, stack unchanged
# d(q0, <br>, X) = (q0, X)
VOID_TAGS = {
    'br', 'img', 'hr', 'input', 'meta', 'link', 'area', 'base',
    'col', 'embed', 'param', 'source', 'track', 'wbr',
}

# Auto-close tags: implicitly close at end or when sibling of same type opens
# d(q0, e, <p>) = (q0, e)
AUTO_CLOSE_TAGS = {
    'p', 'li', 'dt', 'dd', 'td', 'th', 'tr', 'colgroup',
    'thead', 'tbody', 'tfoot', 'option', 'optgroup', 'caption',
}

def run_html(html_input: str, mode: str = 'html'):
    """
    Simulates PDA for nested HTML/XML tag validation.
    mode='html': uses VOID_TAGS and AUTO_CLOSE_TAGS (lenient HTML rules).
    mode='xml':  strict -- every open tag must have a close tag;
                 only <tag/> self-closing syntax avoids pushing to stack.
    """
    is_xml = (mode == 'xml')
    token_re = re.compile(r'(<\/[^>]+>|<[^/>][^>]*>|<[^>]*/\s*>|[^<]+)')
    raw_tokens = token_re.findall(html_input.strip())
    tokens = [t.strip() for t in raw_tokens if t.strip()]

    steps = []
    stack = ['Z0']
    state = 'q0'

    steps.append({
        "step": 1,
        "state": state,
        "input_remaining": ' '.join(tokens),
        "stack": list(reversed(stack)),
        "action": "Initial configuration",
        "arrow": "-- (start)",
        "valid": None,
        "tag_event": "init",
        "tag_name": None,
    })

    error = None
    for i, token in enumerate(tokens):
        rem = ' '.join(tokens[i+1:]) if i+1 < len(tokens) else '(empty)'

        if token.startswith('</'):
            # -- Closing tag --
            tag_name = re.sub(r'[<>/\s]', '', token).lower()

            # Pop any auto-close tags sitting on top (HTML mode only)
            if not is_xml:
                while len(stack) > 1 and stack[-1].lower() in AUTO_CLOSE_TAGS and stack[-1].lower() != tag_name:
                    popped = stack.pop()
                    cur_rem = token + (' ' + rem if rem != '(empty)' else '')
                    steps.append({
                        "step": len(steps) + 1,
                        "state": state,
                        "input_remaining": cur_rem,
                        "stack": list(reversed(stack)),
                        "action": "AUTO-CLOSE <{}> -> POP".format(popped),
                        "arrow": "δ(q0, ε, <{}>) = (q0, ε)".format(popped),
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
                    "action": "READ '</{}>': ERROR stack empty -- no open tag to match".format(tag_name),
                    "arrow": "q0 -> q_err (no match on stack)",
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
                    "action": "READ '</{}>' -> MATCH top '{}' -> POP".format(tag_name, top),
                    "arrow": "δ(q0, </{}>, {}) = (q0, ε)".format(tag_name, top),
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
                    "action": "READ '</{}>': MISMATCH -- top is '{}' (expected </{}>) -> ERROR".format(tag_name, top, top),
                    "arrow": "q0 -> q_err (mismatch)",
                    "valid": False,
                    "tag_event": "error",
                    "tag_name": tag_name,
                })
                break

        elif token.startswith('<'):
            # -- Opening or self-closing tag --
            m = re.match(r'<([^\s/>]+)', token)
            tag_name = m.group(1).lower() if m else token
            is_self_closing = token.rstrip().endswith('/>')
            top = stack[-1]

            if is_self_closing or (not is_xml and tag_name in VOID_TAGS):
                # Void: stack unchanged (HTML void tags like <br> or self-closing <tag/>)
                kind = 'self-closing' if is_self_closing else 'void tag'
                rule_tag = tag_name if (not is_self_closing and tag_name == 'br') else (token[:15] if is_self_closing else tag_name)
                steps.append({
                    "step": len(steps) + 1,
                    "state": state,
                    "input_remaining": rem,
                    "stack": list(reversed(stack)),
                    "action": "READ '{}' -> {} (stack unchanged)".format(token[:30], kind),
                    "arrow": "δ(q0, <{}>, {}) = (q0, {})".format(rule_tag, top, top),
                    "valid": None,
                    "tag_event": "void",
                    "tag_name": tag_name,
                })
            else:
                # Auto-close sibling (HTML mode only):
                if not is_xml and len(stack) > 1 and stack[-1].lower() == tag_name and tag_name in AUTO_CLOSE_TAGS:
                    stack.pop()
                    cur_rem = token + (' ' + rem if rem != '(empty)' else '')
                    steps.append({
                        "step": len(steps) + 1,
                        "state": state,
                        "input_remaining": cur_rem,
                        "stack": list(reversed(stack)),
                        "action": "AUTO-CLOSE previous <{}> (sibling opened) -> POP".format(tag_name),
                        "arrow": "δ(q0, ε, <{}>) = (q0, ε)".format(tag_name),
                        "valid": None,
                        "tag_event": "auto_close",
                        "tag_name": tag_name,
                    })

                prev_top = stack[-1]
                stack.append(tag_name)
                steps.append({
                    "step": len(steps) + 1,
                    "state": state,
                    "input_remaining": rem,
                    "stack": list(reversed(stack)),
                    "action": "READ '{}' -> PUSH '{}'".format(token[:30], tag_name),
                    "arrow": "δ(q0, <{}>, {}) = (q0, {} {})".format(tag_name, prev_top, tag_name, prev_top),
                    "valid": None,
                    "tag_event": "open",
                    "tag_name": tag_name,
                })
        else:
            # -- Text content --
            top = stack[-1]
            short = token[:24] + ('...' if len(token) > 24 else '')
            steps.append({
                "step": len(steps) + 1,
                "state": state,
                "input_remaining": rem,
                "stack": list(reversed(stack)),
                "action": "READ text '{}' -> stack unchanged".format(short),
                "arrow": "δ(q0, text, {}) = (q0, {})".format(top, top),
                "valid": None,
                "tag_event": "text",
                "tag_name": None,
            })

    if not error:
        # Auto-close any remaining auto-close tags before final check (HTML mode only)
        if not is_xml:
            while len(stack) > 1 and stack[-1].lower() in AUTO_CLOSE_TAGS:
                popped = stack.pop()
                steps.append({
                    "step": len(steps) + 1,
                    "state": state,
                    "input_remaining": "(empty)",
                    "stack": list(reversed(stack)),
                    "action": "AUTO-CLOSE <{}> at end of input -> POP".format(popped),
                    "arrow": "δ(q0, ε, <{}>) = (q0, ε)".format(popped),
                    "valid": None,
                    "tag_event": "auto_close",
                    "tag_name": popped,
                })

        if stack == ['Z0']:
            state = 'q_f'
            steps.append({
                "step": len(steps) + 1,
                "state": state,
                "input_remaining": "(empty)",
                "stack": ['Z0'],
                "action": "Input exhausted, stack = [Z0] -> ACCEPT (well-formed)",
                "arrow": "δ(q0, ε, Z0) = (qf, Z0)",
                "valid": True,
                "tag_event": "accept",
                "tag_name": None,
            })
        else:
            unclosed = [s for s in stack if s != 'Z0']
            steps.append({
                "step": len(steps) + 1,
                "state": "q_err",
                "input_remaining": "(empty)",
                "stack": list(reversed(stack)),
                "action": "Input exhausted -- unclosed tags remain: {} -> REJECT".format(unclosed),
                "arrow": "q0 -> q_err (unclosed tags)",
                "valid": False,
                "tag_event": "error",
                "tag_name": unclosed[0] if unclosed else None,
            })

    return steps



# ─────────────────────────────────────────────
# TOPIC D: NLP Shift-Reduce Parse
# ─────────────────────────────────────────────

# Lexicon: word -> POS tag (lowercase key, display value)
LEXICON = {
    'the': 'Det', 'a': 'Det', 'an': 'Det',
    'dog': 'N', 'cat': 'N', 'bird': 'N', 'fish': 'N',
    'man': 'N', 'woman': 'N', 'child': 'N', 'boy': 'N', 'girl': 'N',
    'tree': 'N', 'car': 'N', 'book': 'N', 'ball': 'N',
    'chased': 'V', 'ate': 'V', 'saw': 'V', 'hit': 'V',
    'liked': 'V', 'found': 'V', 'heard': 'V', 'loves': 'V',
    'runs': 'V', 'run': 'V', 'catches': 'V', 'caught': 'V',
    'big': 'Adj', 'small': 'Adj', 'red': 'Adj', 'old': 'Adj', 'young': 'Adj',
    'quickly': 'Adv', 'slowly': 'Adv',
}

# Structural phrase-structure rules only (tuples of non-terminals)
STRUCT_RULES = [
    (('Det', 'Adj', 'N'), 'NP'),
    (('Det', 'N'),        'NP'),
    (('V',   'NP'),       'VP'),
    (('V',),              'VP'),
    (('Adv', 'VP'),       'VP'),
    (('NP',  'VP'),       'S'),
]

def try_struct_reduce(syms, remaining=None):
    """
    Match top of syms against structural rules (longest match first).
    Returns (lhs, rule_str, rlen) or (None, None, 0).
    remaining: list of words not yet shifted (used for shift-reduce conflict).
    """
    for rhs, lhs in sorted(STRUCT_RULES, key=lambda x: -len(x[0])):
        rlen = len(rhs)
        if len(syms) >= rlen and tuple(syms[-rlen:]) == rhs:
            # Shift-reduce conflict resolution:
            # If the only match is V->VP but there is still input that could
            # form an NP object, prefer shifting (delay the reduction).
            if rhs == ('V',) and lhs == 'VP' and remaining:
                next_pos = LEXICON.get(remaining[0]) if remaining else None
                if next_pos in ('Det', 'N', 'Adj'):
                    continue  # skip V->VP, prefer shift
            return lhs, ' '.join(rhs) + ' -> ' + lhs, rlen
    return None, None, 0

def run_nlp(sentence: str):
    """
    Shift-reduce PDA simulation for NLP parsing.
    Returns list of step dicts, each including a syntax tree snapshot.
    """
    words = sentence.strip().lower().split()
    if not words:
        raise ValueError("Sentence is empty")

    unknown = [w for w in words if w not in LEXICON]
    if unknown:
        raise ValueError(
            "Unknown word(s): {}. Supported words: {}".format(
                ', '.join(unknown), ', '.join(sorted(LEXICON.keys()))
            )
        )

    steps = []
    stack = ['Z0']
    tree_stack = []   # parallel to stack (excluding Z0); each item is a tree node dict
    state = 'q0'

    def make_node(label, children=None):
        return {"label": label, "children": list(children) if children else []}

    def node_to_dict(node):
        """Recursively serialise tree node."""
        return {
            "label": node["label"],
            "children": [node_to_dict(c) for c in node["children"]]
        }

    def snap(remaining, action, arrow):
        steps.append({
            "step": len(steps) + 1,
            "state": state,
            "input_remaining": ' '.join(remaining) if remaining else '(empty)',
            "stack": list(reversed(stack)),
            "action": action,
            "arrow": arrow,
            "tree": [node_to_dict(n) for n in tree_stack],
        })

    snap(words, "Initial configuration -- entering q1", "-- (start)")
    state = 'q1'

    remaining = list(words)
    MAX_STEPS = 400
    step_count = 0

    while step_count < MAX_STEPS:
        step_count += 1

        stack_syms = [s for s in stack if s != 'Z0']

        # Accept: stack = [S] and input empty
        if stack_syms == ['S'] and not remaining:
            state = 'q_f'
            snap([], "Stack = [S], input empty -- ACCEPT", "q1 -> q_f")
            break

        # Try structural reduce (pass remaining for conflict resolution)
        lhs, rule, rlen = try_struct_reduce(stack_syms, remaining)
        if lhs:
            # Pop from symbol stack and collect tree children
            for _ in range(rlen):
                stack.pop()
            children = [tree_stack.pop() for _ in range(rlen)][::-1]
            stack.append(lhs)
            tree_stack.append(make_node(lhs, children))
            snap(remaining, "REDUCE: {}".format(rule), "q1 -> q1 (reduce)")
            continue

        # Must shift
        if not remaining:
            snap([], "No more input -- cannot reduce or accept -- REJECT", "q1 -> q_err")
            break

        word = remaining.pop(0)
        pos = LEXICON[word]

        # SHIFT: push raw word onto both stacks
        stack.append(word)
        tree_stack.append(make_node(word))
        snap(remaining, "SHIFT '{}' -- PUSH '{}'".format(word, word), "q1 -> q1 (shift)")

        # Reduce: word -> POS tag (immediately)
        stack.pop()
        word_node = tree_stack.pop()
        stack.append(pos)
        tree_stack.append(make_node(pos, [word_node]))
        snap(remaining, "REDUCE: '{}' -> {}".format(word, pos), "q1 -> q1 (reduce)")

    return steps


# ─────────────────────────────────────────────
# Flask Routes
# ─────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/arithmetic', methods=['POST'])
def api_arithmetic():
    data = request.get_json()
    expr = data.get('expression', '').strip()
    if not expr:
        return jsonify({"error": "Expression is empty"}), 400
    try:
        steps = run_arithmetic(expr)
        return jsonify({"steps": steps})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/hanoi', methods=['POST'])
def api_hanoi():
    data = request.get_json()
    try:
        n = int(data.get('n', 3))
        source = data.get('source', 'A').strip().upper()
        dest   = data.get('dest',   'C').strip().upper()
        aux    = data.get('aux',    'B').strip().upper()
        if len({source, dest, aux}) != 3:
            return jsonify({"error": "Source, destination, and auxiliary pegs must all be different"}), 400
        steps = run_hanoi(n, source, dest, aux)
        return jsonify({"steps": steps})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/html', methods=['POST'])
def api_html():
    data = request.get_json()
    html = data.get('html', '').strip()
    mode = data.get('mode', 'html').strip().lower()
    if mode not in ('html', 'xml'):
        mode = 'html'
    if not html:
        return jsonify({"error": "HTML/XML input is empty"}), 400
    try:
        steps = run_html(html, mode=mode)
        return jsonify({"steps": steps, "mode": mode})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/nlp', methods=['POST'])
def api_nlp():
    data = request.get_json()
    sentence = data.get('sentence', '').strip()
    if not sentence:
        return jsonify({"error": "Sentence is empty"}), 400
    try:
        steps = run_nlp(sentence)
        return jsonify({"steps": steps})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
