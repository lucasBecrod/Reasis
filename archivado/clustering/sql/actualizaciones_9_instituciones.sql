-- Actualizaciones para las 9 instituciones integradas recientemente
-- Se unifican múltiples sentencias UPDATE en una sola para mayor eficiencia.


UPDATE instituciones_educativas 
SET es_eib = 0
WHERE codigo_modular IN (
    '0600692', 
    '1768829', 
    '0481093', 
    '0488403', 
    '0304642', 
    '0428714', 
    '3025715', 
    '2533906', 
    '1781897'
);