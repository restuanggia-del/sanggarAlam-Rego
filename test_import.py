#!/usr/bin/env python
import sys
import traceback

try:
    print("Testing import main from app...")
    sys.path.insert(0, 'app')
    import main
    print("SUCCESS: module main imported successfully!")
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
