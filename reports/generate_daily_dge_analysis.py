import pandas as pd 
import requests
import json
import datetime as dt
import os





target_clases = ['HOSPITALIZADO', 'NEUMONIA', 'INTUBADO', 'FALLECIDO']

#url = 'https://covid19.c3.unam.mx/gateway/api/analysis-population/time-validation-dge/'
body = json.loads("""
	{
	  "target": "FALLECIDO",
	  "initial_date": "2020-02-01",
	  "period": 30
	}
""")

period = 30
initial_date = dt.datetime.strptime('2020-02-01', '%Y-%m-%d').date()
delta_period = dt.timedelta(days = 30)
today = dt.date.today()

while initial_date < today:
	for target in target_clases:

		#if (target == 'CONFIRMADO' and initial_date.strftime('%Y-%m-%d') == '2020-02-01') or (target == 'HOSPITALIZADO' and initial_date.strftime('%Y-%m-%d') == '2020-02-01') or (target == 'FALLECIDO' and initial_date.strftime('%Y-%m-%d') == '2020-02-01'):
		#	continue 
		#print('dge-covariables-{0}-{1}-{2}.csv'.format(target, initial_date.strftime('%Y-%m-%d'), period))
		#print(os.listdir('./'))
		
		body['target'] = target
		body['initial_date'] = initial_date.strftime('%Y-%m-%d')
		
		if 'dge-covariables-{0}-{1}-{2}.csv'.format(target, initial_date.strftime('%Y-%m-%d'), period) in os.listdir('./'):
			pass
		else:
			print('<<<====================Start======================>>>')
			#url = 'https://covid19.c3.unam.mx/gateway/api/dge/covariables/'
			url = 'http://127.0.0.1:8000/api/dge/covariables/'
			print("URL {0}".format(url))
			print("Body {0}".format(json.dumps(body)))
			response = requests.post(url, json=body)
			print("Response {0}".format(response))
			print('<<<=====================End=======================>>>')

			try:
				df = pd.DataFrame(response.json()['covariables'])
				df.to_csv('./dge-covariables-{0}-{1}-{2}.csv'.format(target, initial_date.strftime('%Y-%m-%d'), period), index=False)
			except Exception as e:
				print(str(e))
		
		"""
		if 'dge-occurrences-{0}-{1}-{2}.csv'.format(target, initial_date.strftime('%Y-%m-%d'), period) in os.listdir('./'):
			continue

		print('<<<====================Start======================>>>')
		#url = 'https://covid19.c3.unam.mx/gateway/api/dge/cells/'
		url = 'http://127.0.0.1:8000/api/dge/cells/'
		print("URL {0}".format(url))
		print("Body {0}".format(json.dumps(body)))
		response = requests.post(url, json=body)
		print("Response {0}".format(response))
		print('<<<=====================End=======================>>>')

		try:
			df = pd.DataFrame(response.json()['occurences'])
			df.to_csv('./dge-occurrences-{0}-{1}-{2}.csv'.format(target, initial_date.strftime('%Y-%m-%d'), period), index=False)
		except Exception as e:
			print(str(e))
		"""

	
	initial_date += delta_period