pip3 install -r requirements.txt
python3 -m nuitka --mingw64 --onefile --output-dir=build --standalone --assume-yes-for-downloads --output-filename=pois-windows.exe pois.py
