-- STEP 1: Crear la función que valida el RUT Chileno 
CREATE OR REPLACE FUNCTION public.validar_rut_chileno(rut TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    rut_limpio TEXT;
    cuerpo TEXT;
    dv_ingresado CHAR(1);
    suma INT := 0;
    multiplo INT := 2;
    digito INT;
    dv_calculado INT;
    dv_esperado CHAR(1);
BEGIN
    -- Limpiar y validar formato básico
    rut_limpio := UPPER(regexp_replace(rut, '[.-]', '', 'g'));
    IF rut_limpio ~ '^[0-9]+[0-9K]$' AND LENGTH(rut_limpio) BETWEEN 8 AND 9 THEN
        cuerpo := SUBSTRING(rut_limpio FROM 1 FOR LENGTH(rut_limpio) - 1);
        dv_ingresado := SUBSTRING(rut_limpio FROM LENGTH(rut_limpio));

        -- Calcular suma para el dígito verificador
        FOR i IN REVERSE LENGTH(cuerpo)..1 LOOP
            digito := SUBSTRING(cuerpo FROM i FOR 1)::INT;
            suma := suma + (digito * multiplo);
            multiplo := CASE WHEN multiplo = 7 THEN 2 ELSE multiplo + 1 END;
        END LOOP;

        -- Calcular dígito verificador esperado
        dv_calculado := 11 - (suma % 11);
        dv_esperado := CASE
            WHEN dv_calculado = 11 THEN '0'
            WHEN dv_calculado = 10 THEN 'K'
            ELSE dv_calculado::TEXT
        END;

        -- Comparar y devolver resultado
        RETURN dv_ingresado = dv_esperado;
    ELSE
        RETURN FALSE; -- Formato incorrecto
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;


-- STEP 2: Aplicar la función como una restricción CHECK en la tabla clientes
-- Primero, eliminamos la restricción si ya existe para evitar errores
ALTER TABLE public.clientes DROP CONSTRAINT IF EXISTS chk_rut_valido;

-- Ahora, añadimos la nueva restricción que usa la función
ALTER TABLE public.clientes
ADD CONSTRAINT chk_rut_valido
CHECK (public.validar_rut_chileno(rut_cli));