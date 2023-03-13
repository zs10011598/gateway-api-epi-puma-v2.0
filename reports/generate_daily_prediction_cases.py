from datetime import datetime, timedelta
import requests
import json
import pandas as pd


def get_percentage_not_vaccinated(x):
    return 0 if x >= 100 else 100 - x

def get_data(url1, body1, url2, body2, demographic_group):
	'''
	'''
	try:
		print(body1['target'], demographic_group)
		response1 = requests.post(url1, json=body1)
		print(response1)
		response1 = response1.json()
		data = response1['data']
	
	
		for item in data:
			item['nom_ent'] = item['cell']['state']['name']
			item['nom_mun'] = item['cell']['name']
		
		df1 = pd.DataFrame(response1['data'])
		df1 = df1.rename(columns={'pobtot': 'POPTOT'})
		#print(data[0].keys())
		df = df1[['gridid', 'nom_ent', 'nom_mun', 'POPTOT', demographic_group, 'cases_first', 'p_first', 'score_first', 'cases_training', 'p_training', 'score_training', 'cases_predicted_validation', 'cases_validation']]
		df = df.sort_values(by='gridid')
		
		response2 = requests.post(url2, json=body2).json()
	
		df2 = pd.DataFrame(response2['summary_vaccines'])
		df2 = df2[['gridid', 'percentage_cummulated']]
		df2['percentage_not_vaccinated'] = df2['percentage_cummulated'].apply(lambda x: get_percentage_not_vaccinated(x)/100)
	
		df = df.merge(df2, on='gridid')
		df['eficacia'] = pd.Series([0.9 for i in range(df.shape[0])])
		df['prevenidos'] = df['eficacia']*df['percentage_not_vaccinated']*df['cases_predicted_validation']
		df = df.rename(columns={'gridid': 'CVEGEO'})
	
		df.to_csv('/home/pedro/chamba/PresageResearch/gateway-epi-puma-2.0/reports/QA-project42-' + body1['target'] + '-' + demographic_group + '-training-' + body1['lim_inf_training'] + 'a' + body1['lim_sup_training'] + '.csv', index=False)
	except Exception as e:
		print(str(e))


current_date = datetime(2023, 3, 12)
final_date = datetime(2023, 2, 14)
#final_date = datetime(2021, 3, 8)
#current_date = datetime.today() + timedelta(days=1)
#final_date = datetime.today() + timedelta(days=-1)

url1 = 'http://127.0.0.1:8000/api/analysis-population/time-validation/'
url2 = 'http://127.0.0.1:8000/api/vaccines/summary-vaccines/'

body1 = """{   
			"mesh": "mun",   
			"covariables": [  "inegi2020"   ],   
			"target": "FALLECIDO",   
			"attribute_filter": [{"attribute":"edad", "value": 29, "operator": "<="},
								 {"attribute":"edad", "value": 18, "operator": ">="}],   
			"demographic_group": "p_40a49",   
			"lim_inf_first": "2020-10-01",   
			"lim_sup_first": "2020-10-31",    
			"lim_inf_training": "2020-11-01",   
			"lim_sup_training": "2020-11-30",   
			"lim_inf_validation": "2020-12-01",   
			"lim_sup_validation": "2020-12-31" 
		}"""

body2 = """{
			"attribute_filter":[{"attribute":"edad","value":30,"operator":">="}, {"attribute":"edad","value":39,"operator":"<="}],
			"lim_inf_training":"2021-06-16",
			"lim_sup_training":"2021-07-15",
			"mesh":"mun",
			"demographic_group":"p_30a39"
		}"""

body1 = json.loads(body1)
body2 = json.loads(body2)

while current_date >= final_date:
	print(current_date, final_date)
	current_date += timedelta(days=-1)

	lim_inf_first      = (current_date - timedelta(days=62)).strftime("%Y-%m-%d")
	lim_sup_first      = (current_date - timedelta(days=32)).strftime("%Y-%m-%d")
	lim_inf_training   = (current_date - timedelta(days=31)).strftime("%Y-%m-%d")
	lim_sup_training   = (current_date - timedelta(days=1)).strftime("%Y-%m-%d")
	lim_inf_validation = (current_date).strftime("%Y-%m-%d")
	lim_sup_validation = (current_date + timedelta(days=30)).strftime("%Y-%m-%d")	

	print('first: ', lim_inf_first, ' a ', lim_sup_first, ', training: ', lim_inf_training, ' a ', lim_sup_training, ', validation: ', lim_inf_validation, ' a ', lim_sup_validation)

	demographic_group = 'p_60ymas'
	body2['demographic_group'] = demographic_group
	body2['attribute_filter'] = [{"attribute":"edad", "value": 60, "operator": ">="}]
	body2['lim_inf_training'] = lim_inf_training
	body2['lim_sup_training'] = lim_sup_training
	body1['demographic_group'] = demographic_group
	body1['target'] = 'CONFIRMADO'
	body1['lim_inf_first'] = lim_inf_first
	body1['lim_sup_first'] = lim_sup_first
	body1['lim_inf_training'] = lim_inf_training
	body1['lim_sup_training'] = lim_sup_training
	body1['lim_inf_validation'] = lim_inf_validation
	body1['lim_sup_validation'] = lim_sup_validation
	body1['attribute_filter'] = [{"attribute":"edad", "value": 60, "operator": ">="}]
	get_data(url1, body1, url2, body2, demographic_group)

	body1['target'] = 'FALLECIDO'
	get_data(url1, body1, url2, body2, demographic_group)

	demographic_group = 'p_50a59'
	body2['demographic_group'] = demographic_group
	body2['attribute_filter'] = [{"attribute":"edad", "value": 50, "operator": ">="}, {"attribute":"edad", "value": 59, "operator": "<="}]
	body2['lim_inf_training'] = lim_inf_training
	body2['lim_sup_training'] = lim_sup_training
	body1['target'] = 'CONFIRMADO'
	body1['demographic_group'] = demographic_group
	body1['attribute_filter'] = [{"attribute":"edad", "value": 50, "operator": ">="}, {"attribute":"edad", "value": 59, "operator": "<="}]
	get_data(url1, body1, url2, body2, demographic_group)

	body1['target'] = 'FALLECIDO'
	get_data(url1, body1, url2, body2, demographic_group)

	demographic_group = 'p_40a49'
	body2['demographic_group'] = demographic_group
	body2['attribute_filter'] = [{"attribute":"edad", "value": 40, "operator": ">="}, {"attribute":"edad", "value": 49, "operator": "<="}]
	body2['lim_inf_training'] = lim_inf_training
	body2['lim_sup_training'] = lim_sup_training
	body1['target'] = 'CONFIRMADO'
	body1['demographic_group'] = demographic_group
	body1['attribute_filter'] = [{"attribute":"edad", "value": 40, "operator": ">="}, {"attribute":"edad", "value": 49, "operator": "<="}]
	get_data(url1, body1, url2, body2, demographic_group)	
	
	body1['target'] = 'FALLECIDO'
	get_data(url1, body1, url2, body2, demographic_group)

	demographic_group = 'p_30a39'
	body2['demographic_group'] = demographic_group
	body2['attribute_filter'] = [{"attribute":"edad", "value": 30, "operator": ">="}, {"attribute":"edad", "value": 39, "operator": "<="}]
	body2['lim_inf_training'] = lim_inf_training
	body2['lim_sup_training'] = lim_sup_training
	body1['target'] = 'CONFIRMADO'
	body1['demographic_group'] = demographic_group
	body1['attribute_filter'] = [{"attribute":"edad", "value": 30, "operator": ">="}, {"attribute":"edad", "value": 39, "operator": "<="}]
	get_data(url1, body1, url2, body2, demographic_group)	

	body1['target'] = 'FALLECIDO'
	get_data(url1, body1, url2, body2, demographic_group)

	demographic_group = 'p_18a29'
	body2['demographic_group'] = demographic_group
	body2['attribute_filter'] = [{"attribute":"edad", "value": 18, "operator": ">="}, {"attribute":"edad", "value": 29, "operator": "<="}]
	body2['lim_inf_training'] = lim_inf_training
	body2['lim_sup_training'] = lim_sup_training
	body1['target'] = 'CONFIRMADO'
	body1['demographic_group'] = demographic_group
	body1['attribute_filter'] = [{"attribute":"edad", "value": 18, "operator": ">="}, {"attribute":"edad", "value": 29, "operator": "<="}]
	get_data(url1, body1, url2, body2, demographic_group)	

	body1['target'] = 'FALLECIDO'
	get_data(url1, body1, url2, body2, demographic_group)