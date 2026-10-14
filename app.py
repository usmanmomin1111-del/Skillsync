"""
SkillSync Root Launcher
Enables running `python app.py` directly from the project root.
"""
import os
import sys
import importlib.util

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLSYNC_DIR = os.path.join(ROOT_DIR, "skillsync")

if SKILLSYNC_DIR not in sys.path:
    sys.path.insert(0, SKILLSYNC_DIR)

os.chdir(SKILLSYNC_DIR)

spec = importlib.util.spec_from_file_location("skillsync_main", os.path.join(SKILLSYNC_DIR, "app.py"))
skillsync_module = importlib.util.module_from_spec(spec)
sys.modules["skillsync_main"] = skillsync_module
spec.loader.exec_module(skillsync_module)

app = skillsync_module.app

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

