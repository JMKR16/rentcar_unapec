USE rentcar_unapec;

--  Tipos de Vehículos (Automóvil, Camioneta, etc.)
CREATE TABLE tipos_vehiculos (
    id_tipo_vehiculo INT AUTO_INCREMENT PRIMARY KEY,
    descripcion VARCHAR(100) NOT NULL,
    estado VARCHAR(20) DEFAULT 'Activo'
);

--  Tipos de Combustible (Gasolina, Gasoil, etc.)
CREATE TABLE tipos_combustible (
    id_combustible INT AUTO_INCREMENT PRIMARY KEY,
    descripcion VARCHAR(100) NOT NULL,
    estado VARCHAR(20) DEFAULT 'Activo'
);

--  Modelos (Corolla, Civic, etc.)
CREATE TABLE modelos (
    id_modelo INT AUTO_INCREMENT PRIMARY KEY,
    id_marca INT NOT NULL, -- Conecta el modelo a una marca (Ej: Corolla pertenece a Toyota)
    descripcion VARCHAR(100) NOT NULL,
    estado VARCHAR(20) DEFAULT 'Activo',
    FOREIGN KEY (id_marca) REFERENCES marcas(id_marca)
);

--  Inspección (Requerimiento obligatorio antes de rentar)
CREATE TABLE inspecciones (
    id_inspeccion INT AUTO_INCREMENT PRIMARY KEY,
    id_vehiculo INT NOT NULL,
    id_cliente INT NOT NULL,
    tiene_ralladuras BOOLEAN DEFAULT FALSE,
    cantidad_combustible VARCHAR(20) NOT NULL, -- '1/4', '1/2', '3/4', 'Lleno'
    tiene_goma_repuesta BOOLEAN DEFAULT FALSE,
    tiene_gato BOOLEAN DEFAULT FALSE,
    tiene_roturas_cristal BOOLEAN DEFAULT FALSE,
    fecha DATE NOT NULL,
    id_empleado_inspeccion INT NOT NULL,
    estado VARCHAR(20) DEFAULT 'Completada',
    FOREIGN KEY (id_vehiculo) REFERENCES vehiculos(id_vehiculo),
    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente),
    FOREIGN KEY (id_empleado_inspeccion) REFERENCES empleados(id_empleado)
);