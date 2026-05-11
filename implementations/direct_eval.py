from __future__ import annotations

from core.constitution import CONSTITUTIONS
from domains.regex_domain import ALPHABET, STR_CHARS


def parse_tokens(pattern, cfg):
    p = pattern
    if cfg["anchor_semantics"] == "strict":
        if p.count("^") > 1 or p.count("$") > 1:
            raise ValueError
        if "^" in p and not p.startswith("^"):
            raise ValueError
        if "$" in p and not p.endswith("$"):
            raise ValueError
        if p.startswith("^"):
            p = p[1:]
        if p.endswith("$"):
            p = p[:-1]
    else:
        p = p.replace("^", "").replace("$", "")
    toks = []
    i = 0
    while i < len(p):
        ch = p[i]
        if ch == "[":
            j = p.find("]", i + 1)
            if j == -1:
                if cfg["malformed_pattern_policy"] == "lazy":
                    j = len(p)
                else:
                    raise ValueError
            body = p[i + 1 : j]
            neg = body.startswith("^")
            if neg:
                body = body[1:]
            if body == "":
                if cfg["empty_class_behavior"] == "error":
                    raise ValueError
                toks.append(("class", (neg, set())))
                i = j + 1
                continue
            cls = set()
            k = 0
            while k < len(body):
                c = body[k]
                if c not in ALPHABET:
                    raise ValueError
                if k + 2 < len(body) and body[k + 1] == "-":
                    a, b = body[k], body[k + 2]
                    if a > b:
                        if cfg["invalid_range_behavior"] == "empty":
                            k += 3
                            continue
                        raise ValueError
                    if cfg["range_inclusivity"] == "partial" and k > 0:
                        cls.add(a)
                        cls.add(b)
                    else:
                        for o in range(ord(a), ord(b) + 1):
                            cls.add(chr(o))
                    k += 3
                else:
                    cls.add(c)
                    k += 1
            toks.append(("class", (neg, cls)))
            i = j + 1
            continue
        if ch == ".":
            toks.append(("dot", None))
        elif ch in ALPHABET:
            toks.append(("lit", ch))
        else:
            raise ValueError
        i += 1
    return toks


def make_engine(family, cfg):
    # Keep structural diversity via differing control flow/state representation.
    def pred(tok, ch):
        k, d = tok
        if k == "lit":
            return ch == d
        if k == "dot":
            return (ch != "\n") or cfg["dot_matches_newline"]
        neg, cls = d
        inside = ch in cls
        return (not inside) if neg else inside

    def matcher(p, s):
        toks = parse_tokens(p, cfg)
        starts = range(len(s) - len(toks) + 1) if cfg["search_vs_fullmatch"] == "search" and len(toks) <= len(s) else [0]
        if cfg["search_vs_fullmatch"] == "fullmatch" and len(s) != len(toks):
            return False
        if family == "recursive_descent":
            def rec(i, j, st):
                if i == len(toks):
                    return True if cfg["search_vs_fullmatch"] == "search" else (j == len(s))
                if j >= len(s):
                    return False
                return pred(toks[i], s[j]) and rec(i + 1, j + 1, st)

            return any(rec(0, st, st) for st in starts)
        if family == "finite_state_machine":
            trans = [(lambda tk: (lambda ch: pred(tk, ch)))(tk) for tk in toks]
            for st in starts:
                state = 0
                while state < len(trans) and st + state < len(s) and trans[state](s[st + state]):
                    state += 1
                if state == len(trans):
                    if cfg["search_vs_fullmatch"] == "search" or st + state == len(s):
                        return True
            return False
        if family == "table_driven_matcher":
            table = [{ch: pred(tk, ch) for ch in STR_CHARS} for tk in toks]
            for st in starts:
                if st + len(table) > len(s):
                    continue
                if all(table[i].get(s[st + i], False) for i in range(len(table))):
                    if cfg["search_vs_fullmatch"] == "search" or st + len(table) == len(s):
                        return True
            return False
        if family == "token_stream_interpreter":
            for st in starts:
                ok = True
                for i, tk in enumerate(toks):
                    if st + i >= len(s) or not pred(tk, s[st + i]):
                        ok = False
                        break
                if ok and (cfg["search_vs_fullmatch"] == "search" or st + len(toks) == len(s)):
                    return True
            return len(toks) == 0 and cfg["search_vs_fullmatch"] == "search"
        if family == "compiled_instruction_vm":
            code = [("MATCH", tk) for tk in toks]
            for st in starts:
                pc = 0
                sp = st
                ok = True
                while pc < len(code):
                    if sp >= len(s):
                        ok = False
                        break
                    _, tk = code[pc]
                    if not pred(tk, s[sp]):
                        ok = False
                        break
                    pc += 1
                    sp += 1
                if ok and (cfg["search_vs_fullmatch"] == "search" or sp == len(s)):
                    return True
            return False
        for st in starts:
            i = 0
            while i < len(toks) and st + i < len(s) and pred(toks[i], s[st + i]):
                i += 1
            if i == len(toks) and (cfg["search_vs_fullmatch"] == "search" or st + i == len(s)):
                return True
        return False

    return matcher


def oracle_strict(p, s):
    cfg = CONSTITUTIONS["STRICT_ASCII"]
    return make_engine("direct_pattern_walker", cfg)(p, s)
