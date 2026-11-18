-- C10: reference vs faulty logic vs missed rows, in one result
SELECT
  SUM(CASE WHEN c.birth_date > date(o.date, '-26 years')
            AND c.birth_date <= date(o.date, '-25 years')
           THEN o.quantity_product * p.price ELSE 0 END) AS reference_cents,
  SUM(CASE WHEN CAST(strftime('%Y', o.date) AS INTEGER) - CAST(strftime('%Y', c.birth_date) AS INTEGER) = 25
            AND strftime('%m-%d', o.date) >= strftime('%m-%d', c.birth_date)
           THEN o.quantity_product * p.price ELSE 0 END) AS faulty_case_a_only_cents,
  SUM(CASE WHEN CAST(strftime('%Y', o.date) AS INTEGER) - CAST(strftime('%Y', c.birth_date) AS INTEGER) = 26
            AND strftime('%m-%d', o.date) < strftime('%m-%d', c.birth_date)
           THEN o.quantity_product * p.price ELSE 0 END) AS missed_case_b_cents
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
JOIN product p ON p.product_id = o.product_id;