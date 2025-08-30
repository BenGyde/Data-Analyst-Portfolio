-- Insert below student details in students table and print all data of table.

--+---------+--------+-------+
--| ID  |  Name       | Gender|
--+---------+--------+-------+
--|   3     |  Kim    |   F   |
--|   4     | Molina  |   F   |
--|   5     | Dev     |   M   |
--+---------+--------+-------+

INSERT INTO students (id, name, gender)
VALUES 
    (3, 'Kim', 'F'),
    (4, 'Molina', 'F'),
    (5, 'Dev', 'M');

SELECT *
FROM students
