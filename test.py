import re
import json
import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from zipfile import ZipFile


def format_instagram(data):
    
    if data.get('messages'):
        messages = pd.DataFrame(data.get('messages'))
        title = data.get('title').encode('latin1').decode('utf-8') if isinstance(data.get('title'), str) else data.get('title')
        
        ### handle missing message like reactions
        if not 'content' in messages.columns:
            messages['content'] = ''
        messages = messages[['sender_name', 'timestamp_ms', 'content']]
        messages['title'] = title
        ### convert timestamp integer values to datetime format
        messages['timestamp_ms'] = pd.to_datetime(messages['timestamp_ms'], unit='ms')

        ### decode emojis and different language characters
        for col in ['sender_name', 'content']:
            messages[col] = messages[col].apply(
                lambda x: x.encode('latin1').decode('utf-8') if isinstance(x, str) else x
            )

        emails = []
        phones = []
        marketing_ad = ""
        ### search for email and phone patterns
        for m in messages['content'].tolist():
            m = str(m)
            emails += re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", m)
            phones += re.findall(r"(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4})", m)
            if 'replied to an ad. View ad' in m:
                marketing_ad = "TRUE"

        users = dict()
        users.update({
            'title': title,
            'marketing_ad': marketing_ad,
            'first_message': messages['timestamp_ms'].min(),
            'last_message': messages['timestamp_ms'].max()
        })

        ### filter out anavesnina emails from emails list per user and keep only unique emails
        if emails:
            emails = [e.lower() for e in emails if '@anavesnina.com' not in e]
            emails = list(set(emails))
            users.update({'emails': ', '.join(emails)})

        ### cleanup phone numbers: remove all non digit characters including spaces
        if phones:
            phones = list(set([
                re.sub(r'[^0-9]', '', p).lower() for p in phones
            ]))
            users.update({'phones': ', '.join(phones)})

        users = pd.DataFrame(users, index=[0])
        
        return messages, users
    
    return pd.DataFrame(), pd.DataFrame()

def parse_files(zipfile, csvfile):

    with ZipFile(zipfile, 'r') as zipf:
        
        messages_df = []
        users_df = []
        for f in zipf.namelist():
            ### get all message json file paths excluding message requests
            if 'message' in f and f.endswith('.json') and 'message_requests' not in f:
                with zipf.open(f, 'r') as f:
                    data = json.load(f)
                    messages, users = format_instagram(data)
                    messages_df.append(messages)
                    users_df.append(users)

    stats = dict()         
    messages = pd.concat(messages_df)
    users = pd.concat(users_df)
    users.to_csv('instagram_users.csv', index=False)
    messages.to_csv('instagram_messages.csv', index=False)
    stats['instagram_users'] = users['title'].count()
    stats['marketing_ad'] = users['marketing_ad'].count()

    square = pd.read_csv(csvfile)
    stats['total_appointments'] = square['appointment_id'].count()

    ### filter out users with no emails or phones (if either - keep)
    users = users.loc[(~users['emails'].isna()) | (~users['phones'].isna())]
    square = square[['client_email', 'client_phone', 'service']]
    ### strip country code from phones
    square['client_phone'] = square['client_phone'].apply(lambda x: str(x)[-10:])
    ### format and fill missing emails values
    square['client_email'] = square['client_email'].str.lower()
    square['client_email'] = square['client_email'].fillna('no email')
    ### format and count consultation and appointment occurancies
    square['service'] = square['service'].str.lower()
    square['consultation'] = np.where(square['service'] == 'consultation', 1, 0)
    square['appointment'] = np.where(square['service'] == 'consultation', 0, 1)
    square = square[['client_email', 'client_phone', 'consultation', 'appointment']]
    square = square.groupby(['client_email', 'client_phone']).agg(
        consultation_count=('consultation', 'sum'),
        appointment_count=('appointment', 'sum'),
    )
    square.to_csv('square_users.csv')

    ### join all square users from appointments table to instagram users from messages
    ### all users are cross joined with each other and then filtered out based on condition:
    ### if client_email of square is in email list of instagram emails found in messages OR
    ### if client_phone of square is in phones list of instagram emails found in messages
    square = square.reset_index()
    cross = square.join(users, how='cross')
    cross['email_match'] = cross.apply(lambda row: str(row['client_email']) in str(row['emails']), axis=1)
    cross['phone_match'] = cross.apply(lambda row: str(row['client_phone']) in str(row['phones']), axis=1)
    filtered = cross[cross['email_match'] | cross['phone_match']]
    filtered.to_csv('instagram_x_square_matched_users.csv', index=False)

    ### unmatched users output
    filtered = filtered[['title', 'client_email', 'client_phone']]
    unmatched_users = square.merge(filtered, on=['client_email', 'client_phone'], how='left')
    unmatched_users = unmatched_users[unmatched_users['title'].isnull()]
    unmatched_users.to_csv('unmatched_square_users.csv', index=False)


### user interface
class FileProcessorApp:
    def __init__(self, master):
        self.master = master
        master.title("Conversion rate file processor")
        master.geometry('450x150')

        self.zip_file = ""
        self.csv_file = ""

        ### Zip file selection
        tk.Label(master, text="Instagram ZIP file:").grid(row=0, column=1, padx=5, pady=5)
        self.zip_label = tk.Label(master, text="No file selected")
        self.zip_label.grid(row=0, column=2, padx=5, pady=5)
        self.zip_button = tk.Button(master, text="Select zip file", command=self.select_zip_file)
        self.zip_button.grid(row=0, column=0, padx=5, pady=5)

        ### CSV selection
        tk.Label(master, text="Square CSV file:").grid(row=1, column=1, padx=5, pady=5)
        self.csv_label = tk.Label(master, text="No file selected")
        self.csv_label.grid(row=1, column=2, padx=5, pady=5)
        self.csv_button = tk.Button(master, text="Select csv file", command=self.select_csv_file)
        self.csv_button.grid(row=1, column=0, padx=5, pady=5)

        ### Process button
        self.process_button = tk.Button(master, text="Submit", command=self.process_files)
        self.process_button.grid(row=2, column=1, pady=10)

    def select_zip_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.zip_file = file_path
            self.zip_label.config(text=self.zip_file.split('/')[-1]) # Display only filename

    def select_csv_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.csv_file = file_path
            self.csv_label.config(text=self.csv_file.split('/')[-1]) # Display only filename

    def process_files(self):
        if not self.zip_file or not self.csv_file:
            messagebox.showerror("Error", "Please select both files before processing.")
            return
        try:
            parse_files(self.zip_file, self.csv_file)
            messagebox.showinfo("Processing Complete", f"Files processed successfully!\n")
        except FileNotFoundError:
            messagebox.showerror("Error", "One or both files not found.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during processing: {e}")

root = tk.Tk()
app = FileProcessorApp(root)
root.mainloop()

# parse_files('instagram.zip', 'square_data_appts.csv')
