.. Probabilistic 20/20 documentation master file, created by
   sphinx-quickstart on Mon Jul 28 13:53:42 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Probabilistic 20/20: somatic mutation simulator
===============================================

:Author: Collin Tokheim
:Contact: ctokheim AT jhu.edu
:Source code: `GitHub <https://github.com/KarchinLab/probabilistic2020>`_
:Q&A: `Biostars (tag: prob2020) <https://www.biostars.org/t/prob2020/>`_ 

The Probabibilistic 20/20 statistical test identifies genes with signficant oncogene-like and tumor suppressor gene-like mutational patterns for small somatic variants in coding regions. 
Putative signficant oncogenes are found through evaluating 
missense mutation clustering and *in silico* pathogenicity scores. Often highly clustered missense
mutations are indicative of activating mutations.
While statistically signficant tumor suppressor genes (TSGs) are found by abnormally high proportion of inactivating mutations.

Probabilistic 20/20 evaluates statistical significance by employing 
monte carlo simulations, which incorporates observed mutation base context. Monte carlo
simulations are performed within the same gene and thus avoid building a background
distribution based on other genes. This means that the statistical test can be applied 
to either all genes in the exome from exome sequencing or to a certain target set of genes
from targeted sequencing. Additionally, the direct results of somatic mutation simulations
can be accessed in a Mutation Annotation Format (MAF) file.

The Probabilistic 20/20 test has nice properties since it accounts
for several factors that could effect the significance of driver genes.

* gene length
* mutation context
* gene sequence (e.g. codon bias)

Contents:

.. toctree::
   :maxdepth: 1

   download
   installation
   quickstart
   tutorial
   faq

Citation
--------

Collin J. Tokheim, Nickolas Papadopoulos, Kenneth W. Kinzler, Bert Vogelstein, and Rachel Karchin. Evaluating the evaluation of cancer driver genes. PNAS 2016 ; published ahead of print November 22, 2016, doi:10.1073/pnas.1616440113

If you use the hotmaps1d command to find codons were missense mutations are significantly clustered, please cite the HotMAPS paper:

Tokheim C, Bhattacharya R, Niknafs N, Gygax DM, Kim R, Ryan M, Masica DL, Karchin R (2016) Exome-scale discovery of hotspot mutation regions in human cancer using 3D protein structure Cancer Research. Apr. 28.pii: canres.3190.2015. 
