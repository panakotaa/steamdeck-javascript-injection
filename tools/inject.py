#!/usr/bin/env python3
import os
import sys
from cdp import get_targets, CDPClient, extract_value

HERE    = os.path.dirname(os.path.abspath(__file__))
JS_PATH = os.path.join(HERE, "..", "frontend", "inject.js")
PAGE_MATCH = "Picture"


def find_page():
    targets = get_targets()
    t = next((t for t in targets if PAGE_MATCH.lower() in t.get("title", "").lower()), None)
    if not t:
        print("Big Picture page not found. Are you in Gaming Mode?")
        print("Pages:", [x.get("title") for x in targets])
    return t


def main():
    remove = "--remove" in sys.argv
    target = find_page()
    if not target:
        return

    with CDPClient(target["webSocketDebuggerUrl"]) as c:
        if remove:
            r = c.evaluate("window.__deckyToolbox ? (window.__deckyToolbox.stop(), 'removed') : 'nothing to remove'")
            print(extract_value(r))
            return
        with open(JS_PATH, "r", encoding="utf-8") as f:
            js = f.read()
        print(extract_value(c.evaluate(js)))


if __name__ == "__main__":
    main()
