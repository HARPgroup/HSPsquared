# Linux Installation Instructions
>Check out HSPsquared on on Binder and try the tutorials \
[![Binder](https://mybinder.org/badge.svg)](https://mybinder.org/v2/gh/respec/HSPsquared/linux)
1. Install System Requirements
```sh
# Install Python 2, Python-dev, gfortran and virtualenv if desired
sudo apt-get update
sudo apt-get install python \
  && python-dev \
  && gfortran \
  && virtualenv # optional
```

2. Clone Repo
```sh
git clone https://github.com/respec/HSPsquared/
cd HSPsquared

# add this directory to the PYTHONPATH
export PYTHONPATH=$(pwd)
```

3. Install python requirements
```sh
# Remove included WDMtoolbox as it is not needed. Needed files are installed with pip
rm - r wdmtoolbox

# Optionally create virtualenv
virtualenv venv
# optionally set this virtual environment to activate automatically when logging in
echo "source $(pwd)/venv/bin/activate" >> ~/.bashrc
source venv/bin/activate

# Install requirements as included in the requirements.txt file
pip install --no-cache -r requirements.txt

# Install wdmtoolbox separately as it has conflicts if installed as part of requirements process
pip install --no-cache wdmtoolbox
```

3. Run Jupyter Notebooks
```sh
jupyter-notebook --ip=0.0.0.0  --port=8888
```

4. From a browser, go to localhost:8888?token={token issued on start}

5. Navigate to the HPS2Notebooks directory to explore HSP2.
