-- supabase/migrations/0001_initial_schema.sql

-- 1. Create a table for RERs
CREATE TABLE rers (
    id INTEGER PRIMARY KEY,
    nombre_rer VARCHAR(100) NOT NULL
);

-- 2. Create the function to update the updated_at column
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 3. Create the table for educational institutions
CREATE TABLE instituciones_educativas (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    codigo_modular VARCHAR(10) UNIQUE NOT NULL,
    nombre_ie VARCHAR(200) NOT NULL,
    rer_id INTEGER REFERENCES rers(id) NOT NULL,
    
    -- INDICADORES CONTEXTUALES BASE
    tipo_ruralidad INTEGER CHECK (tipo_ruralidad IN (1,2,3)), 
    -- 1=Urbano, 2=Rural accesible, 3=Rural disperso
    nbi_distrito DECIMAL(5,2), -- Necesidades Básicas Insatisfechas del distrito
    modalidad_eib INTEGER DEFAULT 0 CHECK (modalidad_eib IN (0,1,2)),
    -- 0=No EIB, 1=EIB fortalecimiento, 2=EIB revitalización
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Add the trigger to the table
CREATE TRIGGER set_timestamp
BEFORE UPDATE ON instituciones_educativas
FOR EACH ROW
EXECUTE PROCEDURE trigger_set_timestamp();

-- 4. Create the table for academic indicators
CREATE TABLE indicadores_academicos_base (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    codigo_modular VARCHAR(10) REFERENCES instituciones_educativas(codigo_modular),
    año INTEGER NOT NULL,
    
    -- INDICADORES BASE ACADÉMICOS
    promedio_notas_matematica DECIMAL(4,2) CHECK (promedio_notas_matematica BETWEEN 0 AND 20),
    promedio_notas_comunicacion DECIMAL(4,2) CHECK (promedio_notas_comunicacion BETWEEN 0 AND 20),
    total_estudiantes_evaluados INTEGER,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(codigo_modular, año)
);

-- Add the trigger to the table
CREATE TRIGGER set_timestamp
BEFORE UPDATE ON indicadores_academicos_base
FOR EACH ROW
EXECUTE PROCEDURE trigger_set_timestamp();


-- 5. Create the table for teacher indicators
CREATE TABLE indicadores_docentes_base (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    codigo_modular VARCHAR(10) REFERENCES instituciones_educativas(codigo_modular),
    año INTEGER NOT NULL,
    
    -- INDICADORES BASE DOCENTES
    total_docentes INTEGER NOT NULL,
    docentes_nombrados INTEGER DEFAULT 0,
    promedio_años_servicio_red DECIMAL(4,1),
    promedio_padd_iiee DECIMAL(3,2) CHECK (promedio_padd_iiee BETWEEN 1 AND 4),
    promedio_competencia_digital DECIMAL(3,2) CHECK (promedio_competencia_digital BETWEEN 1 AND 4),
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(codigo_modular, año)
);

-- Add the trigger to the table
CREATE TRIGGER set_timestamp
BEFORE UPDATE ON indicadores_docentes_base
FOR EACH ROW
EXECUTE PROCEDURE trigger_set_timestamp();

-- 6. Create the table for infrastructure indicators
CREATE TABLE indicadores_infraestructura_base (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    codigo_modular VARCHAR(10) REFERENCES instituciones_educativas(codigo_modular),
    año INTEGER NOT NULL,
    
    -- INDICADORES BASE INFRAESTRUCTURA
    servicios_basicos_puntaje DECIMAL(3,2) CHECK (servicios_basicos_puntaje BETWEEN 0 AND 1),
    estado_mobiliario_puntaje DECIMAL(3,2) CHECK (estado_mobiliario_puntaje BETWEEN 0 AND 1),
    tiene_biblioteca BOOLEAN DEFAULT FALSE,
    tipo_organizacion_escolar INTEGER CHECK (tipo_organizacion_escolar IN (1,2,3)),
    -- 1=Polidocente completo, 2=Multigrado, 3=Unidocente
    total_estudiantes INTEGER,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(codigo_modular, año)
);

-- Add the trigger to the table
CREATE TRIGGER set_timestamp
BEFORE UPDATE ON indicadores_infraestructura_base
FOR EACH ROW
EXECUTE PROCEDURE trigger_set_timestamp();

-- 7. Create the views for composite variables

CREATE VIEW variables_dependientes AS
SELECT 
    ia.codigo_modular,
    ia.año,
    
    -- Y1: ÍNDICE DE LOGRO ACADÉMICO (ILA)
    ROUND((ia.promedio_notas_matematica + ia.promedio_notas_comunicacion) / 2, 2) as ila_indice_logro_academico,
    
    -- Y2: TENDENCIA DE DESEMPEÑO (TD) - Se calcula con datos de múltiples años
    ROUND(
        (LEAD(((ia.promedio_notas_matematica + ia.promedio_notas_comunicacion) / 2)) OVER (PARTITION BY ia.codigo_modular ORDER BY ia.año) - 
         ((ia.promedio_notas_matematica + ia.promedio_notas_comunicacion) / 2)) / 
        NULLIF(((ia.promedio_notas_matematica + ia.promedio_notas_comunicacion) / 2), 0), 4
    ) as td_tendencia_desempeño
    
FROM indicadores_academicos_base ia;

CREATE VIEW variables_independientes_contexto AS
SELECT 
    ie.codigo_modular,
    
    -- X1: NIVEL DE VULNERABILIDAD CONTEXTUAL (NVC)
    ROUND(
        (ie.nbi_distrito * 0.4) + 
        (CASE ie.tipo_ruralidad 
            WHEN 1 THEN 0.0    -- Urbano
            WHEN 2 THEN 0.5    -- Rural accesible  
            WHEN 3 THEN 1.0    -- Rural disperso
        END * 0.3) + 
        ((1 - ib.servicios_basicos_puntaje) * 0.3), 2
    ) as nvc_vulnerabilidad_contextual,
    
    -- X2: TIPO DE RURALIDAD (TR) - Variable simple
    ie.tipo_ruralidad as tr_tipo_ruralidad
    
FROM instituciones_educativas ie
JOIN indicadores_infraestructura_base ib ON ie.codigo_modular = ib.codigo_modular;

CREATE VIEW variables_independientes_docentes AS
SELECT 
    id.codigo_modular,
    id.año,
    
    -- X4: ÍNDICE DE DESEMPEÑO DOCENTE (IDD) - Variable simple
    id.promedio_padd_iiee as idd_desempeño_docente,
    
    -- X5: ESTABILIDAD DOCENTE (ED)
    ROUND(
        (CAST(id.docentes_nombrados AS DECIMAL) / NULLIF(id.total_docentes, 0) * 0.5) + 
        (LEAST(id.promedio_años_servicio_red / 10.0, 1.0) * 0.5), 2
    ) as ed_estabilidad_docente,
    
    -- X6: COMPETENCIA DIGITAL DOCENTE (CDD) - Variable simple
    id.promedio_competencia_digital as cdd_competencia_digital
    
FROM indicadores_docentes_base id;

CREATE VIEW variables_independientes_recursos AS
SELECT 
    ib.codigo_modular,
    ib.año,
    
    -- X10: INFRAESTRUCTURA EDUCATIVA (IE)
    ROUND(
        (ib.servicios_basicos_puntaje * 0.4) + 
        (ib.estado_mobiliario_puntaje * 0.3) + 
        (CASE WHEN ib.tiene_biblioteca THEN 1.0 ELSE 0.0 END * 0.3), 2
    ) as ie_infraestructura_educativa,
    
    -- X11: RATIO ESTUDIANTE-DOCENTE (RED)
    ROUND(
        CAST(ib.total_estudiantes AS DECIMAL) / NULLIF(id.total_docentes, 0), 1
    ) as red_ratio_estudiante_docente,
    
    -- X12: TIPO DE ORGANIZACIÓN ESCOLAR (TOE) - Variable simple
    ib.tipo_organizacion_escolar as toe_tipo_organizacion
    
FROM indicadores_infraestructura_base ib
JOIN indicadores_docentes_base id ON ib.codigo_modular = id.codigo_modular AND ib.año = id.año;
