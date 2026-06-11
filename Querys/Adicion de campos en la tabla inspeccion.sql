USE rentcar_unapec;
-- Para poder llevar un registro de cada goma modifiqué la tabla
-- añadiendole mas campos: 
ALTER TABLE inspecciones 
    ADD COLUMN goma_delantera_izq VARCHAR(5) DEFAULT 'No',
    ADD COLUMN goma_delantera_der VARCHAR(5) DEFAULT 'No',
    ADD COLUMN goma_trasera_izq VARCHAR(5) DEFAULT 'No',
    ADD COLUMN goma_trasera_der VARCHAR(5) DEFAULT 'No';
    
    
----- Cambie estos tipos de datos a varchar para poder almacenarlos de forma mas comoda como checklist en el crud
ALTER TABLE inspecciones 
    MODIFY COLUMN tiene_ralladuras VARCHAR(5) DEFAULT 'No',
    MODIFY COLUMN tiene_goma_repuesta VARCHAR(5) DEFAULT 'No',
    MODIFY COLUMN tiene_gato VARCHAR(5) DEFAULT 'No',
    MODIFY COLUMN tiene_roturas_cristal VARCHAR(5) DEFAULT 'No';