-- Esquema opcional (usa public por defecto)
-- CREATE SCHEMA IF NOT EXISTS kaiken;

-- CLIENTES
CREATE TABLE IF NOT EXISTS public.clientes (
  id_cli      integer PRIMARY KEY,
  rut_cli     text,
  nom_cli     text,
  dir_cli     text,
  tel_cli     text,
  cor_cli     text,
  con_cli     text
);

-- PRODUCTS (desde product_sample_clean.csv)
CREATE TABLE IF NOT EXISTS public.products (
  sku_pro     text PRIMARY KEY,              -- PK (antes sku)
  row_number  integer,
  nom_pro     text,
  desc_pro    text,
  cost_prp    numeric(12,2),
  stock       integer,
  cre_pro     date,
  upd_pro     date
);

-- TENDERS (desde tender_sample_clean.csv)
CREATE TABLE IF NOT EXISTS public.tenders (
  id              text PRIMARY KEY,          -- ej: 2306267-LE24
  row_number      integer,
  id_cli          integer REFERENCES public.clientes(id_cli) ON UPDATE CASCADE ON DELETE SET NULL,
  creation_date   date,
  delivery_date   date,
  margin          numeric(6,3)               -- 0.4 etc.
);

-- ORDERS (desde order_sample_clean.csv)
CREATE TABLE IF NOT EXISTS public.orders (
  id          text PRIMARY KEY,              -- tender_id + '-' + product_id
  row_number  integer,
  tender_id   text REFERENCES public.tenders(id) ON UPDATE CASCADE ON DELETE CASCADE,
  product_id  text REFERENCES public.products(sku_pro) ON UPDATE CASCADE,
  quantity    integer,
  price       numeric(12,2),
  observation text
);

-- Índices útiles
CREATE INDEX IF NOT EXISTS idx_tenders_id_cli    ON public.tenders(id_cli);
CREATE INDEX IF NOT EXISTS idx_orders_tender_id  ON public.orders(tender_id);
CREATE INDEX IF NOT EXISTS idx_orders_product_id ON public.orders(product_id);
