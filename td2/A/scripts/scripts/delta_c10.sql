-- C10 delta: orders counted by the reference but missed by Cohere, Qwen and Dots
SELECT c.customer_id,
       c.birth_date,
       COUNT(*) AS order_lines,
       SUM(o.quantity_product * p.price) AS revenue_cents
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
JOIN product p ON p.product_id = o.product_id
WHERE
  -- kept by the reference: 25 completed years at the order date
  c.birth_date > date(o.date, '-26 years')
  AND c.birth_date <= date(o.date, '-25 years')
  -- but NOT kept by the faulty queries (year diff = 25 and birthday reached)
  AND NOT (
    CAST(strftime('%Y', o.date) AS INTEGER) - CAST(strftime('%Y', c.birth_date) AS INTEGER) = 25
    AND strftime('%m-%d', o.date) >= strftime('%m-%d', c.birth_date)
  )
GROUP BY c.customer_id, c.birth_date
ORDER BY c.customer_id;