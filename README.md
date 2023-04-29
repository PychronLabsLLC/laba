# Laba

[![Format code](https://github.com/PychronLabsLLC/laba/actions/workflows/format_code.yml/badge.svg?branch=main)](https://github.com/PychronLabsLLC/laba/actions/workflows/format_code.yml)
[![Python Package using Anaconda](https://github.com/PychronLabsLLC/laba/actions/workflows/python-package-conda.yml/badge.svg?branch=main)](https://github.com/PychronLabsLLC/laba/actions/workflows/python-package-conda.yml)

## Dev branch status
[![Format code](https://github.com/PychronLabsLLC/laba/actions/workflows/format_code.yml/badge.svg?branch=dev)](https://github.com/PychronLabsLLC/laba/actions/workflows/format_code.yml)
[![Python Package using Anaconda](https://github.com/PychronLabsLLC/laba/actions/workflows/python-package-conda.yml/badge.svg?branch=dev)](https://github.com/PychronLabsLLC/laba/actions/workflows/python-package-conda.yml)

This is a re imagining of some of Pychron's hardware control functionality. Laba uses the lessons learned from Pychron 
development.
The design is slightly inspired by Home Assistant


## Installation
### Setup a conda environment
```shell
conda create -n laba python=3.9 sqlalchemy pyserial pyzmq pyyaml pyqt
conda activate laba
```

### Install additional dependencies only 
```shell
pip install chaco envisage
BEZIER_NO_EXTENSION=true python -m pip install --upgrade bezier --no-binary=bezier
```

### Set Environment Variables
```shell
export LABA_ROOT=/path/to/laba
export ETS_TOOLKIT=qt4
```

### Copy the demo files to your `LABA_ROOT`

