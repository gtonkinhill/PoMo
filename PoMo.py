#PoMo 10 script
import sys
import os
import random
import argparse
import re
##from time import clock, time
from libPoMo.main import probability_matrix, a, dsRatio


#parse command line arguments
parser = argparse.ArgumentParser(description="PoMo10 script")
parser.add_argument('file', help="""Name of the fasta file containing
the alignment. Each individual's name must be species_n where
\"species\" is the name of its species, without underscores, and \"n\"
is a number identifying the individual among the other samples of the
same population/species (it actually does not matter which number is
given to which individual). As now, no gaps or Ns are allowed, which
means, you have to remove columns where one of the individuals has
missing characters or unknowns. It does not matter from which
individual each base comes, so you can sub-sample and randomly assign
to individuals within a species.""")

parser.add_argument('--molecular-clock', '-m', type=int,
                    choices=[0, 1], default=1, help="""Determines if
                    you want the molecular clock constraint (and
                    therefore also look for a root) or not. Default is
                    yes. To specify no molecular clock, type \"-m
                    0\".""")
parser.add_argument('--ds-ratio', '-d', type=dsRatio, default=0.66,
                    help=
                    """Determines which proportion of the data is kept after
                    downsampling. The default is 0.66. This means
                    that, if sites have different sample sizes
                    (because of mising data etc.), by default sample
                    sizes are decreased until at least 2 thirds of the
                    sites are included in the current sample sizes.""")
parser.add_argument('--verbose', '-v', action='count',
                    help='Counts the level of verbosity (e.g. -vv).'
                    'Without -v very few information is'
                    'printed to the screen.')
args = parser.parse_args()

print("""PoMo version 1.0 Created by Nicola De Maio. For a reference, please
see and cite: De Maio, Schlotterer, Kosiol (MBE, 2013), and/or: De
Maio, Kosiol (in preparation). You can use this software for
non-commercial purposes, but please, always acknowledge the
authors. For suggestions, doubts, bugs, etc., please contact
nicola.de.maio.85@gmail.com\n""")

if args.molecular_clock == 1:
    noMC = 0
elif args.molecular_clock == 0:
    noMC = 1
verbosity = args.verbose
thresh = args.ds_ratio

#define paths to files
in_name = str(args.file)
infile = open(in_name)
in_name_no_extension = in_name.rsplit(".", maxsplit=1)[0]
out_name = in_name_no_extension + "_PoMo_output.txt"
PoModata_name = in_name_no_extension + "_PoMo_HyPhy.txt"
PoModata_name_cons = in_name_no_extension + "_consensus_HyPhy.txt"

#create file descriptors
PoModatafile = open(PoModata_name, "w")
PoModatafile_cons = open(PoModata_name_cons, "w")

path = os.path.abspath(os.path.dirname(in_name))
path = path+"/"

try:
    path_PoMo = os.path.abspath(os.path.dirname(__file__))
except:
    path_PoMo = os.path.abspath(os.path.dirname(sys.argv[0]))
path_PoMo = path_PoMo+"/"

#define PoMo10 states
codons = ["aaa", "aac", "aag", "aat", "aca", "acc", "acg", "act",
          "aga", "agc", "agg", "agt", "ata", "atc", "atg", "att", "caa",
          "cac", "cag", "cat", "cca", "ccc", "ccg", "cct", "cga", "cgc",
          "cgg", "cgt", "cta", "ctc", "ctg", "ctt", "gaa", "gac", "gag",
          "gat", "gca", "gcc", "gcg", "gct", "gga", "ggc", "ggg", "ggt",
          "gta", "gtc", "gtg", "gtt", "taa", "tac", "tag", "tat", "tca",
          "tcc", "tcg", "tct", "tga", "tgc"]
nucs = ["A", "C", "G", "T"]
N = 10

#number of species
n_species = 0
#list with species names
sp_names = []
#list with sample size of each species
sp_samples = []
#list with actual data
sp_data = []

line = infile.readline()
while line[0] != ">":
    line = infile.readline()
    print(line)
    if line == "":
        break

VCF = 0
if line == "":
    #input is in vcf format
    infile.close()
    infile = open(in_name)
    while len(line) > 0 and line[0] == "#":
        line = infile.readline()
    while len(line.split()) == 0:
        line = infile.readline()
        if line == "":
            print("Error: No Data.\n")
            exit()
    sp_names = line.split()
    n_species = len(sp_names)
    if n_species < 2:
        print("Error: No sufficiently many species (<2).\n")
        exit()
    VCF = 1
    line = infile.readline()
    for i in range(n_species):
        sp_data.append([])
        sp_samples.append(0)
    while len(line.split()) > 1:
        linelist = line.split()
        if len(linelist) != n_species:
            print("Error: input line \"" + line +
                  "\" does not fit number of species.\n")
            exit()
        for i in range(n_species):
            p = linelist[i].split(",")
            if len(p) == 1:
                p = p[0].split("/")
            for j in range(4):
                p[j] = int(p[j])
            summ = 0
            for j in range(4):
                summ += p[j]
            if summ > sp_samples[i]:
                sp_samples[i] = summ
            sp_data[i].append(p)
        line = infile.readline()
    line = ""
    leng = len(sp_data[0])


#In case of Fasta format:
while line != "":
    if line[0] == ">":
        linelist = line.split()
        name = linelist[0].split("_")[0].replace(">", "")
        if len(linelist) > 1:
            init_data = linelist[len(linelist)-1]
        else:
            init_data = ""
        found = 0
        for i in range(len(sp_names)):
            if name == sp_names[i]:
                found = 1
                sp_samples[i] += 1
                sp_data[i].append("")
                if init_data != "":
                    line = init_data
                else:
                    line = infile.readline()
                while (len(line) > 0 and line[0] != ">"):
                    sp_data[i][len(sp_data[i])-1] += line.replace("\n", "")
                    line = infile.readline()
                if sp_data[i][len(sp_data[i])-1] == "":
                    print("\n\n\nSpecies " + sp_names[i] + " sample "
                          + linelist[0].split("_")[1] +
                          " has no data. PoMo is stopping here."
                          "Please check your data file.\n\n\n")
                    exit()
                break
        if found == 0:
            sp_names.append(name)
            n_species += 1
            sp_samples.append(1)
            sp_data.append([""])
            if init_data != "":
                line = init_data
            else:
                line = infile.readline()
            while (len(line) > 0 and line[0] != ">"):
                sp_data[len(sp_data)-1][0] += line.replace("\n", "")
                line = infile.readline()
            if sp_data[len(sp_data)-1][0] == "":
                print("\n\n\nSpecies " + sp_names[len(sp_data)-1] +
                      " sample " + linelist[0].split("_")[1] +
                      " has no data. PoMo is stopping here."
                      " Please check your data file.\n\n\n")
                exit()
    if len(line) > 0 and line[0] != ">":
        line = infile.readline()

#Put fasta data in counts format
DNA = ["A", "C", "G", "T"]
DNA2 = ["a", "c", "g", "t"]
if VCF == 0:
    sp_data2 = sp_data
    sp_data = []
    for i in range(n_species):
        sp_data.append([])
    leng = len(sp_data2[0][0])
    for i in range(n_species):
        for l in range(sp_samples[i]):
            if len(sp_data2[i][l]) != leng:
                print("\n\n\nError: individuals have different number "
                      "of bases (not a proper alignment).\n\n\n")
                exit()
    for l in range(n_species):
        for m in range(leng):
            count = [0, 0, 0, 0]
            for k in range(sp_samples[l]):
                for d in range(4):
                    if sp_data2[l][k][m] == DNA[d] or \
                       sp_data2[l][k][m] == DNA2[d]:
                        count[d] += 1
                        break
            p = count
            sp_data[l].append(p)

#Sites where some species have coverage 0 are removed
to_remove = []
for i in range(leng):
    total = 1
    for s in range(n_species):
        summ = 0
        for d in range(4):
            summ += sp_data[s][i][d]
        if summ == 0:
            total = 0
            break
    if total == 0:
        to_remove.append(i)
summ = 0
for i in range(len(to_remove)):
    for s in range(n_species):
        rem = sp_data[s].pop(to_remove[i]-summ)
    summ += 1

#Now, downsample if necessary
print("Doing downsampling\n")
sp_samples2 = []
for i in range(n_species):
    if sp_samples[i] > N:
        sp_samples2.append(N)
    else:
        sp_samples2.append(sp_samples[i])

covered = 0
while float(covered)/leng < thresh:
    advantages = []
    increments = []
    covered = 0
    for i in range(n_species):
        advantages.append(0)
        increments.append(10000000)
    for i in range(len(sp_data[0])):
        cov = 1
        for s in range(n_species):
            summ = 0
            for d in range(4):
                summ += sp_data[s][i][d]
            if summ < sp_samples2[s]:
                cov = 0
                if summ != 1 and summ == (sp_samples2[s]-increments[s]):
                    advantages[s] += 1
                elif summ != 1 and (sp_samples2[s]-summ) < increments[s]:
                    advantages[s] = 1
                    increments[s] = sp_samples2[s]-summ
        if cov == 1:
            covered += 1
    if float(covered)/leng >= thresh:
        break
    max_ad = 0
    max_ind = -1
    for s in range(n_species):
        if advantages[s] > max_ad:
            max_ad = advantages[s]
            max_ind = s
    if max_ad == 0:
        print("Downsampling with threshold " + str(thresh) +
              " is not possible."
              " Please lower the threshold using option --DS.\n")
        exit()
    sp_samples2[max_ind] = sp_samples2[max_ind]-increments[s]

sp_samples = sp_samples2

#Sites where some species have not sufficient coverage are removed
to_remove = []
for i in range(len(sp_data[0])):
    total = 1
    for s in range(n_species):
        summ = 0
        for d in range(4):
            summ += sp_data[s][i][d]
        if summ < sp_samples[s]:
            total = 0
            break
    if total == 0:
        to_remove.append(i)
summ = 0
for i in range(len(to_remove)):
    for s in range(n_species):
        rem = sp_data[s].pop(to_remove[i]-summ)
    summ += 1
leng = len(sp_data[0])

print("Number of species: ", str(n_species))
print("Sample sizes effectively used: ", sp_samples)
all_one = 1
for i in range(n_species):
    if sp_samples[i] != 1:
        all_one = 0
    if sp_samples[i] > N:
        print("\n\n\nWarning: the number of samples " + str(sp_samples[i]) +
              " is bigger than the virtual population size " + str(N) +
              ". The considered species will be downsampled to " + str(N) +
              ". This is usually not a problem, but if you want to avoid this,"
              " if possible please increase the virtual population size."
              "\n\n\n")
if all_one == 1:
    usr_def = float(input("""\n\n\nAll species have a sample size of
    1, therefore there is no information at the population level,
    which is required by PoMo. So, please enter a guessed or otherwise
    estimated value for theta (population diversity):\n"""))
else:
    usr_def = 0.01
infile.close()

if n_species < 2:
    print("Error: cannot calculate a tree with fewer than 2 species.")
    exit()

#default options
sampling = 1
onlysampling = 1
mbin = 0

#Writing the HyPhy batch file for PoMo
newsamfile = open(path+"PoMo10_root_only_sampling_preliminary_used.bf", "w")
samfile = open(path_PoMo+"PoMo10_root_only_sampling_preliminary.bf")
line = "\n"
while line != "/*Find Root*/\n":
    line = samfile.readline()
    linelist = line.split()
    if len(linelist) > 1 and linelist[0] == "fprintf" \
       and linelist[1] == "(stdout," and verbosity is None:
        newsamfile.write("/*"+line.replace("\n", "")+"*/\n")
    else:
        newsamfile.write(line)
samples_num = []
for i in range(n_species):
    if not (sp_samples[i] in samples_num):
        newsamfile.write(probability_matrix(sp_samples[i]))
        samples_num.append(sp_samples[i])
        newsamfile.write("\n\n\n")
line = "\n"
while line != "":
    line = samfile.readline()
    linelist = line.split()
    if line.split("=")[0] == "\tNsamples":
        newsamfile.write("\tNsamples={{\"")
        for i in range(n_species-1):
            newsamfile.write(str(sp_samples[i])+"\"}{\"")
        newsamfile.write(str(sp_samples[n_species-1])+"\"}};\n")
    elif len(linelist) > 1 and linelist[0] == "fprintf" \
         and linelist[1] == "(stdout," and verbosity is None:  # noqa
        newsamfile.write("/*"+line.replace("\n", "")+"*/\n")
    else:
        newsamfile.write(line)
samfile.close()
newsamfile.close()


#Writing the HyPhy batch file for PoMo with NNI
newsamfile = open(path+"PoMo10_NNI_sampling_preliminary_used.bf", "w")
samfile = open(path_PoMo+"PoMo10_NNI_sampling.bf")
line = "\n"
while line != "/*pre-ML*/\n":
    line = samfile.readline()
    linelist = line.split()
    if len(linelist) > 1 and linelist[0] == "fprintf" \
       and linelist[1] == "(stdout," and verbosity is None:
        newsamfile.write("/*"+line.replace("\n", "")+"*/\n")
    else:
        newsamfile.write(line)
samples_num = []
for i in range(n_species):
    if not (sp_samples[i] in samples_num):
        newsamfile.write(probability_matrix(sp_samples[i]))
        samples_num.append(sp_samples[i])
        newsamfile.write("\n\n\n")
line = "\n"
while line != "":
    line = samfile.readline()
    linelist = line.split()
    if line.split("=")[0] == "\tNsamples":
        newsamfile.write("\tNsamples={{\"")
        for i in range(n_species-1):
            newsamfile.write(str(sp_samples[i])+"\"}{\"")
        newsamfile.write(str(sp_samples[n_species-1])+"\"}};\n")
    elif len(linelist) > 1 and linelist[0] == "fprintf" \
         and linelist[1] == "(stdout," and verbosity is None:  # noqa
        newsamfile.write("/*"+line.replace("\n", "")+"*/\n")
    else:
        newsamfile.write(line)
samfile.close()
newsamfile.close()

#creating HyPhy input file
for l in range(n_species):
    PoModatafile.write(">s"+str(l+1)+"\n")
    PoModatafile_cons.write(">s"+str(l+1)+"\n")
    for m in range(leng):
        count = sp_data[l][m]
        p = count
        maxcount = 0
        i2 = -1
        for j2 in range(4):
            if p[j2] > maxcount:
                i1 = j2
                maxcount = p[j2]
        refs3 = codons[i1]
        maxcount = 0
        for j2 in range(4):
            if j2 != i1 and p[j2] > maxcount:
                i2 = j2
                maxcount = p[j2]
        if i2 == -1:
            refs = codons[i1]
            refs2 = codons[i1]
        else:
            if p[i1]+p[i2] > sp_samples[l]:
                count1 = p[i1]
                count2 = p[i2]
                newcount1 = 0
                newcount2 = 0
                for j5 in range(sp_samples[l]):
                    num = random.random()
                    if num < float(count1)/(count1+count2):
                        newcount1 += 1
                        count1 = count1 - 1
                    else:
                        newcount2 += 1
                        count2 = count2 - 1
            else:
                newcount1 = p[i1]
                newcount2 = p[i2]
            if i1 > i2:
                i3 = i1
                i1 = i2
                i2 = i3
                newcount3 = newcount1
                newcount1 = newcount2
                newcount2 = newcount3
            if newcount1 == sp_samples[l]:
                refs = codons[i1]
                refs2 = codons[i1]
            elif newcount2 == sp_samples[l]:
                refs = codons[i2]
                refs2 = codons[i2]
            else:
                pol = 0
                if i1 == 1:
                    pol = 3
                if i1 == 2:
                    pol = 5
                pol += (i2-(i1+1))
                p1 = newcount2 - 1
                pos = 4+pol*(N-1)+p1
                refs = codons[pos]
        PoModatafile.write(refs)
        PoModatafile_cons.write(refs3)
    PoModatafile.write("\n")
    PoModatafile_cons.write("\n")
PoModatafile.close()
PoModatafile_cons.close()

print("\nRunning 1: NJ consensus\n")
#Run HyPhy concatenation, NJ and root positioning, on consensus data
HPfile = open(path_PoMo+"Nuc_NJandRoot.bf")
HPfile2 = open(path+"Nuc_NJandRoot_used.bf", "w")
line = HPfile.readline()
line = HPfile.readline()
HPfile2.write("inp=\""+PoModata_name_cons+"\";\n")
HPfile2.write("out2=\"" + in_name.split(".")[0] +
              "_consensus_NJandRoot_out.txt\";\n")
while line != "":
    line = HPfile.readline()
    linelist = line.split()
    if len(linelist) > 0 and linelist[0] == "ExecuteAFile":
        HPfile2.write(line.replace("pairwise", path_PoMo + "pairwise"))
    elif len(linelist) > 1 and linelist[0] == "fprintf" \
         and linelist[1] == "(stdout," and verbosity is None:  # noqa
        HPfile2.write("/*" + line.replace("\n", "") + "*/\n")
    else:
        HPfile2.write(line)
HPfile2.close()
HPfile.close()
os.system("cd "+path_PoMo+"\n"+"./HYPHYMP "+path+"Nuc_NJandRoot_used.bf \n")

file = open(in_name.split(".")[0]+"_consensus_NJandRoot_out.txt")
line = file.readline()
linel = line.split()
while line != "":
    line = file.readline()
    linel = line.split()
    if (len(linel) > 1 and linel[0] == "Tree"):
        lasttree = linel[1].replace("givenTree=", "").replace("testTree=", "")
        for i in range((2 * n_species) - 3):
            lasttree = lasttree.replace("Node" + str(n_species-i), "")
NucNJtree_cons = lasttree
file.close()

if n_species > 3:
    print("\nRunning 2: NNI consensus\n")
    #Running HyPhy concatenation, finding topology and root altogether
    #with NNI and rooting, on consensus data
    HPfile = open(path_PoMo+"Nuc_NNIwithRoot.bf")
    HPfile3 = open(path + "Nuc_NNIwithRoot_used.bf", "w")
    line = HPfile.readline()
    line = HPfile.readline()
    line = HPfile.readline()
    HPfile3.write("inp = \""+PoModata_name_cons+"\";\n")
    HPfile3.write("out2=\"" + in_name.split(".")[0] +
                  "_consensus_NNIwithRoot_out.txt\";\n")
    HPfile3.write("treeString=\""+NucNJtree_cons+"\";\n")
    while line != "":
        line = HPfile.readline()
        linelist = line.split()
        if len(linelist) > 0 and linelist[0] == "ExecuteAFile":
            HPfile3.write(line.replace("pairwise", path_PoMo+"pairwise"))
        elif len(linelist) > 0 and linelist[0] == "#include":
            HPfile3.write(line.replace("heuristic", path_PoMo + "heuristic"))
        elif len(linelist) > 1 and linelist[0] == "fprintf" \
             and linelist[1] == "(stdout," and verbosity is None:  # noqa
            HPfile3.write("/*" + line.replace("\n", "") + "*/\n")
        else:
            HPfile3.write(line)
    HPfile3.close()
    HPfile.close()
    os.system(path_PoMo+"HYPHYMP "+path+"Nuc_NNIwithRoot_used.bf \n")

    HPofile = open(in_name.split(".")[0]+"_consensus_NNIwithRoot_out.txt")
    line = HPofile.readline()
    while line != "":
        line = HPofile.readline()
        linel = line.split()
        if (len(linel) > 1 and linel[0] == "Tree"):
            lasttree = linel[1].replace("givenTree=", "")
            lasttree = lasttree.replace("testTree=", "")
            for i in range((2*n_species) - 3):
                lasttree = lasttree.replace("Node" + str(n_species-i), "")
    consetree = lasttree
    HPofile.close()

    print("\nRunning 3: NNI PoMo\n")
    #Running PoMo10, finding the topology with NNI
    HPfile = open(path+"PoMo10_NNI_sampling_preliminary_used.bf")
    HPfile2 = open(path+"PoMo10_NNI_sampling_used.bf", "w")
    line = HPfile.readline()
    line = HPfile.readline()
    line = HPfile.readline()
    line = HPfile.readline()
    line = HPfile.readline()
    line = HPfile.readline()
    line = HPfile.readline()
    line = HPfile.readline()
    HPfile2.write("inp = \""+PoModata_name+"\";\n")
    HPfile2.write("out2=\""+path+"PoMo10_NNI_sampling_out.txt\";\n")
    if all_one == 1:
        HPfile2.write("user_defining=1;\n")
    else:
        HPfile2.write("user_defining=0;\n")
    HPfile2.write("user_defined_Ppol="+str(usr_def)+";\n")
    if all_one == 1:
        HPfile2.write("scale_Ppol:=1.0;\n")
    else:
        a_total = 0.0
        for i in range(n_species):
            a_total += a(sp_samples[i])
        a_total = a_total/n_species
        HPfile2.write("scale_Ppol:="+str(a(N)/a_total)+";\n")
    HPfile2.write("sample:=0;\n")
    NJtree2 = consetree
    NJtree2Samp = NJtree2
    for ss in range(n_species):
        NJtree2Samp = NJtree2Samp.replace("s"+str(n_species-ss),
                                          "(z"+str(n_species-ss) +
                                          "{Mto" +
                                          str(sp_samples[(n_species-1)-ss]) +
                                          "}:1.0)u" +
                                          str(n_species-ss)+"{M1}")
    for ss in range(n_species):
        NJtree2Samp = NJtree2Samp.replace("z", "s")
    HPfile2.write("treeString=\""+NJtree2Samp+"\";\n")
    HPfile2.write("NoSampTree=\""+consetree+"\";\n")
    while line != "":
        line = HPfile.readline()
        linelist = line.split()
        if len(linelist) > 0 and linelist[0] == "ExecuteAFile":
            HPfile2.write(line.replace("pairwise", path_PoMo + "pairwise"))
        elif len(linelist) > 0 and linelist[0] == "#include":
            HPfile2.write(line.replace("heuristic", path_PoMo + "heuristic"))
        else:
            HPfile2.write(line)
    HPfile2.close()
    HPfile.close()
    os.system(path_PoMo+"HYPHYMP "+path+"PoMo10_NNI_sampling_used.bf \n")
    HPofile = open(path+"PoMo10_NNI_sampling_out.txt")
    line = HPofile.readline()
    while line != "":
        line = HPofile.readline()
        linel = line.split()
        if (len(linel) > 1 and linel[0] == "Tree"):
            lasttree = linel[1].replace("givenTree=", "")
            lasttree = lasttree.replace("testTree=", "")
            for i in range((2*n_species) - 3):
                lasttree = lasttree.replace("Node" + str(n_species-i), "")
    NNItreesamp = lasttree
    HPofile.close()
else:
    NNItreesamp = NucNJtree_cons

# What happens when there is no molecular clock?
if n_species > 3 and noMC == 1:
    #If PoMo NNI has been done, output outcome
    HPofile = open(path+"PoMo10_NNI_sampling_out.txt")
    line = HPofile.readline()
    out_wr = line
    out_wr2 = ""
    while line != "":
        line = HPofile.readline()
        linel = line.split()
        if (len(linel) > 1 and linel[0] == "Tree"):
            lasttree = linel[1].replace("givenTree=", "")
            lasttree = lasttree.replace("testTree=", "")
            for i in range((2*n_species)):
                lasttree = lasttree.replace("Node" + str(n_species-i), "")
            out_wr2 = out_wr
            out_wr = ""
        else:
            out_wr += line
    swap_fast_samp_tree = lasttree
    HPofile.close()


elif n_species <= 3 and noMC == 1:
    #If no PoMo NNI has been done, do a single ML run without looking
    #for best topology Writing the HyPhy batch file for PoMo without
    #NNI
    newsamfile = open(path + "PoMo10_NoMolClock_preliminary.bf", "w")
    samfile = open(path_PoMo+"PoMo10_NoMolClock.bf")
    line = "\n"
    while line != "/*pre-ML*/\n":
        line = samfile.readline()
        linelist = line.split()
        if len(linelist) > 1 and linelist[0] == "fprintf" \
           and linelist[1] == "(stdout," and verbosity is None:
            newsamfile.write("/*" + line.replace("\n", "") + "*/\n")
        else:
            newsamfile.write(line)
    samples_num = []
    for i in range(n_species):
        if not (sp_samples[i] in samples_num):
            newsamfile.write(probability_matrix(sp_samples[i]))
            samples_num.append(sp_samples[i])
            newsamfile.write("\n\n\n")
    line = "\n"
    while line != "":
        line = samfile.readline()
        linelist = line.split()
        if len(linelist) > 1 and linelist[0] == "fprintf" \
           and linelist[1] == "(stdout," and verbosity is None:
            newsamfile.write("/*" + line.replace("\n", "") + "*/\n")
        else:
            newsamfile.write(line)
    samfile.close()
    newsamfile.close()

    print("\nRunning PoMo without Molecular clock\n")
    #Running PoMo10, finding the topology with NNI
    HPfile = open(path + "PoMo10_NoMolClock_preliminary.bf")
    HPfile2 = open(path + "PoMo10_NoMolClock_used.bf", "w")
    line = HPfile.readline()
    line = HPfile.readline()
    line = HPfile.readline()
    line = HPfile.readline()
    line = HPfile.readline()
    line = HPfile.readline()
    line = HPfile.readline()
    line = HPfile.readline()
    HPfile2.write("inp = \"" + PoModata_name + "\";\n")
    HPfile2.write("out2=\"" + path + "PoMo10_NoMolClock_out.txt\";\n")
    if all_one == 1:
        HPfile2.write("user_defining=1;\n")
    else:
        HPfile2.write("user_defining=0;\n")
    HPfile2.write("user_defined_Ppol="+str(usr_def)+";\n")
    if all_one == 1:
        HPfile2.write("scale_Ppol:=1.0;\n")
    else:
        a_total = 0.0
        for i in range(n_species):
            a_total += a(sp_samples[i])
        a_total = a_total/n_species
        HPfile2.write("scale_Ppol:="+str(a(N)/a_total)+";\n")
    HPfile2.write("sample:=0;\n")
    NJtree2 = NucNJtree_cons
    NJtree2Samp = NJtree2
    for ss in range(n_species):
        NJtree2Samp = NJtree2Samp.replace("s" + str(n_species-ss), "(z" +
                                          str(n_species-ss) + "{Mto" +
                                          str(sp_samples[(n_species-1)-ss]) +
                                          "}:1.0)u" + str(n_species-ss) +
                                          "{M1}")
    for ss in range(n_species):
        NJtree2Samp = NJtree2Samp.replace("z", "s")
    HPfile2.write("treeString=\""+NJtree2Samp+"\";\n")
    HPfile2.write("NoSampTree=\""+NucNJtree_cons+"\";\n")
    while line != "":
        line = HPfile.readline()
        linelist = line.split()
        if len(linelist) > 0 and linelist[0] == "ExecuteAFile":
            HPfile2.write(line.replace("pairwise", path_PoMo + "pairwise"))
        elif len(linelist) > 0 and linelist[0] == "#include":
            HPfile2.write(line.replace("heuristic", path_PoMo + "heuristic"))
        else:
            HPfile2.write(line)
    HPfile2.close()
    HPfile.close()
    os.system(path_PoMo+"HYPHYMP "+path+"PoMo10_NoMolClock_used.bf \n")
    HPofile = open(path+"PoMo10_NoMolClock_out.txt")
    line = HPofile.readline()
    out_wr = line
    out_wr2 = ""
    while line != "":
        line = HPofile.readline()
        linel = line.split()
        if (len(linel) > 1 and linel[0] == "Tree"):
            lasttree = linel[1].replace("givenTree=", "")
            lasttree = lasttree.replace("testTree=", "")
            for i in range((2*n_species)):
                lasttree = lasttree.replace("Node" + str(n_species-i), "")
            out_wr2 = out_wr
            out_wr = ""
        else:
            out_wr += line
    swap_fast_samp_tree = lasttree
    HPofile.close()

else:
    print("\nRunning 4: Rooting PoMo\n")
    #Running PoMo10, finding root from the topology estimated with NNI
    #and PoMo10
    HPfile = open(path + "PoMo10_root_only_sampling_preliminary_used.bf")
    HPfile2 = open(path + "PoMo10_root_only_sampling_used.bf", "w")
    line = HPfile.readline()
    line = HPfile.readline()
    line = HPfile.readline()
    line = HPfile.readline()
    line = HPfile.readline()
    HPfile2.write("inp = \"" + PoModata_name+"\";\n")
    HPfile2.write("out2=\"" + path + "PoMo10_NNI_sampling_rooted_out.txt\";\n")
    if all_one == 1:
        HPfile2.write("user_defining=1;\n")
    else:
        HPfile2.write("user_defining=0;\n")
    HPfile2.write("user_defined_Ppol=" + str(usr_def) + ";\n")
    if all_one == 1:
        HPfile2.write("scale_Ppol:=1.0;\n")
    else:
        a_total = 0.0
        for i in range(n_species):
            a_total += a(sp_samples[i])
        a_total = a_total/n_species
        HPfile2.write("scale_Ppol:="+str(a(N)/a_total)+";\n")

    NJtree2 = NNItreesamp
    while line != "":
        line = HPfile.readline()
        if len(line.split("=")) > 1 and line.split("=")[0] == "treeString" \
           and line.split("=")[1].replace("\n", "") == "\"\";":
            lasttree = NJtree2
            if n_species > 3:
                for spes in range(n_species):
                    pap = re.compile("\\(s" + str(spes+1) + ":" +
                                     "\\d+(\\.\\d+)?" + "(e-\\d\\d)?\\)u" +
                                     str(spes+1))
                    mam = pap.search(lasttree)
                    lasttree = lasttree.replace(mam.group(), "s" + str(spes+1))
            HPfile2.write("treeString=\""+lasttree+"\";\n")
        else:
            HPfile2.write(line)
    HPfile2.close()
    HPfile.close()
    os.system(path_PoMo+"HYPHYMP "+path+"PoMo10_root_only_sampling_used.bf \n")

    HPofile = open(path+"PoMo10_NNI_sampling_rooted_out.txt")
    line = HPofile.readline()
    out_wr = line
    out_wr2 = ""
    while line != "":
        line = HPofile.readline()
        linel = line.split()
        if (len(linel) > 1 and linel[0] == "Tree"):
            lasttree = linel[1].replace("givenTree=", "")
            lasttree = lasttree.replace("testTree=", "")
            for i in range((2*n_species)):
                lasttree = lasttree.replace("Node" + str(n_species-i), "")
            out_wr2 = out_wr
            out_wr = ""
        else:
            out_wr += line
    swap_fast_samp_tree = lasttree
    HPofile.close()

#Write final output to file
for spes in range(n_species):
    pap = re.compile("\\(s" + str(n_species-spes) + ":" + "\\d+(\\.\\d+)?" +
                     "(e-\\d\\d)?\\)u" + str(n_species-spes))
    mam = pap.search(swap_fast_samp_tree)
    swap_fast_samp_tree = swap_fast_samp_tree.replace(mam.group(), sp_names[(n_species - 1) - spes])  # noqa
# for i in range(n_species):
#     swap_fast_samp_tree = swap_fast_samp_tree.replace("s" + str((n_species)-i), sp_names[(n_species-1)-i])  # noqa
out_wr2 += swap_fast_samp_tree
outfile = open(out_name, "w")
outfile.write(out_wr2)
outfile.write("\n")
outfile.close

os.system("rm -f "+path+"Nuc_NJandRoot_used.bf")
os.system("rm -f "+in_name.split(".")[0]+"_consensus_NJandRoot_out.txt")
os.system("rm -f "+path+"Nuc_NNIwithRoot_used.bf")
os.system("rm -f "+in_name.split(".")[0]+"_consensus_NNIwithRoot_out.txt")
os.system("rm -f "+path+"PoMo10_NNI_sampling_used.bf")
os.system("rm -f "+path+"PoMo10_NNI_sampling_out.txt")
os.system("rm -f "+path+"PoMo10_root_only_sampling_used.bf")
os.system("rm -f "+path+"PoMo10_NNI_sampling_rooted_out.txt")
os.system("rm -f "+path+"PoMo10_root_only_sampling_preliminary_used.bf")
os.system("rm -f "+path+"PoMo10_NNI_sampling_preliminary_used.bf")
os.system("rm -f "+PoModata_name_cons)
os.system("rm -f "+PoModata_name)
os.system("rm -f "+path+"PoMo10_NoMolClock_out.txt")
os.system("rm -f "+path+"PoMo10_NoMolClock_preliminary.bf")
os.system("rm -f "+path+"PoMo10_NoMolClock_used.bf")
exit()