import os
import pandas as pd
import numpy as np


files = os.listdir('./reports/')
files = [f for f in files if 'dge'==f[0:3]]

#print(files)

for f in files:
	path_file = './reports/{0}'.format(f)
	df = pd.read_csv(path_file)	

	#print(df.columns)

	epsilons = np.sign(df['epsilon'])
	scores = np.sign(df['score'])
	N = epsilons.size

	for i in range(N):
		if epsilons[i] != scores[i]:
			print(i, df.iloc[i]['variable'], df.iloc[i]['value'])
	
	print('====================================')
	#assert np.array_equal(epsilons, scores)
