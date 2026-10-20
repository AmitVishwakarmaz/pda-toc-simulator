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

def run_html(html_input: str, mode: str = 'xml'):
    """
    Simulates PDA for nested HTML/XML tag validation.
    mode='xml':  strict 3-state DPDA (q0, q1, qf):
                 - δ(q0, <T>, Z0) = (q1, T Z0) [open root tag only from start state q0]
                 - δ(q1, <T2>, T1) = (q1, T2 T1) [nested open tags only over existing tag T1 != Z0]
                 - δ(q1, text, T) = (q1, T) [consume text content only when T != Z0]
                 - δ(q1, </T>, T) = (q1, ε) [pop matching closing tags]
                 - δ(q1, ε, Z0) = (qf, Z0) [move to final state qf upon uncovering Z0]
                 All other combinations undefined (rejects raw root text and multiple roots).
    mode='html': uses VOID_TAGS and AUTO_CLOSE_TAGS (lenient HTML rules, start in q0).
    """
    is_xml = (mode == 'xml')
    token_re = re.compile(r'(<\/[^>]+>|<[^/>][^>]*>|<[^>]*/\s*>|[^<]+)')
    raw_tokens = token_re.findall(html_input.strip())
    tokens = [t.strip() for t in raw_tokens if t.strip()]

    steps = []
    stack = ['Z0']
    state = 'q0'

    init_rem = ' '.join(tokens) if is_xml else (' '.join(tokens) + (' $' if not (tokens and tokens[-1] == '$') else ''))
    steps.append({
        "step": 1,
        "state": state,
        "input_remaining": init_rem,
        "stack": list(reversed(stack)),
        "action": "Initial configuration",
        "arrow": "-- (start)",
        "valid": None,
        "tag_event": "init",
        "tag_name": None,
    })

    error = None

    if is_xml:
        # ─────────────────────────────────────────────────────────
        # XML Mode: Strict 3-state DPDA (q0, q1, qf)
        # ─────────────────────────────────────────────────────────
        for i, token in enumerate(tokens):
            rem = ' '.join(tokens[i+1:]) if i+1 < len(tokens) else '(empty)'

            # ── State q_f: Final state (root element already closed, Z0 uncovered) ──
            # No transitions are defined from q_f; any subsequent token halts and rejects.
            if state == 'q_f':
                if token.startswith('<') and not token.startswith('</'):
                    m = re.match(r'<([^\s/>]+)', token)
                    tag_name = m.group(1).lower() if m else token
                    error = "Multiple root elements not allowed in XML: read '<{}>' in final state qf".format(tag_name)
                    steps.append({
                        "step": len(steps) + 1,
                        "state": "q_err",
                        "input_remaining": rem,
                        "stack": list(reversed(stack)),
                        "action": "READ '{}': ERROR undefined transition in final state qf (multiple roots) -> REJECT".format(token[:30]),
                        "arrow": "δ(qf, <{}>, Z0) = undefined -> q_err".format(tag_name),
                        "valid": False,
                        "tag_event": "error",
                        "tag_name": tag_name,
                    })
                    break
                elif token.startswith('</'):
                    tag_name = re.sub(r'[<>/\s]', '', token).lower()
                    error = "Unexpected closing tag '</{}>' in final state qf".format(tag_name)
                    steps.append({
                        "step": len(steps) + 1,
                        "state": "q_err",
                        "input_remaining": rem,
                        "stack": list(reversed(stack)),
                        "action": "READ '</{}>': ERROR undefined transition in final state qf -> REJECT".format(tag_name),
                        "arrow": "δ(qf, </{}>, Z0) = undefined -> q_err".format(tag_name),
                        "valid": False,
                        "tag_event": "error",
                        "tag_name": tag_name,
                    })
                    break
                else:
                    short = token[:24] + ('...' if len(token) > 24 else '')
                    error = "Trailing text '{}' after root element in XML".format(short)
                    steps.append({
                        "step": len(steps) + 1,
                        "state": "q_err",
                        "input_remaining": rem,
                        "stack": list(reversed(stack)),
                        "action": "READ text '{}': ERROR undefined transition in final state qf (trailing text) -> REJECT".format(short),
                        "arrow": "δ(qf, text, Z0) = undefined -> q_err",
                        "valid": False,
                        "tag_event": "error",
                        "tag_name": None,
                    })
                    break

            # ── State q0: Start state (open root tag only) ──
            elif state == 'q0':
                if token.startswith('<') and not token.startswith('</'):
                    m = re.match(r'<([^\s/>]+)', token)
                    tag_name = m.group(1).lower() if m else token
                    is_self_closing = token.rstrip().endswith('/>')
                    rule_tag = token[:15] if is_self_closing else tag_name

                    if is_self_closing:
                        # Self-closing root tag: opens in q0 -> q1, immediately reveals Z0 -> qf
                        state = 'q1'
                        steps.append({
                            "step": len(steps) + 1,
                            "state": state,
                            "input_remaining": rem,
                            "stack": list(reversed(stack)),
                            "action": "READ '{}' -> self-closing root tag (q0 -> q1)".format(token[:30]),
                            "arrow": "δ(q0, <{}>, Z0) = (q1, Z0)".format(rule_tag),
                            "valid": None,
                            "tag_event": "void",
                            "tag_name": tag_name,
                        })
                        state = 'q_f'
                        is_end = (rem == '(empty)')
                        steps.append({
                            "step": len(steps) + 1,
                            "state": state,
                            "input_remaining": rem,
                            "stack": list(reversed(stack)),
                            "action": "Root element closed, uncover Z0 -> ACCEPT in final state qf" if is_end else "Root element closed, uncover Z0 -> move to final state qf",
                            "arrow": "δ(q1, ε, Z0) = (qf, Z0)",
                            "valid": True if is_end else None,
                            "tag_event": "accept" if is_end else "close_match",
                            "tag_name": None,
                        })
                    else:
                        # δ(q0, <T>, Z0) = (q1, T Z0): Open root tag only from start state q0
                        stack.append(tag_name)
                        state = 'q1'
                        steps.append({
                            "step": len(steps) + 1,
                            "state": state,
                            "input_remaining": rem,
                            "stack": list(reversed(stack)),
                            "action": "READ '{}' -> PUSH root '{}' (q0 -> q1)".format(token[:30], tag_name),
                            "arrow": "δ(q0, <{}>, Z0) = (q1, {} Z0)".format(tag_name, tag_name),
                            "valid": None,
                            "tag_event": "open",
                            "tag_name": tag_name,
                        })
                elif token.startswith('</'):
                    tag_name = re.sub(r'[<>/\s]', '', token).lower()
                    error = "Closing tag '</{}>' in start state q0: no open root tag".format(tag_name)
                    steps.append({
                        "step": len(steps) + 1,
                        "state": "q_err",
                        "input_remaining": rem,
                        "stack": list(reversed(stack)),
                        "action": "READ '</{}>': ERROR undefined transition in state q0 (no open root tag) -> REJECT".format(tag_name),
                        "arrow": "δ(q0, </{}>, Z0) = undefined -> q_err".format(tag_name),
                        "valid": False,
                        "tag_event": "error",
                        "tag_name": tag_name,
                    })
                    break
                else:
                    short = token[:24] + ('...' if len(token) > 24 else '')
                    error = "Raw root text '{}' in start state q0".format(short)
                    steps.append({
                        "step": len(steps) + 1,
                        "state": "q_err",
                        "input_remaining": rem,
                        "stack": list(reversed(stack)),
                        "action": "READ text '{}': ERROR undefined transition in state q0 (raw root text) -> REJECT".format(short),
                        "arrow": "δ(q0, text, Z0) = undefined -> q_err",
                        "valid": False,
                        "tag_event": "error",
                        "tag_name": None,
                    })
                    break

            # ── State q1: Active parsing state inside open root element ──
            elif state == 'q1':
                top = stack[-1]

                if token.startswith('</'):
                    # δ(q1, </T>, T) = (q1, ε): Pop matching closing tags
                    tag_name = re.sub(r'[<>/\s]', '', token).lower()
                    if top.lower() == tag_name:
                        stack.pop()
                        steps.append({
                            "step": len(steps) + 1,
                            "state": state,
                            "input_remaining": rem,
                            "stack": list(reversed(stack)),
                            "action": "READ '</{}>' -> MATCH top '{}' -> POP".format(tag_name, top),
                            "arrow": "δ(q1, </{}>, {}) = (q1, ε)".format(tag_name, top),
                            "valid": None,
                            "tag_event": "close_match",
                            "tag_name": tag_name,
                        })
                        # δ(q1, ε, Z0) = (qf, Z0): Move to final state qf upon uncovering Z0
                        if stack == ['Z0']:
                            state = 'q_f'
                            is_end = (rem == '(empty)')
                            steps.append({
                                "step": len(steps) + 1,
                                "state": state,
                                "input_remaining": rem,
                                "stack": ['Z0'],
                                "action": "Root element closed, uncover Z0 -> ACCEPT in final state qf" if is_end else "Root element closed, uncover Z0 -> move to final state qf",
                                "arrow": "δ(q1, ε, Z0) = (qf, Z0)",
                                "valid": True if is_end else None,
                                "tag_event": "accept" if is_end else "close_match",
                                "tag_name": None,
                            })
                    else:
                        error = "Mismatch: expected </{}> but got </{}>".format(top, tag_name)
                        steps.append({
                            "step": len(steps) + 1,
                            "state": "q_err",
                            "input_remaining": rem,
                            "stack": list(reversed(stack)),
                            "action": "READ '</{}>': MISMATCH -- top is '{}' (expected </{}>) -> ERROR".format(tag_name, top, top),
                            "arrow": "δ(q1, </{}>, {}) = undefined -> q_err".format(tag_name, top),
                            "valid": False,
                            "tag_event": "error",
                            "tag_name": tag_name,
                        })
                        break

                elif token.startswith('<'):
                    # δ(q1, <T2>, T1) = (q1, T2 T1): Allow nested opening tags only over T1 != Z0
                    m = re.match(r'<([^\s/>]+)', token)
                    tag_name = m.group(1).lower() if m else token
                    is_self_closing = token.rstrip().endswith('/>')
                    rule_tag = token[:15] if is_self_closing else tag_name

                    if is_self_closing:
                        steps.append({
                            "step": len(steps) + 1,
                            "state": state,
                            "input_remaining": rem,
                            "stack": list(reversed(stack)),
                            "action": "READ '{}' -> self-closing nested tag (stack unchanged)".format(token[:30]),
                            "arrow": "δ(q1, <{}>, {}) = (q1, {})".format(rule_tag, top, top),
                            "valid": None,
                            "tag_event": "void",
                            "tag_name": tag_name,
                        })
                    else:
                        stack.append(tag_name)
                        steps.append({
                            "step": len(steps) + 1,
                            "state": state,
                            "input_remaining": rem,
                            "stack": list(reversed(stack)),
                            "action": "READ '{}' -> PUSH nested '{}'".format(token[:30], tag_name),
                            "arrow": "δ(q1, <{}>, {}) = (q1, {} {})".format(tag_name, top, tag_name, top),
                            "valid": None,
                            "tag_event": "open",
                            "tag_name": tag_name,
                        })

                else:
                    # δ(q1, text, T) = (q1, T): Consume text content only when inside open element (T != Z0)
                    short = token[:24] + ('...' if len(token) > 24 else '')
                    steps.append({
                        "step": len(steps) + 1,
                        "state": state,
                        "input_remaining": rem,
                        "stack": list(reversed(stack)),
                        "action": "READ text '{}' -> stack unchanged".format(short),
                        "arrow": "δ(q1, text, {}) = (q1, {})".format(top, top),
                        "valid": None,
                        "tag_event": "text",
                        "tag_name": None,
                    })

        if not error:
            if state == 'q_f' and stack == ['Z0']:
                if steps[-1]['valid'] is not True:
                    steps.append({
                        "step": len(steps) + 1,
                        "state": "q_f",
                        "input_remaining": "(empty)",
                        "stack": ['Z0'],
                        "action": "Input exhausted, stack = [Z0] -> ACCEPT in final state qf (well-formed XML single root)",
                        "arrow": "δ(q1, ε, Z0) = (qf, Z0)",
                        "valid": True,
                        "tag_event": "accept",
                        "tag_name": None,
                    })
            elif stack != ['Z0']:
                unclosed = [s for s in stack if s != 'Z0']
                steps.append({
                    "step": len(steps) + 1,
                    "state": "q_err",
                    "input_remaining": "(empty)",
                    "stack": list(reversed(stack)),
                    "action": "Input exhausted -- unclosed tags remain: {} -> REJECT".format(unclosed),
                    "arrow": "δ(q1, ε, {}) = undefined -> q_err".format(stack[-1]),
                    "valid": False,
                    "tag_event": "error",
                    "tag_name": unclosed[0] if unclosed else None,
                })
            else:
                steps.append({
                    "step": len(steps) + 1,
                    "state": "q_err",
                    "input_remaining": "(empty)",
                    "stack": ['Z0'],
                    "action": "Input exhausted -- no root element found in XML -> REJECT",
                    "arrow": "δ(q0, ε, Z0) = undefined -> q_err",
                    "valid": False,
                    "tag_event": "error",
                    "tag_name": None,
                })

    else:
        # ─────────────────────────────────────────────────────────
        # HTML Mode: Deterministic DPDA (q0, q1, qf) with end-marker '$'
        # ─────────────────────────────────────────────────────────
        clean_tokens = [t for t in tokens if t != '$']

        for i, token in enumerate(clean_tokens):
            rem = (' '.join(clean_tokens[i+1:]) + ' $').strip() if i+1 < len(clean_tokens) else '$'

            if token.startswith('</'):
                tag_name = re.sub(r'[<>/\s]', '', token).lower()

                if len(stack) <= 1:
                    error = "Closing tag </{}>: stack is empty".format(tag_name)
                    steps.append({
                        "step": len(steps) + 1,
                        "state": "q_err",
                        "input_remaining": rem,
                        "stack": list(reversed(stack)),
                        "action": "READ '</{}>': ERROR stack empty -- no open tag to match".format(tag_name),
                        "arrow": "δ(q0, </{}>, Z0) = undefined -> q_err".format(tag_name),
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
                        "arrow": "δ(q0, </{}>, {}) = undefined -> q_err".format(tag_name, top),
                        "valid": False,
                        "tag_event": "error",
                        "tag_name": tag_name,
                    })
                    break

            elif token.startswith('<'):
                m = re.match(r'<([^\s/>]+)', token)
                tag_name = m.group(1).lower() if m else token
                is_self_closing = token.rstrip().endswith('/>')
                top = stack[-1]

                if is_self_closing or tag_name in VOID_TAGS:
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
                    # Self-Loop on q0: Replace any ε-transitions on <p> with <p>, p / p
                    if len(stack) > 1 and stack[-1].lower() == tag_name and tag_name in AUTO_CLOSE_TAGS:
                        steps.append({
                            "step": len(steps) + 1,
                            "state": state,
                            "input_remaining": rem,
                            "stack": list(reversed(stack)),
                            "action": "READ '{}' -> self-loop on q0 (stack: {} / {})".format(token[:30], tag_name, tag_name),
                            "arrow": "δ(q0, <{}>, {}) = (q0, {})".format(tag_name, tag_name, tag_name),
                            "valid": None,
                            "tag_event": "sibling_open",
                            "tag_name": tag_name,
                        })
                    else:
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

        # Process end-marker '$' for deterministic HTML DPDA
        if not error:
            top = stack[-1].lower() if len(stack) > 1 else 'Z0'

            # Transition from q0 to q1: Add a transition triggered by the end-marker that pops the unclosed paragraph: $, p / ε
            if len(stack) > 1 and top in AUTO_CLOSE_TAGS:
                popped = stack.pop()
                state = 'q1'
                steps.append({
                    "step": len(steps) + 1,
                    "state": state,
                    "input_remaining": "(empty)",
                    "stack": list(reversed(stack)),
                    "action": "READ '$' -> pop unclosed <{}> (q0 -> q1)".format(popped),
                    "arrow": "δ(q0, $, {}) = (q1, ε)".format(popped),
                    "valid": None,
                    "tag_event": "auto_close",
                    "tag_name": popped,
                })

                # In cleanup state q1, pop any additional unclosed auto-close tags
                while len(stack) > 1 and stack[-1].lower() in AUTO_CLOSE_TAGS:
                    popped = stack.pop()
                    steps.append({
                        "step": len(steps) + 1,
                        "state": state,
                        "input_remaining": "(empty)",
                        "stack": list(reversed(stack)),
                        "action": "In cleanup state q1: pop unclosed <{}>".format(popped),
                        "arrow": "δ(q1, ε, {}) = (q1, ε)".format(popped),
                        "valid": None,
                        "tag_event": "auto_close",
                        "tag_name": popped,
                    })

                # Transition from q1 to qf: In the new cleanup state q1, transition to the accepting final state qf without consuming more input once the stack is empty: ε, Z0 / Z0
                if stack == ['Z0']:
                    state = 'q_f'
                    steps.append({
                        "step": len(steps) + 1,
                        "state": state,
                        "input_remaining": "(empty)",
                        "stack": ['Z0'],
                        "action": "Stack = [Z0] in cleanup state q1 -> ACCEPT in final state qf",
                        "arrow": "δ(q1, ε, Z0) = (qf, Z0)",
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
                        "action": "In state q1: unclosed tag(s) remain: {} -> REJECT".format(unclosed),
                        "arrow": "δ(q1, ε, {}) = undefined -> q_err".format(stack[-1]),
                        "valid": False,
                        "tag_event": "error",
                        "tag_name": unclosed[0] if unclosed else None,
                    })

            # Transition from q0 to qf: Add a direct accepting transition for when no tags remain unclosed at the end: $, Z0 / Z0
            elif stack == ['Z0']:
                state = 'q_f'
                steps.append({
                    "step": len(steps) + 1,
                    "state": state,
                    "input_remaining": "(empty)",
                    "stack": ['Z0'],
                    "action": "READ '$', stack = [Z0] -> ACCEPT in final state qf (well-formed HTML)",
                    "arrow": "δ(q0, $, Z0) = (qf, Z0)",
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
                    "action": "READ '$': unclosed tag(s) remain: {} -> REJECT".format(unclosed),
                    "arrow": "δ(q0, $, {}) = undefined -> q_err".format(stack[-1]),
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
    data = request.get_json() or {}
    html = data.get('html', '').strip()
    mode = data.get('mode', 'xml').strip().lower()
    if mode not in ('html', 'xml'):
        mode = 'xml'
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
