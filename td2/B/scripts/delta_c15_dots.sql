-- C15, Dots (138920 vs reference 168680): rows missed because case (b) is omitted.
-- Reference window: 25 completed years on 2026-09-25, orders from 2026-03-01 to 2026-06-01 (exclusive).
-- Dots keeps only: birth year 2001 and birthday reached on 09-25.
SELECT c.customer_id, c.birth_date, COUNT(*) AS order_lines,
       SUM(o.quantity_product * p.price) AS revenue_cents
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
JOIN product p ON p.product_id = o.product_id
WHERE o.date >= '2026-03-01 00:00:00' AND o.date < '2026-06-01 00:00:00'
  AND c.birth_date > '2000-09-25' AND c.birth_date <= '2001-09-25'
  AND NOT (strftime('%Y', c.birth_date) = '2001'
           AND strftime('%m-%d', c.birth_date) <= '09-25')
GROUP BY c.customer_id, c.birth_date
ORDER BY c.customer_id;
