from pathlib import Path
import sys


PYTHON_APP_DIR = Path(__file__).resolve().parent / "python_papp"
if str(PYTHON_APP_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_APP_DIR))


from python_papp.app import *  # noqa: F401,F403
