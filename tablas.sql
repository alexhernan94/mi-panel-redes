-- ============================================================
-- ESTRUCTURA DE TABLAS - Panel de Redes itsbgart
-- Base de datos: u764199979_rrss_analytics (Hostinger)
-- ============================================================

CREATE TABLE contenidos (
    id_contenido VARCHAR(100) NOT NULL,
    plataforma ENUM('instagram', 'tiktok', 'youtube') NOT NULL,
    estilo_visual ENUM('Post Foto', 'Carrusel', 'Reel', 'Story', 'Vídeo vertical', 'Vídeo largo', 'Short') NOT NULL DEFAULT 'Post Foto',
    duracion_segundos INT UNSIGNED DEFAULT NULL,
    titulo VARCHAR(255) DEFAULT 'Sin título',
    url VARCHAR(500),
    fecha_publicacion DATETIME NOT NULL,
    PRIMARY KEY (id_contenido),
    INDEX idx_plataforma (plataforma),
    INDEX idx_fecha (fecha_publicacion),
    INDEX idx_plataforma_fecha (plataforma, fecha_publicacion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 3. Añadir columna de duración en segundos a contenidos
ALTER TABLE contenidos 
ADD COLUMN duracion_segundos INT UNSIGNED DEFAULT NULL AFTER estilo_visual;

CREATE TABLE metricas_rendimiento (
    id_contenido VARCHAR(100) NOT NULL,
    fecha_registro DATE NOT NULL,
    visualizaciones INT UNSIGNED DEFAULT 0,
    likes INT UNSIGNED DEFAULT 0,
    compartidos INT UNSIGNED DEFAULT 0,
    guardados INT UNSIGNED DEFAULT 0,
    comentarios INT UNSIGNED DEFAULT 0,
    alcance INT UNSIGNED DEFAULT 0,
    PRIMARY KEY (id_contenido, fecha_registro),
    CONSTRAINT fk_metrica_contenido 
        FOREIGN KEY (id_contenido) REFERENCES contenidos(id_contenido) ON DELETE CASCADE,
    INDEX idx_fecha_registro (fecha_registro)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 1. Añadir columna de comentarios a metricas_rendimiento
ALTER TABLE metricas_rendimiento 
ADD COLUMN comentarios INT UNSIGNED DEFAULT 0 AFTER guardados;

-- 2. Añadir columna de alcance (reach) a metricas_rendimiento
ALTER TABLE metricas_rendimiento 
ADD COLUMN alcance INT UNSIGNED DEFAULT 0 AFTER comentarios;

CREATE TABLE insights_ia (
    id_insight INT AUTO_INCREMENT PRIMARY KEY,
    tendencias_actuales TEXT,
    analisis_rendimiento TEXT,
    ideas_contenido MEDIUMTEXT,
    fecha_generacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_fecha_gen (fecha_generacion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE seguidores_historico (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plataforma ENUM('instagram', 'tiktok', 'youtube') NOT NULL,
    seguidores INT UNSIGNED NOT NULL DEFAULT 0,
    fecha_registro DATE NOT NULL,
    UNIQUE INDEX idx_plat_fecha (plataforma, fecha_registro)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE configuracion (
    clave VARCHAR(100) NOT NULL,
    valor TEXT,
    PRIMARY KEY (clave)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS objetivos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plataforma ENUM('instagram', 'tiktok', 'youtube', 'global') NOT NULL,
    metrica VARCHAR(50) NOT NULL COMMENT 'seguidores, visualizaciones, engagement...',
    valor_actual INT UNSIGNED DEFAULT 0,
    valor_objetivo INT UNSIGNED NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_objetivo DATE NOT NULL,
    completado BOOLEAN DEFAULT FALSE,
    INDEX idx_plat_metrica (plataforma, metrica)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

