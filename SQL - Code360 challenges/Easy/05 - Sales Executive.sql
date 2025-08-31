--Given three tables: salesperson, company, orders.
--Output all the names in the table salesperson, who didn?t have sales to company 'RED'.

SELECT salesperson.name
FROM salesperson
WHERE salesperson.sales_id NOT IN (
	SELECT orders.sales_id
	FROM orders
	JOIN company
		on orders.com_id = company.com_id
	WHERE company.name = 'RED'
)
