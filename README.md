# TCT software

This is the software to perform and analyse TCT measurements at UZH

**Installation** is done by using *venv* module for **python3.8.10**

```bash
python3 -m venv env_3_8
source env_3_8/bin/activate
pip install --upgrade pip wheel setuptools
pip install -r requirements3_8.txt
```

Create and fill *.env* file by using *.env.example* according to your sample

**Running of the GUI**

```bash
python3 gui.py
```

**Running of the measurements**

```bash
python3 main.py
```

**Analysis**

Python3.8.10 is suitable for old computer where the measurements are performed but not for jupyter notebooks. So, analysis is done with **python3.12.2** which can be manually compiled or installed. The main reason for creation of two separate env-s is that PyQt has some conflicts with this old Ubuntu 20.04

New environment creation:

```bash
python3.12 -m venv env_3_12
```

Or for example with absolute path 
```bash
/home/tct/Python-3.12.2/python -m venv env_3_12
```

Then standart procedure:
```bash
source env_3_12/bin/activate
pip install -r requirements3_12.txt
```

Then specify in your vscode or whatever you use this env and perform the analysis from *main.ipynb*