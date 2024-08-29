# routing
Laboratorio 3 - Algoritmos de Enrutamiento

To create the executable you can use library pyinstaller

To download it just run
```bash
pip install pyinstaller
```

To create the executable run based on current OS.
```bash
pyinstaller --onefile --hidden-import yaml --collect-all slixmpp --collect-all tkinter InteractiveClientGUI.py
```

To create the executable run for Windows (Only works when running on windows.)
```
pyinstaller InteractiveClientGUIWin.spec
```

To create the executable run for Macos (Only works when running on MacOS)
```
pyinstaller InteractiveClientGUIMacOS.spec
```
