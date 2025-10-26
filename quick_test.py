import pandas as pd
import numpy as np


stats = dict()
insta_users = pd.read_csv('instagram_users.csv')
matched = pd.read_csv('instagram_x_square_matched_users.csv')
unmatched = pd.read_csv('unmatched_square_users.csv')
appts = pd.read_csv('square_data_appts.csv')
square_users = pd.read_csv('square_users.csv')

stats['instagram_users'] = insta_users['title'].count()
stats['instagram_users_from_marketing'] = insta_users['marketing_ad'].count()
stats['square_users'] = square_users['client_phone'].count()
stats['matched_users'] = matched['title'].count()
stats['unmatched_users'] = unmatched['client_phone'].count()
stats['matched_users_from_marketing'] = matched['marketing_ad'].count()
stats['matched_users_from_marketing_to_consultation'] = ((matched['consultation_count'] > 0) & (matched['marketing_ad'] == True)).sum()
stats['matched_users_from_marketing_to_appointment'] = ((matched['appointment_count'] > 0) & (matched['marketing_ad'] == True)).sum()
stats['sqaure_total_appointments'] = appts['appointment_id'].count()
stats['square_consultations'] = square_users['consultation_count'].sum()
stats['square_appointments'] = square_users['appointment_count'].sum()
stats['square_users_with_consultation'] = (square_users['consultation_count'] > 0).sum()
stats['square_users_with_appointment'] = (square_users['appointment_count'] > 0).sum()

stats['share_of_matched_users_from_marketing'] = round(stats['matched_users_from_marketing'] / stats['matched_users'], 4)*100
stats['share_of_matched_marketing_users_to_consultation'] = round(stats['matched_users_from_marketing_to_consultation'] / stats['matched_users'], 4)*100
stats['share_of_matched_marketing_users_to_appointments'] = round(stats['matched_users_from_marketing_to_appointment'] / stats['matched_users'], 4)*100
stats['share_of_instagram_users_from_marketign'] = round(stats['instagram_users_from_marketing'] / stats['instagram_users'], 4)*100
stats['total_instagram_users_to_square_appointments'] = round(stats['square_appointments'] / stats['instagram_users'], 4)*100
stats['total_instagram_users_to_square_users'] = round(stats['square_users'] / stats['instagram_users'], 4)*100
stats['total_instagram_users_to_square_users_with_consultation'] = round(stats['square_users_with_consultation'] / stats['instagram_users'], 4)*100
stats['total_instagram_users_to_square_users_with_appointment'] = round(stats['square_users_with_appointment'] / stats['instagram_users'], 4)*100
stats['Ana conversion (consultation to appointment)'] = round(stats['square_users_with_appointment'] / stats['square_users_with_consultation'], 4)*100

df = pd.DataFrame(stats, index=[0])
df = df.T.reset_index()
df.columns = ['metric', 'value']
df.to_csv('stats.csv', index=False)
print(df)
