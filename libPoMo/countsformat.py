#!/usr/bin/env python

"""libPomo.countsformat
----------------------------------------------------------------------

This model provides functions to read, write and access files that are
in counts format. This file format is used by PoMo and lists the base
counts for every position. It contains:

1 headerline with tab separated sequence names
N lines with counts of A, C, G and T bases at position n
#TODO positional information

Sheep   \t BlackSheep \t RedSheep \t Wolf    \t RedWolf
0,0,1,0 \t 0,0,1,0    \t 0,0,1,0  \t 0,0,5,0 \t 0,0,0,1
0,0,0,1 \t 0,0,0,1    \t 0,0,0,1  \t 0,0,0,5 \t 0,0,0,1
.
.
.

"""

import numpy as np
import libPoMo.seqbase as sb
import libPoMo.vcf as vcf
import libPoMo.fasta as fa


def save_as_cf(vcfStrL, refFaStr, CFFileName, verb=False,
               addL=None, nameL=None):
    """Save the given sequence in counts format.

    This function saves the SNPs from `vcfStrL`, a given list of
    VCFStream (variant call format sequence stream) objects in counts
    format to the file `CFFileName`.  The reference genome `refFaStr`,
    to which `VCFSeqStr` is compared to, needs to be passed as an
    FaStream object.

    The name of all streams in `vcfStrL` should be the same as the
    name of `faRef`.  The names of the sequences in the reference
    should be the names of the chromosomes found in the `vcfStr`
    object, otherwise we do not know where to compare the sequences
    to.  They must also be in the same order!

    Individuals with the same name and suffix "_n", where n is a
    number, will be saved in one column without the suffix.

    `vcfStrL` - list with VCF Streams containing SNPs
    `refFaStr` - reference fasta sequence stream object
    `CFFileName` - name of output file (counts format)
    `verb` - If `verb` is True, additional information is printed to
             the output file.
    `addL` - A list of truth values. If `addL[i]` is True, all
            individuals of `vcfStrL[i]` are treated as one species
            independent of their name. The respective counts are
            summed up.  If `nameL[i]` is given, the name of the summed
            sequence will be `nameL[i]`. If not, the name of the first
            individual in `vcfStrL[i]` will be used.
    `nameL` - A list of names. Cf. `addL`.

    """

    dna = {'a': 0, 'c': 1, 'g': 2, 't': 3}

    def get_cf_headerline(species):
        """Returns a string containing the headerline in counts format."""
        return '\t'.join([e for lst in species for e in lst])

    def collapse(speciesL, add=False, name=None):
        """Collapse the species names.

        Collapse the species names using the naming rules given in
        save_as_countsformat. Returns a dictionary with collapsed
        species names as keys and an assignment list.

        `add`: if set to true, all species/individuals will be
        collapsed to a single one with name `name` (if `name` is
        given).

        """
        l = len(speciesL)
        if add is True:
            if name is None:
                name = speciesL[0].rsplit('_', maxsplit=1)[0]
            assList = [name for i in range(l)]
            collapsedSp = [name]
        else:
            assList = [speciesL[i].rsplit('_', maxsplit=1)[0]
                       for i in range(l)]
            collapsedSp = sorted(set(assList))
        return (collapsedSp, assList)

    def find_next_SNP_pos(nSNPChromL, nSNPPosL, ref):
        """Find the position of next SNP.

        Return the position of the next SNP in `ref` and a list of
        indices of these SNPs in `nSNPChromL` and `nSNPPosL`. If no
        next SNP is found on this sequence (this might happen if all
        next SNPs are on the next chromosome) a ValueError is raised.
        
        `nSNPChromL` - list with chromosome names of the next SNPs of
                       the vcfStrL
        `nSNPPosL` - list with positions of the next SNPs of the
                     vcfStrL
        `ref` - Seq object of the sequence of the reference

        """
        ind = -1
        indL = []
        posL = []
        for i in range(len(nSNPChromL)):
            ind += 1
            if ref.name == nSNPChromL[i]:
                posL.append(nSNPPosL[i])
                indL.append(ind)
        if len(posL) > 0:
            npPosL = np.array(posL)
            minIndL = np.where(npPosL == npPosL.min())[0].tolist()
            fIndL = [indL[i] for i in minIndL]
            return (posL[minIndL[0]], fIndL)
        else:
            raise ValueError("No next SNP found in `ref`.")

    def fill_species_dict_ref(spDi, assL, refBase):
        """Fills the species dictionary if no SNP is present."""
        # reset species dictionary to 0 counts per base
        for key in spDi.keys():
            spDi[key] = [0, 0, 0, 0]
        # if no altBase is given, count species
        try:
            r = dna[refBase.lower()]
        except KeyError:
            # Base is not valid (reference is masked on this position).
            return None
        for sp in assL:
            spDi[sp][r] += 1
        return

    def fill_species_dict_alt(spDi, assL, refBase, altBases, spData):
        """Fills the species dictionary when a SNP is present.

        Raise SequenceDataError, if spDi could not be filled.
        """
        # reset species dictionary to 0 counts per base
        for key in spDi.keys():
            spDi[key] = [0, 0, 0, 0]
        if (altBases is not None) \
           and (spData is not None):
            bases = [refBase.lower()]
            for b in altBases:
                bases.append(b.lower())
            # loop over species
            l = len(spData[0])
            for i in range(0, len(spData)):
                # loop over chromatides (e.g. diploid)
                for d in range(0, l):
                    if spData[i][d] is not None:
                        bI = dna[bases[spData[i][d]]]
                        spDi[assL[i]][bI] += 1
            return
        raise sb.SequenceDataError("Could not fill species dictionary.")

    def get_counts_line(spDi, speciesL):
        """Returns line string in counts format."""
        stringL = []
        for i in range(len(spDi)):
            stringL.append(','.join(map(str, spDi[i][speciesL[i][0]])))
            l = len(speciesL[i])
            if l > 1:
                for j in range(1, l):
                    stringL[i] += '\t' + \
                                  ','.join(map(str, spDi[i][speciesL[i][j]]))
        return '\t'.join(stringL)

    lVcfStrL = len(vcfStrL)
    if (not isinstance(refFaStr, fa.FaStream)):
        raise sb.SequenceDataError("`faRef` is not an FaStream object.")
    for i in range(lVcfStrL):
        if (not isinstance(vcfStrL[i], vcf.VCFStream)):
            raise sb.SequenceDataError("`vcfStr` " + vcfStrL[i] +
                                       " is not a VCFStream object.")
        if vcfStrL[i].name != refFaStr.name:
            raise sb.SequenceDataError("VCF sequence name " + vcfStrL[i].name +
                                       " and reference name " + refFaStr.name +
                                       " do not match.")
        if vcfStrL[i].nSpecies == 0:
            raise sb.SequenceDataError("`VCFSeq` has no saved data.")

    # Set addL and nameL if they are not given.
    if addL is None:
        addL = []
        for i in range(lVcfStrL):
            addL.append(False)
    if nameL is None:
        nameL = []
        for i in range(lVcfStrL):
            nameL.append(None)

    # allSpeciesL = list of vcfStr species
    # assL = assignment list; allSpeciesL[i]=Wolf_n => assL[i]=Wolf
    # collSpeciesL = collapsed species list (_n removed)
    # spDi = dictionary with speciesL as keys and list of counts
    # hence, spDi[assL[i]] is the list of counts for Wolf
    allSpeciesL = []
    collSpeciesL = []
    assL = []
    spDi = []
    for i in range(lVcfStrL):
        allSpeciesL.extend(vcfStrL[i].speciesL)
        (collSpecies, ass) = collapse(vcfStrL[i].speciesL, addL[i], nameL[i])
        collSpeciesL.append(collSpecies)
        assL.append(ass)
        spDi.append(dict.fromkeys(collSpecies, None))

    with open(CFFileName, 'w') as fo:
        if verb is True:
            print("#Sequence name =", refFaStr.name, file=fo)
        print(get_cf_headerline(collSpeciesL), file=fo)
        # get chromosomes and positions of next SNPs from the vcfStrL
        nSNPChromL = []
        nSNPPosL = []
        for i in range(lVcfStrL):
            nSNPChromL.append(vcfStrL[i].base.chrom)
            nSNPPosL.append(vcfStrL[i].base.pos - 1)
        # Loop over sequences (chromosomes) in refFaStr.
        while True:
            # Initialize the saved old position of the previous SNP
            # and the sequence of the reference genome.
            oldPos = 0
            ref = refFaStr.seq
            if verb is True:
                print("#Chromosome name =", ref.name, file=fo)
            # Find next SNP position and the corresponding indices
            try:
                (nSNPPos, nSNPIndL) = find_next_SNP_pos(nSNPChromL,
                                                        nSNPPosL, ref)
            except ValueError:
                nSNPPos = ref.dataLen
                nSNPIndL = None
            # Loop over positions in sequence `ref` of the reference genome.
            while True:
                # Loop from previous SNP to one position before this one.
                for pos in range(oldPos, nSNPPos):
                    for i in range(lVcfStrL):
                        fill_species_dict_ref(spDi[i], assL[i],
                                              ref.data[pos])
                    print(get_counts_line(spDi, collSpeciesL), file=fo)
                # Process the SNP at position pos on chromosome ref.
                if nSNPIndL is None:
                    # There is no more SNP on this chromosome.
                    break
                # Set spDi to reference
                for i in range(lVcfStrL):
                    fill_species_dict_ref(spDi[i], assL[i],
                                          ref.data[nSNPPos])
                # Loop over SNPs at position nSNPPos.
                for s in range(len(nSNPIndL)):
                    altBases = vcfStrL[nSNPIndL[s]].base.get_alt_base_list()
                    spData = vcfStrL[nSNPIndL[s]].base.get_speciesData()
                    fill_species_dict_alt(spDi[nSNPIndL[s]], assL[nSNPIndL[s]],
                                          ref.data[nSNPPos], altBases,
                                          spData)
                    # Read next SNP.
                    try:
                        vcfStrL[nSNPIndL[s]].read_next_base()
                        nSNPChromL[nSNPIndL[s]]\
                            = vcfStrL[nSNPIndL[s]].base.chrom
                        nSNPPosL[nSNPIndL[s]] = vcfStrL[nSNPIndL[s]].base.pos-1
                    except ValueError:
                        # VCFStream ends here.
                        nSNPChromL[nSNPIndL[s]] = None
                        nSNPPosL[nSNPIndL[s]] = None
                # Save old SNP position.
                oldPos = nSNPPos + 1
                print(get_counts_line(spDi, collSpeciesL), file=fo)
                # Find next SNP position and the corresponding indices
                try:
                    (nSNPPos, nSNPIndL) = find_next_SNP_pos(nSNPChromL,
                                                            nSNPPosL, ref)
                except ValueError:
                    nSNPPos = ref.dataLen
                    nSNPIndL = None
            # Read next sequence in reference and break if none is found.
            if refFaStr.read_next_seq() is None:
                break
