USE rentcar_unapec;

-- Se insertan datos para poder trabajar las tablas ya que  estoy trabajando con database first

-- marcas
INSERT INTO marcas (descripcion) VALUES ('Toyota'), ('Honda'), ('Hyundai'), ('Kia');

-- modelos
INSERT INTO modelos (id_marca, descripcion) VALUES 
(1, 'Corolla'), (1, 'RAV4'),
(2, 'Civic'), (2, 'CR-V'),
(3, 'Elantra'), (3, 'Tucson'),
(4, 'K5'), (4, 'Sportage');

--  tipos de vehículos
INSERT INTO tipos_vehiculos (descripcion) VALUES ('Sedán'), ('Jeepeta'), ('Camioneta'), ('Compacto');

-- tipos de combustibles
INSERT INTO tipos_combustible (descripcion) VALUES ('Gasolina'), ('Gasoil (Diesel)'), ('GLP'), ('Híbrido/Eléctrico');



