USE rentcar_unapec;

CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    correo VARCHAR(100) UNIQUE NOT NULL,
    clave VARCHAR(255) NOT NULL,
    estado VARCHAR(20) DEFAULT 'Activo'
);

-- Se inserta un primer usuario administrador de pruebas
INSERT INTO usuarios (nombre, correo, clave, estado) 
VALUES ('Administrador', 'admin@rentcar.com', 'admin123', 'Activo')
ON DUPLICATE KEY UPDATE id_usuario=id_usuario;

select * from usuarios
