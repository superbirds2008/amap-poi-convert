docker run --rm -v ./:/app --name  centos76-niukta superbirds2008/centos76x86-nuitka:0.1 \
  /bin/bash -c "\
  python3 -m pip install -r requirements.txt && \
  python3 -m nuitka --standalone --onefile --output-dir=build --assume-yes-for-download --output-filename=rest_pois.bin rest_pois.py"