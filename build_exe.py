import PyInstaller.__main__
import os

# Get the absolute path of the current directory
current_dir = os.path.abspath(os.path.dirname(__file__))

PyInstaller.__main__.run([
    'app.py',
    '--onefile',
    '--windowed',
    '--name=TaskManager',
    f'--add-data={os.path.join(current_dir, "templates")}:templates',
    f'--add-data={os.path.join(current_dir, "static")}:static',
    '--icon=static/icon.ico',  # Optional: Add if you have an icon
    '--hidden-import=flask',
    '--hidden-import=pywebview',
    '--hidden-import=csv',
])