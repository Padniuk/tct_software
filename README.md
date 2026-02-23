# TCT software

This is the software to perform and analyse TCT measurements at UZH

**Installation** is done by using *venv* module for python3.8.10

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

Create and fill *.env* file by using *.env.example* according to your sample

**Running of the measurements**

```bash
python3 main.py
```

Perform the analysis from *main.ipynb*