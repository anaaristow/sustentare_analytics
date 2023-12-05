# Checking the databases
select * from unimestre.view_matriculas limit 1; #All matriculas
select count(*) from unimestre_moodle.view_moodle_pessoas; #Info student
select * from unimestre_moodle.view_moodle_pessoas limit 1; #Info student
select count(*) from unimestre_moodle.view_moodle_pessoas limit 1; #Info student - with data_nascimento
select * from unimestre_wp.view_turmas limit 1;
select * from unimestre.pessoas  where cd_pessoa = "117607";
select count(*) from unimestre.pessoas;
select * from unimestre.pessoas limit 1;
select * from unimestre.diario_logs limit 10;

# Checking one example to see correlation between tables
select * from unimestre.pessoas where cd_pessoa = "117607";
select * from unimestre_wp.view_matriculas where codigoaluno = "117607"; # Show only one course
select * from unimestre.view_matriculas where cd_pessoa = "117607"; # Show all that the student have done/doing
# cd_turma = MKTDIGITAL2017B; MKTDIGITAL2018A; ONLINE2017B
select * from unimestre_wp.view_matriculas where cd_turma = "MKTDIGITAL2017B"; # Did not found this one... So won't be able to use this to connect
select min(dt_log) from unimestre.diario_logs where cd_pessoa = "117607";

#Distinct values in cd_turma
SELECT DISTINCT cd_turma FROM unimestre.view_matriculas;

# Checking students per year - start with 20 
SELECT
    CASE
        WHEN cd_turma LIKE '%20%' THEN SUBSTRING(cd_turma, LOCATE('20', cd_turma), 4)
        ELSE NULL
    END AS Year,
    COUNT(DISTINCT cd_pessoa) AS num_students
FROM
    unimestre.view_matriculas
GROUP BY
    Year;
    
# Checking if all unimestre_wp.view_pessoas - cd_pessoas existis in unimestre_moodle.view_moodle_pessoas - cd_pessoa
SELECT DISTINCT wp.cd_pessoa
FROM unimestre_wp.view_pessoas AS wp
LEFT JOIN unimestre_moodle.view_moodle_pessoas AS moodle ON wp.cd_pessoa = moodle.cd_pessoa
WHERE moodle.cd_pessoa IS NULL; #Return nothing: all cd_pessoas in wp are in moodle

#Counting number of cd_pessoa for unimestre_wp.view_pessoas and unimestre_moodle.view_moodle_pessoas
SELECT COUNT(DISTINCT cd_pessoa) FROM unimestre_wp.view_pessoas; #1967
SELECT COUNT(DISTINCT cd_pessoa) FROM unimestre_moodle.view_moodle_pessoas; #12056

# Joining two tables to get the maximum information filled and Transformin ds_cidade to only the first case Upper 
# Doing this modification because on the RD Station (Leads) dataset have this pattern
SELECT
    moodle.cd_pessoa AS cd_pessoa,
    CASE
        WHEN moodle.ds_cidade IS NULL THEN
            CONCAT(UPPER(SUBSTRING(wp.ds_cidade, 1, 1)), LOWER(SUBSTRING(wp.ds_cidade, 2)))
        ELSE
            CONCAT(UPPER(SUBSTRING(moodle.ds_cidade, 1, 1)), LOWER(SUBSTRING(moodle.ds_cidade, 2)))
    END AS ds_cidade,
    CASE
        WHEN moodle.ds_email IS NULL THEN wp.ds_contato
        ELSE moodle.ds_email
    END AS ds_email
FROM
    unimestre_wp.view_pessoas AS wp
RIGHT JOIN
    unimestre_moodle.view_moodle_pessoas AS moodle
    ON wp.cd_pessoa = moodle.cd_pessoa;

# Checking the null for the query above
SELECT
    COUNT(*) AS total_rows,
    SUM(CASE WHEN ds_cidade IS NULL THEN 1 ELSE 0 END) AS null_ds_cidade,
    SUM(CASE WHEN ds_email IS NULL THEN 1 ELSE 0 END) AS null_ds_email
FROM (
    SELECT
        moodle.cd_pessoa AS cd_pessoa,
        CASE
            WHEN moodle.ds_cidade IS NULL THEN
                CONCAT(UPPER(SUBSTRING(wp.ds_cidade, 1, 1)), LOWER(SUBSTRING(wp.ds_cidade, 2)))
            ELSE
                CONCAT(UPPER(SUBSTRING(moodle.ds_cidade, 1, 1)), LOWER(SUBSTRING(moodle.ds_cidade, 2)))
        END AS ds_cidade,
        CASE
            WHEN moodle.ds_email IS NULL THEN wp.ds_contato
            ELSE moodle.ds_email
        END AS ds_email
    FROM
        unimestre_wp.view_pessoas AS wp
    RIGHT JOIN
        unimestre_moodle.view_moodle_pessoas AS moodle
        ON wp.cd_pessoa = moodle.cd_pessoa
) AS subquery; #12056 - total 22333 - null

#Checking te null_ds_cidade only for the database moodle
SELECT
    COUNT(*) AS total_rows,
    SUM(CASE WHEN ds_cidade IS NULL THEN 1 ELSE 0 END) AS null_ds_cidade_moodle
FROM unimestre_moodle.view_moodle_pessoas; #12056 - total 22333 - null

#Checking te null_ds_cidade for the database unimestre.pessoas
SELECT
    COUNT(*) AS total_rows,
    SUM(CASE WHEN ds_cidade IS NULL THEN 1 ELSE 0 END) AS null_ds_cidade_moodle
FROM unimestre.pessoas; #12056 - total 22333 - null

# With this notice that the null values is the same in all tables, so no need to do join to complete fields
# Creating a query to export  to after compare with the information on RD Station leads
# Containing the first day of contact with the school (conversion day)

-- Set the wait_timeout for the current session
SET SESSION wait_timeout = 1000000000;

-- Set the interactive_timeout for the current session
SET SESSION interactive_timeout = 1000000000;
SELECT
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
limit 1000000;

# Finding the number of rows
SELECT
    COUNT(*) AS total_rows
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
) AS log ON pessoas.cd_pessoa = log.cd_pessoa;

# Counting how many cd_pessoa have no log
SELECT
    COUNT(CASE WHEN dl.dt_log IS NULL THEN 1 END) AS count_null_min_dt_log
FROM
    unimestre.pessoas AS pessoas
JOIN 
    unimestre_moodle.view_moodle_pessoas AS moodle
    ON pessoas.cd_pessoa = moodle.cd_pessoa
LEFT JOIN
    unimestre.diario_logs dl
ON
    pessoas.cd_pessoa = dl.cd_pessoa;

# Extracting '20' and two characters after it, and one character after '20' + 2 characters
SELECT
    cd_pessoa, cd_turma,
    -- Using LOCATE to find the position of '20' and SUBSTRING to extract '20' and two characters after it
    SUBSTRING(cd_turma, LOCATE('20', cd_turma), 4) AS ano,
    -- Using LOCATE('20', cd_turma) + 3 to get the position after '20' and adding one character
    SUBSTRING(cd_turma, LOCATE('20', cd_turma) + 4, 1) AS semestre
FROM
    unimestre.view_matriculas
LIMIT 500;

# Creating a query to export with the info of first day class (min date) based on the cd_turma
SELECT
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

# Counting the number of unique cd_pessoa with NULL in min_formatted_date.
SELECT
    COUNT(CASE WHEN min_date IS NULL THEN 1 ELSE NULL END) AS null_min_date_count
FROM (
    SELECT
        m.cd_pessoa,
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
        m.cd_pessoa
) AS subquery; #3094
-- ^this query was exported 

# Trying to find the info of the first contact of the student with the school in another table
SELECT
    cd_pessoa, dt_cadastro 
FROM
    unimestre.pessoas
GROUP BY cd_pessoa
LIMIT 100000; 

# Extractig the name of the students
SELECT cd_pessoa, nm_pessoa, ds_primeiro_nome, ds_email 
    FROM unimestre_moodle.view_moodle_pessoas LIMIT 100000; 