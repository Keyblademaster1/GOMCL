#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__    = "Guannan Wang"
__email__     = "wangguannan2014@gmail.com"
__version__   = "1"

import argparse, sys, re, os, io, operator 
from scripts.go_enrichment_result_formatter import goea_formatter, goea_filter
from scripts.go_clustering import go_compare, go_assign_cluster
from scripts.go_plot import sim_plot, sim_density, sim_newtork, construct_go_hierarchy_subgraph, sim_cumulative

try:	
	import matplotlib.pyplot as plt
except ImportError as ErrorMessage:
	print(str(ErrorMessage))
	sys.exit()	
	
try:
	import seaborn as sns
except ImportError as ErrorMessage:
	print(str(ErrorMessage))
	sys.exit()

synopsis = "\n\
#############################################################################################################################################\n\
#GOMCL-sub.py sub-clusters GO terms from selected clusters identified by GOMCL based on overlapping ratios, OC (Overlap coefficient)        #\n\
#or JC (Jaccard coefficient).                                                                                                               #\n\
#Use examples:                                                                                                                              #\n\
#   GOMCL-sub.py -Ct 0.5 -I 1.5 Test.clstr                                                                                                  #\n\
#   GOMCL-sub.py -SI JC -Ct 0.5 -I 1.5 Test.clstr                                                                                           #\n\
#                                                                                                                                           #\n\
#############################################################################################################################################"

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description = synopsis, formatter_class = argparse.RawTextHelpFormatter)
	parser.add_argument('OBOInput', metavar = '-OBO', help = 'obo file should be provided, e.g. go-basic.obo', action = 'store', nargs = None, const = None, default = None, type = None, choices = None)
	parser.add_argument('Clstr', metavar = None, help = 'clstr files generated by GOMCL.py, e.g. test.clstr', action = 'store', nargs = None, const = None, default = None, type = None, choices = None)
	parser.add_argument('-C', metavar = None, dest = "subclstr", help = 'The number of the clusters that need further processing (default: the largest cluster, C%(default)s)', action = 'store', nargs = None, const = None, default = 1, type = int, choices = None)
	parser.add_argument("-gosize", metavar = None, dest = None, help = "Threshold for the size of GO terms, only GO terms below this threshold will be printed out (default: %(default)s)", action = "store", nargs = None, const = None, default = 2500, type = int, choices = None)
	parser.add_argument("-SI", metavar = None, dest = "simindex", help = "Method to calculate similarity between GO terms, OC (Overlap coefficient) or JC (Jaccard coefficient) (default: %(default)s)", action = "store", nargs = None, const = None, default = "OC", type = str, choices = ["OC", "JC"]) 
	parser.add_argument("-Ct", metavar = None, dest = "cutoff", help = "Clustering threshold for the overlapping ratio between two GO terms, any value between 0 and 1 (default: %(default)s)", action = "store", nargs = None, const = None, default = 0.5, type = float, choices = None) 
	parser.add_argument("-I", metavar = None, dest = "inflation", help = "Inflation value, main handle for cluster granularity, usually chosen somewhere in the range [1.2-5.0] (default: %(default)s)", action = "store", nargs = None, const = None, default = 1.5, type = float, choices = None) 
	parser.add_argument("-Sig", metavar = None, dest = "sig", help = "Signifance level (p-value cutoff) used in the enrichment test (default: %(default)s)", action = "store", nargs = None, const = None, default = 0.05, type = float, choices = None)
	parser.add_argument("-ssd", metavar = None, dest = None, help = "Only needed if a similarity score distribution is desired for clusters with number of GOs larger than this threshold", action = "store", nargs = "?", const = 0, default = None, type = int, choices = None)
	parser.add_argument("-hg", metavar = None, dest = None, help = "Only needed if a hierarchy graph is desired for clusters with number of GOs larger than this threshold", action = "store", nargs = "?", const = 0, default = None, type = int, choices = None)
	parser.add_argument("-hgt", dest = None, help = "Only needed if a tabular output of the GO hierarchy is desired for the clusters specified by option -hg, should always be used with option -hg", action = "store_true", default = None)
	parser.add_argument("-hm",  dest = None, help = "Only needed if a similarity heatmap is desired", action = "store_true", default = None ) 
	parser.add_argument("-nw",  dest = None, help = "Only needed if a similarity-based network is desired", action = "store_true", default = None ) 
	args = parser.parse_args() 
	
	with open(args.Clstr, "rU") as fin_clstr:
		with open(os.path.splitext(args.Clstr)[0] + "_GOsize" + str(args.gosize) + "_" + str(args.simindex) + "_Ct" + str(args.cutoff) + "I" + str(args.inflation) + "_C" + str(args.subclstr) + ".enGOfltrd", "w") as fout_subclstr:
			fout_subclstr.write("Full GO-ID" + "\t" + "Description" + "\t" + "Type" + "\t" + "Depth" + "\t" + "p-value" + "\t" + "adj p-value" + "\t" + "x.cats.test" + "\t" + "n.cats.ref" + "\t" + "X.total.test" + "\t" + "N.total.ref" + "\t" + "Genes in test set" + "\n")
			for line_in_clstr in fin_clstr:
				line_in_clstr = line_in_clstr.rstrip()
				if line_in_clstr.split("\t")[0].isdigit():
					clstr = int(line_in_clstr.split("\t")[0])
					type = str(line_in_clstr.split("\t")[3])
					go_size_ref = int(line_in_clstr.split("\t")[8])
					if clstr == int(args.subclstr) and go_size_ref <= int(args.gosize):
						fout_subclstr.write("\t".join(map(str, line_in_clstr.split("\t")[1:])) + "\n")
	fin_clstr.close()
	fout_subclstr.close()
			
	subclstr_enGOfmtfltr_info_dict, subclstr_gosim_dict = go_compare(os.path.splitext(args.Clstr)[0] + "_GOsize" + str(args.gosize) + "_" + str(args.simindex) + "_Ct" + str(args.cutoff) + "I" + str(args.inflation) + "_C" + str(args.subclstr) + ".enGOfltrd", 1, 0, args.simindex)
	
	with open(os.path.splitext(args.Clstr)[0] + "_GOsize" + str(args.gosize) + "_" + str(args.simindex) + "_Ct" + str(args.cutoff) + "I" + str(args.inflation) + "_C" + str(args.subclstr) + ".simfltred", "w") as fout_subclstr_simfltr:
		fout_subclstr_simfltr.write("GOtermID-A"	+ "\t" + "GOtermID-B" + "\t" + "Similarity (" + str(args.simindex) + ")" + "\n")
		subclstr_processed = []
		for key_subclstr_querygo in subclstr_gosim_dict:
			for key_subclstr_subjectgo in subclstr_gosim_dict:
				if str(key_subclstr_querygo) <> str(key_subclstr_subjectgo):
					subclstr_pair_qs = str(key_subclstr_querygo) + "_" + str(key_subclstr_subjectgo)
					subclstr_pair_sq = str(key_subclstr_subjectgo) + "_" + str(key_subclstr_querygo)
					if subclstr_pair_qs not in subclstr_processed and subclstr_pair_sq not in subclstr_processed:
						if max(subclstr_gosim_dict[key_subclstr_querygo][key_subclstr_subjectgo], subclstr_gosim_dict[key_subclstr_subjectgo][key_subclstr_querygo]) >= float(args.cutoff):
							fout_subclstr_simfltr.write(str(key_subclstr_querygo) + "\t" + str(key_subclstr_subjectgo) + "\t" +  str(max(subclstr_gosim_dict[key_subclstr_querygo][key_subclstr_subjectgo], subclstr_gosim_dict[key_subclstr_subjectgo][key_subclstr_querygo])) + "\n")
							subclstr_processed.extend([subclstr_pair_qs,subclstr_pair_sq])
				else:
					fout_subclstr_simfltr.write(str(key_subclstr_querygo) + "\t" + "" + "\t" + "" + "\n")

	subclstr_go_clstr_dict, subclstr_gene_clstr_dict, subclstr_clstred_go_dict, subclstr_clstred_gene_dict = go_assign_cluster(os.path.splitext(args.Clstr)[0] + "_GOsize" + str(args.gosize) + "_" + str(args.simindex) + "_Ct" + str(args.cutoff) + "I" + str(args.inflation) + "_C" + str(args.subclstr) + ".enGOfltrd", args.simindex, args.cutoff, args.inflation)
	
	with open(os.path.splitext(args.Clstr)[0] + "_GOsize" + str(args.gosize) + "_" + str(args.simindex) + "_Ct" + str(args.cutoff) + "I" + str(args.inflation) + "_C" + str(args.subclstr) + ".subclstr", "w") as fout_subclstr_clstr:
		fout_subclstr_clstr.write("Clstr" + "\t" + "Full GO-ID" + "\t" + "Description" + "\t" + "Type" + "\t" + "Depth" + "\t" + "p-value" + "\t" + "adj p-value" + "\t" + "x.cats.test" + "\t" + "n.cats.ref" + "\t" + "X.total.test" + "\t" + "N.total.ref" + "\t" + "Genes in test set" + "\n")
		if any("D" in list(element_subclstr_enGOfmtfltr.split("\t")[3]) for element_subclstr_enGOfmtfltr in subclstr_enGOfmtfltr_info_dict.values()):
			try:
				for key_enGO in sorted(subclstr_enGOfmtfltr_info_dict, key = lambda dict_key : (int(subclstr_go_clstr_dict[dict_key]), int(subclstr_enGOfmtfltr_info_dict[dict_key].split("\t")[3].split("D")[1]), -int(subclstr_enGOfmtfltr_info_dict[dict_key].split("\t")[7]))):
					fout_subclstr_clstr.write(str(subclstr_go_clstr_dict[key_enGO]) + "\t" + "\t".join(map(str,subclstr_enGOfmtfltr_info_dict[key_enGO].split("\t"))) + "\n")
			except TypeError:
				for key_enGO in sorted(subclstr_enGOfmtfltr_info_dict, key = lambda dict_key : (int(subclstr_go_clstr_dict[dict_key]), int(subclstr_enGOfmtfltr_info_dict[dict_key].split("\t")[3].split("D")[1]))):
					fout_subclstr_clstr.write(str(subclstr_go_clstr_dict[key_enGO]) + "\t" + "\t".join(map(str,subclstr_enGOfmtfltr_info_dict[key_enGO].split("\t"))) + "\n")
		else:
			for key_enGO in sorted(subclstr_enGOfmtfltr_info_dict, key = lambda dict_key : (int(subclstr_go_clstr_dict[dict_key]), -int(subclstr_enGOfmtfltr_info_dict[dict_key].split("\t")[7]))):
					fout_subclstr_clstr.write(str(subclstr_go_clstr_dict[key_enGO]) + "\t" + "\t".join(map(str,subclstr_enGOfmtfltr_info_dict[key_enGO].split("\t"))) + "\n")
	fout_subclstr_clstr.close()


	with open(os.path.splitext(args.Clstr)[0] + "_GOsize" + str(args.gosize) + "_" + str(args.simindex) + "_Ct" + str(args.cutoff) + "I" + str(args.inflation) + "_C" + str(args.subclstr) + ".subclstrinfo", "w") as fout_subclstr_clstrinfo:
		subclstr_Accumgenelist = []
		if args.nw:
			go_sim_newtork = sim_newtork(os.path.splitext(args.Clstr)[0] + "_GOsize" + str(args.gosize) + "_" + str(args.simindex) + "_Ct" + str(args.cutoff) + "I" + str(args.inflation) + "_C" + str(args.subclstr) + ".subclstr", args.simindex, args.cutoff, args.inflation, args.sig)
			fout_subclstr_clstrinfo.write("GO.Clstr" + "\t" + "# of GOs" + "\t" + "# of genes" + "\t" + "Accum # of genes" + "\t" + "Largest size (Description) (n/N, p-value)" + "\t" + "Smallest p-value (Description) (n/N, p-value)" + "\t" + "Most connected (Description) (n/N, p-value)" + "\n")
			for clstrid in subclstr_clstred_go_dict:
				pvaluesortedlist = sorted(subclstr_clstred_go_dict[clstrid], key = lambda element_GO : float(subclstr_enGOfmtfltr_info_dict[element_GO].split("\t")[5]))
				sizesortedlist = sorted(subclstr_clstred_go_dict[clstrid], key = lambda element_GO : int(subclstr_enGOfmtfltr_info_dict[element_GO].split("\t")[7]), reverse = True)
				#minpvalueGO = min(subclstr_clstred_go_dict[clstrid], key = lambda element_GO : float(subclstr_enGOfmtfltr_info_dict[element_GO].split("\t")[5]))
				#largestGO = max(subclstr_clstred_go_dict[clstrid], key = lambda element_GO : int(subclstr_enGOfmtfltr_info_dict[element_GO].split("\t")[7]))
				edgesortedlist = sorted(subclstr_clstred_go_dict[clstrid], key = lambda element_GO : int(dict(go_sim_newtork.degree())[element_GO]), reverse = True)
				subclstr_Accumgenelist.extend(subclstr_clstred_gene_dict[clstrid])
				
				fout_subclstr_clstrinfo.write(str(args.simindex) + "Ct" + str(args.cutoff) + "I" + str(args.inflation) + "_" + str(clstrid) + "\t" + str(len(set(subclstr_clstred_go_dict[clstrid]))) + "\t" + str(len(set(subclstr_clstred_gene_dict[clstrid]))) + "\t" + str(len(set(subclstr_Accumgenelist))) + "\t" + str(sizesortedlist[0]) + " (" + str(subclstr_enGOfmtfltr_info_dict[sizesortedlist[0]].split("\t")[1]) + ")" + " (" + str(subclstr_enGOfmtfltr_info_dict[sizesortedlist[0]].split("\t")[6]) + "/" + str(subclstr_enGOfmtfltr_info_dict[sizesortedlist[0]].split("\t")[7]) + ", " + str(subclstr_enGOfmtfltr_info_dict[sizesortedlist[0]].split("\t")[5]) + ")" + "\t" + str(pvaluesortedlist[0]) + " (" + str(subclstr_enGOfmtfltr_info_dict[pvaluesortedlist[0]].split("\t")[1]) + ")" + " (" + str(subclstr_enGOfmtfltr_info_dict[pvaluesortedlist[0]].split("\t")[6]) + "/" + str(subclstr_enGOfmtfltr_info_dict[pvaluesortedlist[0]].split("\t")[7]) + ", " + str(subclstr_enGOfmtfltr_info_dict[pvaluesortedlist[0]].split("\t")[5]) + ")" + "\t" + str(edgesortedlist[0]) + " (" + str(subclstr_enGOfmtfltr_info_dict[edgesortedlist[0]].split("\t")[1]) + ")" + " (" + str(subclstr_enGOfmtfltr_info_dict[edgesortedlist[0]].split("\t")[6]) + "/" + str(subclstr_enGOfmtfltr_info_dict[edgesortedlist[0]].split("\t")[7]) + ", " + str(subclstr_enGOfmtfltr_info_dict[edgesortedlist[0]].split("\t")[5]) + ")"	+ "\n")
#				fout_subclstr_clstrinfo.write(str(args.simindex) + "Ct" + str(args.cutoff) + "I" + str(args.inflation) + "_" + str(clstrid) + "\t" + str(len(set(subclstr_clstred_go_dict[clstrid]))) + "\t" + str(len(set(subclstr_clstred_gene_dict[clstrid]))) + "\t" + str(len(set(subclstr_Accumgenelist))) + "\t" + str(sizesortedlist[0]) + " (" + str(subclstr_enGOfmtfltr_info_dict[sizesortedlist[0]].split("\t")[1]) + ")" + " (" + str(subclstr_enGOfmtfltr_info_dict[sizesortedlist[0]].split("\t")[6]) + "/" + str(subclstr_enGOfmtfltr_info_dict[sizesortedlist[0]].split("\t")[7]) + ", " + "{:.0E}".format(float(subclstr_enGOfmtfltr_info_dict[sizesortedlist[0]].split("\t")[5])) + ")" + "\t" + str(pvaluesortedlist[0]) + " (" + str(subclstr_enGOfmtfltr_info_dict[pvaluesortedlist[0]].split("\t")[1]) + ")" + " (" + str(subclstr_enGOfmtfltr_info_dict[pvaluesortedlist[0]].split("\t")[6]) + "/" + str(subclstr_enGOfmtfltr_info_dict[pvaluesortedlist[0]].split("\t")[7]) + ", " + "{:.0E}".format(float(subclstr_enGOfmtfltr_info_dict[pvaluesortedlist[0]].split("\t")[5])) + ")" + "\t" + str(edgesortedlist[0]) + " (" + str(subclstr_enGOfmtfltr_info_dict[edgesortedlist[0]].split("\t")[1]) + ")" + " (" + str(subclstr_enGOfmtfltr_info_dict[edgesortedlist[0]].split("\t")[6]) + "/" + str(subclstr_enGOfmtfltr_info_dict[edgesortedlist[0]].split("\t")[7]) + ", " + "{:.0E}".format(float(subclstr_enGOfmtfltr_info_dict[edgesortedlist[0]].split("\t")[5])) + ")"	+ "\n")
		else:
			fout_subclstr_clstrinfo.write("GO.Clstr" + "\t" + "# of GOs" + "\t" + "# of genes" + "\t" + "Accum # of genes" + "\t" + "Largest size (Description) (n/N, p-value)" + "\t" + "Smallest p-value (Description) (n/N, p-value)" + "\n")
			for clstrid in subclstr_clstred_go_dict:
				pvaluesortedlist = sorted(subclstr_clstred_go_dict[clstrid], key = lambda element_GO : float(subclstr_enGOfmtfltr_info_dict[element_GO].split("\t")[5]))
				sizesortedlist = sorted(subclstr_clstred_go_dict[clstrid], key = lambda element_GO : int(subclstr_enGOfmtfltr_info_dict[element_GO].split("\t")[7]), reverse = True)
				subclstr_Accumgenelist.extend(subclstr_clstred_gene_dict[clstrid])
				
				fout_subclstr_clstrinfo.write(str(args.simindex) + "Ct" + str(args.cutoff) + "I" + str(args.inflation) + "_" + str(clstrid) + "\t" + str(len(set(subclstr_clstred_go_dict[clstrid]))) + "\t" + str(len(set(subclstr_clstred_gene_dict[clstrid]))) + "\t" + str(len(set(subclstr_Accumgenelist))) + "\t" + str(sizesortedlist[0]) + " (" + str(subclstr_enGOfmtfltr_info_dict[sizesortedlist[0]].split("\t")[1]) + ")" + " (" + str(subclstr_enGOfmtfltr_info_dict[sizesortedlist[0]].split("\t")[6]) + "/" + str(subclstr_enGOfmtfltr_info_dict[sizesortedlist[0]].split("\t")[7]) + ", " + str(subclstr_enGOfmtfltr_info_dict[sizesortedlist[0]].split("\t")[5]) + ")" + "\t" + str(pvaluesortedlist[0]) + " (" + str(subclstr_enGOfmtfltr_info_dict[pvaluesortedlist[0]].split("\t")[1]) + ")" + " (" + str(subclstr_enGOfmtfltr_info_dict[pvaluesortedlist[0]].split("\t")[6]) + "/" + str(subclstr_enGOfmtfltr_info_dict[pvaluesortedlist[0]].split("\t")[7]) + ", " + str(subclstr_enGOfmtfltr_info_dict[pvaluesortedlist[0]].split("\t")[5]) + ")" + "\n")
#				fout_subclstr_clstrinfo.write(str(args.simindex) + "Ct" + str(args.cutoff) + "I" + str(args.inflation) + "_" + str(clstrid) + "\t" + str(len(set(subclstr_clstred_go_dict[clstrid]))) + "\t" + str(len(set(subclstr_clstred_gene_dict[clstrid]))) + "\t" + str(len(set(subclstr_Accumgenelist))) + "\t" + str(sizesortedlist[0]) + " (" + str(subclstr_enGOfmtfltr_info_dict[sizesortedlist[0]].split("\t")[1]) + ")" + " (" + str(subclstr_enGOfmtfltr_info_dict[sizesortedlist[0]].split("\t")[6]) + "/" + str(subclstr_enGOfmtfltr_info_dict[sizesortedlist[0]].split("\t")[7]) + ", " + "{:.0E}".format(float(subclstr_enGOfmtfltr_info_dict[sizesortedlist[0]].split("\t")[5])) + ")" + "\t" + str(pvaluesortedlist[0]) + " (" + str(subclstr_enGOfmtfltr_info_dict[pvaluesortedlist[0]].split("\t")[1]) + ")" + " (" + str(subclstr_enGOfmtfltr_info_dict[pvaluesortedlist[0]].split("\t")[6]) + "/" + str(subclstr_enGOfmtfltr_info_dict[pvaluesortedlist[0]].split("\t")[7]) + ", " + "{:.0E}".format(float(subclstr_enGOfmtfltr_info_dict[pvaluesortedlist[0]].split("\t")[5])) + ")" + "\n")
	fout_subclstr_clstrinfo.close()
	
	
	if args.hm:
		sim_plot(os.path.splitext(args.Clstr)[0] + "_GOsize" + str(args.gosize) + "_" + str(args.simindex) + "_Ct" + str(args.cutoff) + "I" + str(args.inflation) + "_C" + str(args.subclstr) + ".subclstr", args.simindex, args.cutoff, args.inflation)
		
	if args.ssd is not None:
		for subclstr_clstrnum in subclstr_clstred_go_dict:
			if len(subclstr_clstred_go_dict[subclstr_clstrnum]) >= max(int(args.ssd), 2):
				subclstr_simlist = []
				subclstr_processed = []
				for subclstr_clstredGO_A in subclstr_clstred_go_dict[subclstr_clstrnum]:
					for subclstr_clstredGO_B in subclstr_clstred_go_dict[subclstr_clstrnum]:
						if str(subclstr_clstredGO_A) <> str(subclstr_clstredGO_B):
							subclstr_pairAB = str(subclstr_clstredGO_A) + str(subclstr_clstredGO_B)
							subclstr_pairBA = str(subclstr_clstredGO_B) + str(subclstr_clstredGO_A)
							if subclstr_pairAB not in subclstr_processed and subclstr_pairBA not in subclstr_processed:
								subclstr_simlist.append(subclstr_gosim_dict[subclstr_clstredGO_A][subclstr_clstredGO_B])
								subclstr_processed.extend([subclstr_pairAB, subclstr_pairBA])
				try:
#					print("GOsize" + str(args.gosize) + "_" + str(args.simindex) + "_Ct" + str(args.cutoff) + "I" + str(args.inflation) + "_C" + str(args.subclstr) + "-" + str(subclstr_clstrnum) + "_P(>=0.5): " + "{:.2%}".format(len([sim for sim in subclstr_simlist if float(sim) >= 0.5])/float(len(subclstr_simlist))))
					print("GOsize{0}_{1}_Ct{2}_I{3}_C{4}-{5}_P(>=0.5): {6:.2%}".format(args.gosize, args.simindex, args.cutoff, args.inflation, args.subclstr, subclstr_clstrnum, len([sim for sim in subclstr_simlist if float(sim) >= float(args.cutoff)])/float(len(subclstr_simlist))))
				except ZeroDivisionError:
#					print("GOsize" + str(args.gosize) + "_" + str(args.simindex) + "_Ct" + str(args.cutoff) + "I" + str(args.inflation) + "_C" + str(args.subclstr) + "-" + str(subclstr_clstrnum) + "_P(>=0.5): " + "{:.2%}".format(len([sim for sim in subclstr_simlist if float(sim) >= 0.5])/float(len(subclstr_simlist))))
					print("GOsize{0}_{1}_Ct{2}_I{3}_C{4}-{5}_P(>=0.5): Only one GO term is present in this cluster.".format(args.gosize, args.simindex, args.cutoff, args.inflation, args.subclstr, subclstr_clstrnum))
					
				sim_density_plot = sim_density(subclstr_simlist, args.simindex, increment = 0.02)
				plt.savefig(os.path.splitext(args.Clstr)[0] + "_GOsize" + str(args.gosize) + "_" + str(args.simindex) + "_Ct" + str(args.cutoff) + "I" + str(args.inflation) + "_C" + str(args.subclstr) + "-" + str(subclstr_clstrnum) + "_simden.png", dpi = 600, transparent = False, bbox_inches = 'tight', pad_inches = 0)
				plt.close()
				
				sim_cumulative_plot = sim_cumulative(subclstr_simlist, args.simindex, args.cutoff, increment = 0.02)
				plt.savefig(os.path.splitext(args.Clstr)[0] + "_GOsize" + str(args.gosize) + "_" + str(args.simindex) + "_Ct" + str(args.cutoff) + "I" + str(args.inflation) + "_C" + str(args.subclstr) + "-" + str(subclstr_clstrnum) + "_simcum.png", dpi = 600, transparent = False, bbox_inches = 'tight', pad_inches = 0)
				plt.close()
	if args.hg is not None:	
		for subclstr_clstrnum in subclstr_clstred_go_dict:
			if len(subclstr_clstred_go_dict[subclstr_clstrnum]) >= int(args.hg):
				subclstr_bpgo_list = []
				subclstr_mfgo_list = []
				subclstr_ccgo_list = []
				for clstred_go in subclstr_clstred_go_dict[subclstr_clstrnum]:
					if subclstr_enGOfmtfltr_info_dict[clstred_go].split("\t")[2] == "BP":
						subclstr_bpgo_list.append(clstred_go)
					if subclstr_enGOfmtfltr_info_dict[clstred_go].split("\t")[2] == "MF":
						subclstr_mfgo_list.append(clstred_go)
					if subclstr_enGOfmtfltr_info_dict[clstred_go].split("\t")[2] == "CC":
						subclstr_ccgo_list.append(clstred_go)
				if subclstr_bpgo_list:
					clstredgo_hierarchy_network, clstredgo_hierarchy_subgraph = construct_go_hierarchy_subgraph(args.OBOInput, subclstr_bpgo_list, sig = args.sig, GOinfodict = subclstr_enGOfmtfltr_info_dict)
					plt.savefig(os.path.splitext(args.Clstr)[0] + "_GOsize" + str(args.gosize) + "_" + str(args.simindex) + "_Ct" + str(args.cutoff) + "I" + str(args.inflation) + "_C" + str(args.subclstr) + "-" + str(subclstr_clstrnum) + "_BPhierplot.png", dpi = 600, transparent = False, bbox_inches = 'tight', pad_inches = 0)
					plt.close()
					if args.hgt:
						with open(os.path.splitext(args.Clstr)[0] + "_GOsize" + str(args.gosize) + "_" + str(args.simindex) + "_Ct" + str(args.cutoff) + "I" + str(args.inflation) + "_C" + str(args.subclstr) + "-" + str(subclstr_clstrnum) + ".BPhgt", "w") as fin_subcluster_bghgt:
							fin_subcluster_bghgt.write("GOtermA" + "\t" + "GOtermB" + "\t" + "weight" + "\n")
							for edge in clstredgo_hierarchy_network.edges(data = True):
								nodeA, nodeB, attributes = edge
								fin_subcluster_bghgt.write("{0}\t{1}\t{2}\n".format(nodeA, nodeB, attributes["weight"]))
						fin_subcluster_bghgt.close()
				if subclstr_mfgo_list:
					clstredgo_hierarchy_network, clstredgo_hierarchy_subgraph = construct_go_hierarchy_subgraph(args.OBOInput, subclstr_mfgo_list, sig = args.sig, GOinfodict = subclstr_enGOfmtfltr_info_dict)
					plt.savefig(os.path.splitext(args.Clstr)[0] + "_GOsize" + str(args.gosize) + "_" + str(args.simindex) + "_Ct" + str(args.cutoff) + "I" + str(args.inflation) + "_C" + str(args.subclstr) + "-" + str(subclstr_clstrnum) + "_MFhierplot.png", dpi = 600, transparent = False, bbox_inches = 'tight', pad_inches = 0)
					plt.close()
					if args.hgt:
						with open(os.path.splitext(args.Clstr)[0] + "_GOsize" + str(args.gosize) + "_" + str(args.simindex) + "_Ct" + str(args.cutoff) + "I" + str(args.inflation) + "_C" + str(args.subclstr) + "-" + str(subclstr_clstrnum) + ".MFhgt", "w") as fin_subcluster_mfhgt:
							fin_subcluster_mfhgt.write("GOtermA" + "\t" + "GOtermB" + "\t" + "weight" + "\n")
							for edge in clstredgo_hierarchy_network.edges(data = True):
								nodeA, nodeB, attributes = edge
								fin_subcluster_mfhgt.write("{0}\t{1}\t{2}\n".format(nodeA, nodeB, attributes["weight"]))
						fin_subcluster_mfhgt.close()
				if subclstr_ccgo_list:
					clstredgo_hierarchy_network, clstredgo_hierarchy_subgraph = construct_go_hierarchy_subgraph(args.OBOInput, subclstr_ccgo_list, sig = args.sig, GOinfodict = subclstr_enGOfmtfltr_info_dict)
					plt.savefig(os.path.splitext(args.Clstr)[0] + "_GOsize" + str(args.gosize) + "_" + str(args.simindex) + "_Ct" + str(args.cutoff) + "I" + str(args.inflation) + "_C" + str(args.subclstr) + "-" + str(subclstr_clstrnum) + "_CChierplot.png", dpi = 600, transparent = False, bbox_inches = 'tight', pad_inches = 0)
					plt.close()
					if args.hgt:
						with open(os.path.splitext(args.Clstr)[0] + "_GOsize" + str(args.gosize) + "_" + str(args.simindex) + "_Ct" + str(args.cutoff) + "I" + str(args.inflation) + "_C" + str(args.subclstr) + "-" + str(subclstr_clstrnum) + ".CChgt", "w") as fin_subcluster_cchgt:
							fin_subcluster_cchgt.write("GOtermA" + "\t" + "GOtermB" + "\t" + "weight" + "\n")
							for edge in clstredgo_hierarchy_network.edges(data = True):
								nodeA, nodeB, attributes = edge
								fin_subcluster_cchgt.write("{0}\t{1}\t{2}\n".format(nodeA, nodeB, attributes["weight"]))
						fin_subcluster_cchgt.close()
						