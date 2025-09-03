--Write an SQL query to swap all employee genders in the Salary table.

UPDATE Salary
SET sex = CASE sex
    WHEN 'm' THEN 'f'
    WHEN 'f' THEN 'm'
END
