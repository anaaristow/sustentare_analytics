import numpy as np
import pandas as pd
import mysql.connector


# Dealing with RD Station - Lead info
def process_rd_station_profile(df):

    """
    Transform the columns of DataFrame to lowercase and replace spaces in column names with underscores also,
    Process the DataFrame to handle missing values and create consolidated columns.

    Parameters:
    - rd_station (DataFrame): The original RD Station DataFrame.

    Returns:
    - df (DataFrame): Processed RD Station profile with consolidated and cleaned columns.
        """
    
    df.columns = df.columns.str.lower().str.replace(' ', '_')

    rd_station_profile = df[[
        'email', 'nome', 'lead_scoring_-_perfil', 'url_pública', 'estágio_no_funil', 'total_de_conversões',
        'lead_scoring_-_interesse', 'status_para_comunicação_por_email',
        'data_da_primeira_conversão', 'eventos_(últimos_100)', 'origem_da_última_conversão',
        'data_da_última_conversão', 'origem_da_primeira_conversão', 'curso_de_interesse:',
        'empresa', 'cargo.1', 'tags', 'data_da_última_oportunidade', 'cargo', 'estado',
        'valor_total_da_oportunidade_no_crm_(última_atualização)',
        'qualificação_da_oportunidade_no_crm_(última_atualização)',
        'etapa_do_funil_de_vendas_no_crm_(última_atualização)',
        'nome_do_responsável_pela_oportunidade_no_crm_(última_atualização)',
        'origem_da_oportunidade_no_crm_(última_atualização)',
        'cidade', 'possui_interesse_em_realizar_uma_pós-graduação_ou_mba?',
        'qual_é_a_sua_área_de_atuação?', 'selecione_o_curso_desejado:.1',
        'qual_a_sua_área_de_atuação?', 'data_de_nascimento',
        'desejo_receber_o_sustentare_news', 'qual_sua_área_de_interesse?',
        'como_você_conheceu_a_sustentare:', 'universidade', 'reside_em:',
        'cidade_de_residência:', 'interesse_em', 'qual_o_curso_de_interesse?'
    ]]

    rd_station_profile.loc[:, 'cidade_final'] = (
        rd_station_profile['cidade']
        .fillna(rd_station_profile['reside_em:'])
        .fillna(rd_station_profile['cidade_de_residência:'])
    )

    rd_station_profile.loc[:, 'cargo_final'] = (
        rd_station_profile['cargo.1']
        .fillna(rd_station_profile['cargo'])
    )

    rd_station_profile.loc[:, 'area_atuacao'] = (
        rd_station_profile['qual_é_a_sua_área_de_atuação?']
        .fillna(rd_station_profile['qual_a_sua_área_de_atuação?'])
    )

    rd_station_profile.loc[:, 'interesse_final'] = (
        rd_station_profile['curso_de_interesse:']
        .fillna(rd_station_profile['selecione_o_curso_desejado:.1'])
        .fillna(rd_station_profile['qual_sua_área_de_interesse?'])
        .fillna(rd_station_profile['interesse_em'])
        .fillna(rd_station_profile['qual_o_curso_de_interesse?'])
    )
    rd_station_profile = rd_station_profile.drop(columns=['cidade', 'reside_em:', 'cidade_de_residência:', 'cargo.1', 'cargo', 'qual_é_a_sua_área_de_atuação?', 'qual_a_sua_área_de_atuação?', 'curso_de_interesse:', 'qual_sua_área_de_interesse?', 'interesse_em', 'selecione_o_curso_desejado:.1'])

    return rd_station_profile


# Dealing with Unimestre - Student info
def connect_to_database(config):

    """  
    Establishes a connection to a MySQL database using the provided configuration.
        """
    
    try:
        connection = mysql.connector.connect(**config)
        return connection
    except Exception as e:
        print(f"Error connecting to the MySQL database: {e}")
        return None
    

def get_student_information(connection):

    """
    Performs a SQL query to join tables from the 'unimestre' and 'unimestre_moodle' databases.
    Selects specific columns such as 'cd_pessoa', 'ds_email', 'ds_cidade', 'dt_nascimento', and 'min_dt_log'
    and returns the result as a DataFrame. The query includes joins and left joins to connect data from
    multiple tables.

    Returns:
    - df (DataFrame): DataFrame containing selected columns from joined tables.
    
    """
    if connection is None:
        return "Connection to database failed."

    cursor = connection.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()

    query = f'''SELECT
    pessoas.cd_pessoa,
    moodle.ds_email,
    CONCAT(UPPER(SUBSTRING(pessoas.ds_cidade, 1, 1)), LOWER(SUBSTRING(pessoas.ds_cidade, 2))) as ds_cidade,
    pessoas.dt_nascimento,
    log.min_dt_log
    FROM
    unimestre.pessoas AS pessoas
JOIN 
    unimestre_moodle.view_moodle_pessoas AS moodle
    ON pessoas.cd_pessoa = moodle.cd_pessoa
LEFT JOIN (
    SELECT
        cd_pessoa,
        MIN(dt_log) as min_dt_log
    FROM
        unimestre.diario_logs
    GROUP BY
        cd_pessoa
) AS log ON pessoas.cd_pessoa = log.cd_pessoa
limit 100000;
'''
    df = pd.read_sql(query, connection)
    df = df.groupby('ds_email').first().reset_index()

    cursor.close()

    return df

def first_cd_turma_for_students(connection):
    """
    Performs a SQL query to retrieve information about the first 'cd_turma' for students
    from the 'unimestre.view_matriculas' table. Calculates the 'ano' and 'semestre' based on the
    'cd_turma' column and determines the minimum date associated with each 'cd_pessoa', 'cd_turma', 'ano',
    and 'semestre' combination. The result is returned as a Pandas DataFrame.

    Returns:
    - df (DataFrame): A DataFrame containing information about the first 'cd_turma' for students.

    """
    if connection is None:
        return "Connection to database failed."

    cursor = connection.cursor()

    # SQL query to retrieve information about the first 'cd_turma' for students
    query = f'''SELECT
    m.cd_pessoa,
    m.cd_turma,
    SUBSTRING(m.cd_turma, LOCATE('20', m.cd_turma), 4) AS ano,
    SUBSTRING(m.cd_turma, LOCATE('20', m.cd_turma) + 4, 1) AS semestre,
    MIN(
        CASE
            WHEN SUBSTRING(m.cd_turma, LOCATE('20', m.cd_turma) + 4, 1) = 'A' THEN DATE_FORMAT(CONCAT(SUBSTRING(m.cd_turma, LOCATE('20', m.cd_turma), 4), '-02-01'), '%Y-%m-%d')
            WHEN SUBSTRING(m.cd_turma, LOCATE('20', m.cd_turma) + 4, 1) = 'B' THEN DATE_FORMAT(CONCAT(SUBSTRING(m.cd_turma, LOCATE('20', m.cd_turma), 4), '-07-01'), '%Y-%m-%d')
            ELSE NULL
        END
    ) AS min_date
    FROM
    unimestre.view_matriculas AS m
    GROUP BY
    m.cd_pessoa, m.cd_turma, ano, semestre
    LIMIT 100000;
    '''

    # Read the query result into a Pandas DataFrame
    df = pd.read_sql(query, connection)

    cursor.close()

    return df


# Trying to find the info of the first contact of the student with the school in another table
def first_contact_dates_for_students(connection):

    """ 
    Returns:
    - df (DataFrame): A DataFrame containing information about the first contact date of students.

    SQL query to retrieve information about the first contact date of students
    with the school from the 'unimestre.pessoas' table. The query selects the 'cd_pessoa' and 'dt_cadastro'
    columns, grouping the results by 'cd_pessoa' to get unique records. The result is returned as a DataFrame.
    
    """
    if connection is None:
        return "Connection to database failed."

    cursor = connection.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()

    query = f'''
    SELECT
        cd_pessoa, dt_cadastro 
    FROM
        unimestre.pessoas
    GROUP BY cd_pessoa
    LIMIT 100000; 
    '''
    df = pd.read_sql(query, connection)

    cursor.close()

    return df


# Merge df info student and handle missing value on min_dt_log
def handle_missing_value_on_min_dt_log(info_student_unimestre, dt_cadastro_student, first_cd_turma_student):
    """
    Merge three DataFrames based on 'cd_pessoa' and handle missing values.

    Parameters:
    - info_student_unimestre (DataFrame): DataFrame containing student information from Unimestre.
    - dt_cadastro_student (DataFrame): DataFrame containing student registration dates.
    - first_cd_turma_student (DataFrame): DataFrame containing the first contact date of students with the school.

    Returns:
    - merged_df (DataFrame): Merged DataFrame with handled missing values.
    """
    # Merge 'info_student_unimestre' with 'dt_cadastro_student'
    merged_df = pd.merge(info_student_unimestre, dt_cadastro_student[['cd_pessoa', 'dt_cadastro']], on='cd_pessoa', how='left')

    # Merge the result with 'first_cd_turma_student'
    merged_df = pd.merge(merged_df, first_cd_turma_student[['cd_pessoa', 'min_date']], on='cd_pessoa', how='left')

    # Handle missing values in 'dt_cadastro'
    info_student_unimestre['min_dt_log'] = merged_df['dt_cadastro'].fillna(merged_df['min_date']).fillna(info_student_unimestre['min_dt_log'])

    return info_student_unimestre

# Join RD Station and Unimestre - save as a csv
def merge_and_preprocess_data(rd_station_profile, info_student_unimestre):
    """
    Merge data from RD Station and Unimestre, and perform necessary preprocessing.

    Parameters:
    - rd_station_profile (DataFrame): DataFrame containing data from RD Station.
    - info_student_unimestre (DataFrame): DataFrame containing student information from Unimestre.

    Returns:
    - merged_df (DataFrame): Merged DataFrame with preprocessed columns.

    """
    # Merge data from RD Station and Unimestre based on the email column
    merge_left = rd_station_profile.merge(info_student_unimestre, left_on='email', right_on='ds_email', how='left')

    # Create a binary column 'aluno' indicating whether a person is a student
    merge_left['aluno'] = (merge_left['cd_pessoa'].notnull()).astype(int)

    # Handle missing values in 'cidade' and 'data_nascimento'
    merge_left.loc[:, 'cidade'] = merge_left['ds_cidade'].fillna(merge_left['cidade_final'])
    merge_left.loc[:, 'data_nascimento'] = merge_left['dt_nascimento'].fillna(merge_left['data_de_nascimento'])

    # Drop unnecessary columns
    merge_left = merge_left.drop(columns=['ds_cidade', 'cidade_final', 'dt_nascimento', 'data_de_nascimento'])

    return merge_left

