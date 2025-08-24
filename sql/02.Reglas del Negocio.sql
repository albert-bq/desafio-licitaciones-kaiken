-- Función que valida el precio de venta contra el costo del producto
CREATE OR REPLACE FUNCTION public.check_price_vs_cost()
RETURNS TRIGGER AS $$
DECLARE
  product_cost numeric;
BEGIN
  -- Obtener el costo del producto desde la tabla 'products'
  SELECT cost_prp INTO product_cost
  FROM public.products
  WHERE sku_pro = NEW.product_id;

  -- Si el precio de venta es menor o igual al costo, lanzar un error
  IF NEW.price <= product_cost THEN
    RAISE EXCEPTION 'El precio de venta (%.2f) no puede ser menor o igual al costo del producto (%.2f).', NEW.price, product_cost;
  END IF;

  -- Si la validación es exitosa, permitir la operación
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Crear el trigger en la tabla 'orders'
-- Se activa ANTES de insertar o actualizar una fila
DROP TRIGGER IF EXISTS trg_check_price_on_orders ON public.orders; -- Para evitar errores si ya existe
CREATE TRIGGER trg_check_price_on_orders
BEFORE INSERT OR UPDATE ON public.orders
FOR EACH ROW
EXECUTE FUNCTION public.check_price_vs_cost();

CREATE OR REPLACE VIEW public.order_details_with_margin AS
SELECT
  o.id AS order_id,
  o.tender_id,
  o.product_id,
  p.nom_pro AS product_name,
  o.quantity,
  p.cost_prp AS cost_price,
  o.price AS sale_price,
  -- Cálculo de la ganancia por unidad
  (o.price - p.cost_prp) AS margin_per_unit,
  -- Cálculo de la ganancia total para esta línea de orden
  (o.price - p.cost_prp) * o.quantity AS total_margin
FROM
  public.orders AS o
JOIN
  public.products AS p ON o.product_id = p.sku_pro;

  -- Para ver el detalle y margen de todas las órdenes
SELECT * FROM public.order_details_with_margin;

-- Para ver el margen total de una licitación específica
SELECT
  tender_id,
  SUM(total_margin) AS total_profit_for_tender
FROM
  public.order_details_with_margin
WHERE
  tender_id = '2306267-LE24' -- <-- Cambia por un ID de tu licitación
GROUP BY
  tender_id;