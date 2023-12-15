import numpy as np
import pandas as pd
from datetime import datetime
import re


# Columns to datime
def convert_columns_to_datetime(df):
    """
    Convert specified columns in a DataFrame to datetime format.

    Parameters:
    - DataFrame

    Returns:
    - The DataFrame with specified columns converted to datetime.
    """
    #df = df.drop(columns='Unnamed: 0')
    date_columns = ['data_da_primeira_conversão', 'data_da_última_conversão', 'data_da_última_oportunidade', 'data_nascimento', 'min_dt_log']
    
    df[date_columns] = df[date_columns].apply(lambda col: pd.to_datetime(col, errors='coerce'))
    for i in date_columns:
        df[i] = pd.to_datetime(df[i], utc=True).dt.tz_convert(None)
    return df


# Calculate months
def calculate_months_since_conversion(df):
    """
    Calculates the number of months since the first conversion based on the 'aluno' column and additional date columns.
    Drops rows where 'aluno' = 1 and min_dt_log is null.

    Parameters:
    - The input DataFrame containing the necessary columns.
    
    Returns:
    - The DataFrame with additional columns representing the number of months since the first conversion,
          last conversion, and last opportunity. Null values are assigned to these columns if the corresponding dates are null.
    """
    # Drop rows based on conditions
    df = df.drop(df[(df['aluno'] == 1) & df['min_dt_log'].isnull()].index)

    # Calculate months since conversion
    df['months_since_first_conversion'] = np.where(
        df['aluno'] == 1,
        (df['min_dt_log'] - df['data_da_primeira_conversão']).dt.days / 30,
        (datetime.now() - df['data_da_primeira_conversão']).dt.days / 30
    )

    # Calculate months since last conversion
    df['months_since_last_conversion'] = np.where(
        df['data_da_última_conversão'].notnull(),
        (df['data_da_última_conversão'] - df['data_da_primeira_conversão']).dt.days / 30,
        np.nan
    )

    # Calculate months since last opportunity
    df['months_since_last_opportunity'] = np.where(
        df['data_da_última_oportunidade'].notnull(),
        (df['data_da_última_oportunidade'] - df['data_da_primeira_conversão']).dt.days / 30,
        np.nan
    )

    #df = df.drop(columns=['data_da_primeira_conversão', 'min_dt_log', 'data_da_última_conversão', 'data_da_última_oportunidade'])

    return df

# Creating column age
def create_column_with_calculate_age(df):
    """
    Calculates age based on the birthdate column and adds a new column to the DataFrame.

    Parameters:
    - DataFrame.

    Returns:
    - The DataFrame with the new age column added.
    """
    df['age'] = pd.to_datetime(df['data_nascimento'], errors='coerce').dt.year
    current_year = pd.to_datetime('now').year
    df['age'] = current_year - df['age']

    # Set age to NaN for values less than 19 or greater than 70
    df.loc[(df['age'] < 19) | (df['age'] > 70), 'age'] = pd.NA
    
    #df = df.drop(columns='data_nascimento')

    return df


# Dealing with 'Evento' column
def add_keyword_columns(df):
    """
    Add new columns for each specific keyword and populate them with the counts of occurrences.
    Also, add a new column that represents the sum of values across all keyword columns.
    Additionally, add a new column 'total_eventos' that counts the number of values separated by "|".

    Parameters:
    - The DataFrame containing the data.

    Returns:
    - The modified DataFrame with added columns.
    """

     # Ensure 'eventos_(últimos_100)' is of type string
    df['eventos_(últimos_100)'] = df['eventos_(últimos_100)'].astype(str)

    keywords = ['live', 'newsletter', 'master-class', 'whatsapp', 'webinar', 'gratuito', 'gratuita' , 'festival', 
                'linkedin', 'ebook', 'exame-de-bolsas', 'e-book', 'bolsa-de-estudos']

    # Create a regex pattern to match variations of the keywords
    pattern = re.compile(r'\b(?:' + '|'.join(keywords) + r')\b', flags=re.IGNORECASE)

    # Iterate through each keyword and add a new column
    for i in keywords:
        # Create a new column for each keyword
        df[i] = 0

        # Iterate through each row and count occurrences
        for idx, row in df.iterrows():
            events = row['eventos_(últimos_100)'].split('/')

            # Check if the keyword appears in the events using regex
            for event in events:
                if pattern.search(event):
                    matched_keyword = pattern.search(event).group().lower()
                    if matched_keyword == i.lower():
                        # Increment the count in the corresponding column
                        df.at[idx, i] += 1

    # Add a new column for the sum of keyword columns
    df['total_interacoes'] = df[keywords].sum(axis=1)

    # Add a new column for the count of values in 'eventos_(últimos_100)'
    df['total_eventos'] = df['eventos_(últimos_100)'].apply(lambda x: x.count('/') + 1)

    # Additional operations
    df['gratuito'] = df['gratuito'] + df['gratuita']
    df = df.drop(columns=['gratuita'])
    df['ebook'] = df['ebook'] + df['e-book']
    df = df.drop(columns=['e-book'])

    return df
