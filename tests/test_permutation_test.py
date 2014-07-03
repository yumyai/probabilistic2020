# fix problems with pythons terrible import system
import os
import sys
file_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(file_dir, '../bin/'))
sys.path.append(os.path.join(file_dir, '../src/python/'))

import permutation_test as pt
import numpy as np
import utils


def test_ctnnb1_main():
    opts = {'input': os.path.join(file_dir, 'data/CTNNB1.fa'),
            'bed': os.path.join(file_dir, 'data/CTNNB1.bed'),
            'mutations': os.path.join(file_dir, 'data/CTNNB1_mutations.txt'),
            'output': os.path.join(file_dir, 'output/CTNNB1_output.txt'),
            'context': 1,
            'tsg_score': .05,
            'processes': 1,
            'num_permutations': 10000}
    # single nucleotide context
    result = pt.main(opts)
    assert result.ix[0, 'recurrent p-value'] < 0.001, 'CTNNB1 should have a very low p-value ({0}>.001)'.format(result[0][2])
    assert result.ix[0, 'entropy p-value'] < 0.001, 'CTNNB1 should have a very low p-value ({0}>.001)'.format(result[0][2])

    # di-nucleotide case
    opts['context'] = 2
    result = pt.main(opts)
    assert result.ix[0, 'recurrent p-value'] < 0.001, 'CTNNB1 should have a very low p-value ({0}>.001)'.format(result[0][2])
    assert result.ix[0, 'entropy p-value'] < 0.001, 'CTNNB1 should have a very low p-value ({0}>.001)'.format(result[0][2])

    # no context case
    opts['context'] = 0
    result = pt.main(opts)
    assert result.ix[0, 'recurrent p-value'] < 0.001, 'CTNNB1 should have a very low p-value ({0}>.001)'.format(result[0][2])
    assert result.ix[0, 'entropy p-value'] < 0.001, 'CTNNB1 should have a very low p-value ({0}>.001)'.format(result[0][2])


def test_ctnnb1_get_aa_mut_info():
    import pysam
    from gene_sequence import GeneSequence

    # read fasta
    ctnnb1_fasta = os.path.join(file_dir, 'data/CTNNB1.fa')
    gene_fa = pysam.Fastafile(ctnnb1_fasta)
    gs = GeneSequence(gene_fa, nuc_context=1)

    # read CTNNB1 bed file
    ctnnb1_bed = os.path.join(file_dir, 'data/CTNNB1.bed')
    bed_list = [b for b in utils.bed_generator(ctnnb1_bed)]
    gs.set_gene(bed_list[0])

    # specify mutation
    coding_pos = [0]
    somatic_base = ['C']

    # check mutation info
    aa_info = pt.get_aa_mut_info(coding_pos, somatic_base, gs)
    ref_codon_msg =  'First codon should be start codon ({0})'.format(aa_info['Reference Codon'][0])
    assert aa_info['Reference Codon'][0] == 'ATG', ref_codon_msg
    assert aa_info['Somatic Codon'][0] == 'CTG', 'First "A" should be replaced with a "C"'
    assert aa_info['Codon Pos'][0] == 0, 'Start codon should be position 0'


def test_100genes_main():
    opts = {'input': os.path.join(file_dir, 'data/100genes.fa'),
            'bed': os.path.join(file_dir, 'data/100genes.bed'),
            'mutations': os.path.join(file_dir, 'data/100genes_mutations.txt'),
            'output': os.path.join(file_dir, 'output/100genes_single_nuc_output.txt'),
            'context': 1,
            'tsg_score': .05,
            'processes': 5,
            'num_permutations': 10000}
    # single nucleotide context
    result = pt.main(opts)
    tested_result = result[result['Performed Recurrency Test']==1]
    assert np.sum(tested_result['recurrent BH q-value'] < .1) < 5, 'Few of the 100 test genes should not be significant'
    assert np.sum(tested_result['entropy BH q-value'] < .1) < 5, 'Few of the 100 test genes should not be significant'

    # no context case
    opts['context'] = 0
    opts['output'] = os.path.join(file_dir, 'output/100genes_no_context_output.txt')
    result = pt.main(opts)
    tested_result = result[result['Performed Recurrency Test']==1]
    assert np.sum(tested_result['recurrent BH q-value'] < .1) < 5, 'Few of the 100 test genes should not be significant'
    assert np.sum(tested_result['entropy BH q-value'] < .1) < 5, 'Few of the 100 test genes should not be significant'

    # di-nucleotide context
    opts['context'] = 2
    opts['output'] = os.path.join(file_dir, 'output/100genes_dinuc_output.txt')
    result = pt.main(opts)
    tested_result = result[result['Performed Recurrency Test']==1]
    assert np.sum(tested_result['recurrent BH q-value'] < .1) < 5, 'Few of the 100 test genes should not be significant'
    assert np.sum(tested_result['entropy BH q-value'] < .1) < 5, 'Few of the 100 test genes should not be significant'