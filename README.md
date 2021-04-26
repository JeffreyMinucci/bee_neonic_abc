[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4721797.svg)](https://doi.org/10.5281/zenodo.4721797)

# Analysis of honey bee colony pesticide feeding study data using the VarroaPop+Pesticide model and Approximate Bayesian Computation.

This code supports **Minucci et al. 2021.** *Inferring pesticide toxicity to honey bees from a field-based feeding study using a colony model and Bayesian inference*

<br>

How to set up this repo:

```
git clone https://github.com/JeffreyMinucci/bee_neonic_abc.git
cd bee_neonic_abc
git submodule update --init
```

<br>

We utilize the VarroaPy python package, which wraps the VarroaPop+Pesticide program (written in C++ and the MFC library). This package is included as a submodule, but it's standalone repo can be found [here.](https://github.com/quanted/VarroaPy/)

<br>

#### If Github is not rendering the Jupyter Notebook files (*.ipynb), which seems to be an intermittent issue with their backend, you can view them on [Jupyter's nbviewer.](https://nbviewer.jupyter.org/github/JeffreyMinucci/bee_neonic_abc/tree/master/) 
