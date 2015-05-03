# package imports
import prob2020.python.mutation_context as mc
import prob2020.python.permutation as pm
import prob2020.cython.cutils as cutils
import prob2020.python.utils as utils

# external imports
import numpy as np
import pandas as pd
import scipy.stats as stats


def fishers_method(pvals):
    """Fisher's method for combining independent p-values."""
    pvals = np.asarray(pvals)
    degrees_of_freedom = 2 * pvals.size
    chisq_stat = np.sum(-2*np.log(pvals))
    fishers_pval = stats.chi2.sf(chisq_stat, degrees_of_freedom)
    return fishers_pval


def cummin(x):
    """A python implementation of the cummin function in R"""
    for i in range(1, len(x)):
        if x[i-1] < x[i]:
            x[i] = x[i-1]
    return x


def bh_fdr(pval):
    """A python implementation of the Benjamani-Hochberg FDR method.

    This code should always give precisely the same answer as using
    p.adjust(pval, method="BH") in R.

    Parameters
    ----------
    pval : list or array
        list/array of p-values

    Returns
    -------
    pval_adj : np.array
        adjusted p-values according the benjamani-hochberg method
    """
    pval_array = np.array(pval)
    sorted_order = np.argsort(pval_array)
    original_order = np.argsort(sorted_order)
    pval_array = pval_array[sorted_order]

    # calculate the needed alpha
    n = float(len(pval))
    pval_adj = np.zeros(n)
    i = np.arange(1, n+1, dtype=float)[::-1]  # largest to smallest
    pval_adj = np.minimum(1, cummin(n/i * pval_array[::-1]))[::-1]
    return pval_adj[original_order]


def calc_deleterious_p_value(mut_info,
                             unmapped_mut_info,
                             fs_ct,
                             prob_inactive,
                             sc,
                             gs,
                             bed,
                             num_permutations,
                             del_threshold,
                             pseudo_count,
                             seed=None):
    """Calculates the p-value for the number of inactivating SNV mutations.

    Calculates p-value based on how many simulations exceed the observed value.

    Parameters
    ----------
    mut_info : dict
        contains codon and amino acid residue information for mutations mappable
        to provided reference tx.
    unmapped_mut_info : dict
        contains codon/amino acid residue info for mutations that are NOT mappable
        to provided reference tx.
    fs_ct : int
        number of frameshifts for gene
    prob_inactive : float
        proportion of inactivating mutations out of total over all genes
    sc : SequenceContext
        object contains the nucleotide contexts for a gene such that new random
        positions can be obtained while respecting nucleotide context.
    gs : GeneSequence
        contains gene sequence
    bed : BedLine
        just used to return gene name
    num_permutations : int
        number of permutations to perform to estimate p-value. more permutations
        means more precision on the p-value.
    seed : int (Default: None)
        seed number to random number generator (None to be randomly set)
    """
    prng = np.random.RandomState(seed)
    if len(mut_info) > 0:
        mut_info['Coding Position'] = mut_info['Coding Position'].astype(int)
        mut_info['Context'] = mut_info['Coding Position'].apply(lambda x: sc.pos2context[x])

        # group mutations by context
        cols = ['Context', 'Tumor_Allele']
        unmapped_mut_df = pd.DataFrame(unmapped_mut_info)
        tmp_df = pd.concat([mut_info[cols], unmapped_mut_df[cols]])
        context_cts = tmp_df['Context'].value_counts()
        context_to_mutations = dict((name, group['Tumor_Allele'])
                                    for name, group in tmp_df.groupby('Context'))

        # get deleterious info for actual mutations
        aa_mut_info = mc.get_aa_mut_info(mut_info['Coding Position'],
                                         mut_info['Tumor_Allele'].tolist(),
                                         gs)
        ref_aa = aa_mut_info['Reference AA'] + unmapped_mut_info['Reference AA']
        somatic_aa = aa_mut_info['Somatic AA'] + unmapped_mut_info['Somatic AA']
        codon_pos = aa_mut_info['Codon Pos'] + unmapped_mut_info['Codon Pos']
        num_snv_del = cutils.calc_deleterious_info(ref_aa, somatic_aa, codon_pos)
        num_del = fs_ct + num_snv_del

        # skip permutation test if number of deleterious mutations is not at
        # least meet some user-specified threshold
        if num_del >= del_threshold:
            # perform permutations
            null_del_list = pm.deleterious_permutation(context_cts,
                                                       context_to_mutations,
                                                       sc,  # sequence context obj
                                                       gs,  # gene sequence obj
                                                       num_permutations,
                                                       pseudo_count)

            # calculate p-value
            if not fs_ct:
                # calculate p-value if no frameshift occurs
                del_num_nulls = sum([1 for d in null_del_list
                                     if d+utils.epsilon >= num_del])
            else:
                # adjust null if frameshifts happened
                inactive_fs_null = prng.binomial(fs_ct, prob_inactive, num_permutations)
                del_num_nulls_array = np.array(null_del_list) + inactive_fs_null + utils.epsilon
                del_num_nulls = np.sum(del_num_nulls_array>=num_del)
            del_p_value = del_num_nulls / float(num_permutations)
        else:
            del_p_value = None
    else:
        num_del = 0
        del_p_value = None

    result = [bed.gene_name, num_del, del_p_value]
    return result


def calc_position_p_value(mut_info,
                          unmapped_mut_info,
                          sc,
                          gs,
                          bed,
                          num_permutations,
                          pseudo_count,
                          min_recurrent,
                          min_fraction):
    if len(mut_info) > 0:
        mut_info['Coding Position'] = mut_info['Coding Position'].astype(int)
        mut_info['Context'] = mut_info['Coding Position'].apply(lambda x: sc.pos2context[x])

        # group mutations by context
        cols = ['Context', 'Tumor_Allele']
        unmapped_mut_df = pd.DataFrame(unmapped_mut_info)
        tmp_df = pd.concat([mut_info[cols], unmapped_mut_df[cols]])
        context_cts = tmp_df['Context'].value_counts()
        context_to_mutations = dict((name, group['Tumor_Allele'])
                                    for name, group in tmp_df.groupby('Context'))

        # perform permutations
        permutation_result = pm.position_permutation(context_cts,
                                                     context_to_mutations,
                                                     sc,  # sequence context obj
                                                     gs,  # gene sequence obj
                                                     num_permutations,
                                                     pseudo_count)
        num_recur_list, pos_entropy_list, delta_pos_entropy_list = permutation_result  # unpack results

        # get recurrent info for actual mutations
        aa_mut_info = mc.get_aa_mut_info(mut_info['Coding Position'],
                                         mut_info['Tumor_Allele'].tolist(),
                                         gs)
        codon_pos = aa_mut_info['Codon Pos'] + unmapped_mut_info['Codon Pos']
        ref_aa = aa_mut_info['Reference AA'] + unmapped_mut_info['Reference AA']
        somatic_aa = aa_mut_info['Somatic AA'] + unmapped_mut_info['Somatic AA']
        num_recurrent, pos_ent, delta_pos_ent = cutils.calc_pos_info(codon_pos,
                                                                     ref_aa,
                                                                     somatic_aa,
                                                                     min_frac=min_fraction,
                                                                     min_recur=min_recurrent)

        # calculate permutation p-value
        recur_num_nulls = sum([1 for null_recur in num_recur_list
                               if null_recur+utils.epsilon >= num_recurrent])
        entropy_num_nulls = sum([1 for null_ent in pos_entropy_list
                                 if null_ent-utils.epsilon <= pos_ent])
        delta_entropy_num_nulls = sum([1 for null_ent in delta_pos_entropy_list
                                       if null_ent+utils.epsilon >= delta_pos_ent])
        recur_p_value = recur_num_nulls / float(num_permutations)
        ent_p_value = entropy_num_nulls / float(num_permutations)
        delta_ent_p_value = delta_entropy_num_nulls / float(num_permutations)
    else:
        num_recurrent = 0
        pos_ent = 0
        delta_pos_ent = 0
        recur_p_value = 1.0
        ent_p_value = 1.0
        delta_ent_p_value = 1.0
    result = [bed.gene_name, num_recurrent, pos_ent, delta_pos_ent,
              recur_p_value, ent_p_value, delta_ent_p_value]
    return result


def calc_effect_p_value(mut_info,
                        unmapped_mut_info,
                        sc,
                        gs,
                        bed,
                        num_permutations,
                        pseudo_count,
                        min_recurrent,
                        min_fraction):
    if len(mut_info) > 0:
        mut_info['Coding Position'] = mut_info['Coding Position'].astype(int)
        mut_info['Context'] = mut_info['Coding Position'].apply(lambda x: sc.pos2context[x])

        # group mutations by context
        cols = ['Context', 'Tumor_Allele']
        unmapped_mut_df = pd.DataFrame(unmapped_mut_info)
        tmp_df = pd.concat([mut_info[cols], unmapped_mut_df[cols]])
        context_cts = tmp_df['Context'].value_counts()
        context_to_mutations = dict((name, group['Tumor_Allele'])
                                    for name, group in tmp_df.groupby('Context'))

        # perform permutations
        permutation_result = pm.effect_permutation(context_cts,
                                                   context_to_mutations,
                                                   sc,  # sequence context obj
                                                   gs,  # gene sequence obj
                                                   num_permutations,
                                                   pseudo_count)
        effect_entropy_list, recur_list, inactivating_list = permutation_result  # unpack results

        # get effect info for actual mutations
        aa_mut_info = mc.get_aa_mut_info(mut_info['Coding Position'],
                                         mut_info['Tumor_Allele'].tolist(),
                                         gs)
        codon_pos = aa_mut_info['Codon Pos'] + unmapped_mut_info['Codon Pos']
        ref_aa = aa_mut_info['Reference AA'] + unmapped_mut_info['Reference AA']
        somatic_aa = aa_mut_info['Somatic AA'] + unmapped_mut_info['Somatic AA']
        effect_ent, num_recur, num_inactivating = cutils.calc_effect_info(codon_pos,
                                                                          ref_aa,
                                                                          somatic_aa,
                                                                          min_frac=min_fraction,
                                                                          min_recur=min_recurrent)

        # calculate permutation p-value
        entropy_num_nulls = sum([1 for null_ent in effect_entropy_list
                                 if null_ent-utils.epsilon <= effect_ent])
        ent_p_value = entropy_num_nulls / float(num_permutations)
    else:
        num_recur = 0
        num_inactivating = 0
        effect_ent = 0
        ent_p_value = 1.0
    result = [bed.gene_name, num_recur, num_inactivating,
              effect_ent, ent_p_value]
    return result