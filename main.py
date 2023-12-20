import pandas as pd
import numpy as np
import os
import mysql.connector
from datetime import datetime
import re
import src.extraction as ext
import src.transformation as tran
import dotenv as env
env.load_dotenv()

# extraction.py
#Info Leads
rd_station = pd.read_csv("data/lead_complete_rdstation.csv", sep=",")
rd_station_profile = ext.process_rd_station_profile(rd_station)

# Database connection details
db_config = {
    'user': os.getenv('user'),
    'password': os.getenv('password'),
    'host': os.getenv('host'),
    'database': os.getenv('database')
}
db_connection = ext.connect_to_database(db_config)

# Info Student
info_student_unimestre = ext.get_student_information(db_connection)
first_cd_turma_student = ext.first_cd_turma_for_students(db_connection)
dt_cadastro_student = ext.first_contact_dates_for_students(db_connection)
info_student_unimestre_merge = ext.handle_missing_value_on_min_dt_log(info_student_unimestre, dt_cadastro_student, first_cd_turma_student)

# Merging RD Station and Unimestre and converting into csv
merge_left = ext.merge_and_preprocess_data(rd_station_profile, info_student_unimestre)
print(merge_left['aluno'].value_counts())
# Save the result to a CSV file
merge_left.to_csv("data/merged_lead_student.csv")

# ------------------------------------------------ # ----------------------------------------------------

# transformation.py

# Datetime
merge_left = tran.convert_columns_to_datetime(merge_left)
# Months since
perfil_df = tran.calculate_months_since_conversion(merge_left)
# Calculate Age
perfil_df = tran.create_column_with_calculate_age(perfil_df)
# Dealing with 'Evento' column
new_perfil_df = tran.add_keyword_columns(perfil_df) 
# Save the result to a CSV file
new_perfil_df.to_csv('data/clear_perfil_visitor_and_students.csv', index=False)
