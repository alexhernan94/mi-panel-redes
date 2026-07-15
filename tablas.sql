-- ============================================================
-- ESTRUCTURA DE TABLAS - Panel de Redes itsbgart
-- Base de datos: u764199979_rrss_analytics (Hostinger)
-- ============================================================

CREATE TABLE contenidos (
    id_contenido VARCHAR(100) NOT NULL,
    plataforma ENUM('instagram', 'tiktok', 'youtube') NOT NULL,
    estilo_visual ENUM('Post Foto', 'Carrusel', 'Reel', 'Story', 'Vídeo vertical', 'Vídeo largo', 'Short') NOT NULL DEFAULT 'Post Foto',
    titulo VARCHAR(255) DEFAULT 'Sin título',
    url VARCHAR(500),
    fecha_publicacion DATETIME NOT NULL,
    PRIMARY KEY (id_contenido),
    INDEX idx_plataforma (plataforma),
    INDEX idx_fecha (fecha_publicacion),
    INDEX idx_plataforma_fecha (plataforma, fecha_publicacion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE metricas_rendimiento (
    id_contenido VARCHAR(100) NOT NULL,
    fecha_registro DATE NOT NULL,
    visualizaciones INT UNSIGNED DEFAULT 0,
    likes INT UNSIGNED DEFAULT 0,
    compartidos INT UNSIGNED DEFAULT 0,
    guardados INT UNSIGNED DEFAULT 0,
    PRIMARY KEY (id_contenido, fecha_registro),
    CONSTRAINT fk_metrica_contenido 
        FOREIGN KEY (id_contenido) REFERENCES contenidos(id_contenido) ON DELETE CASCADE,
    INDEX idx_fecha_registro (fecha_registro)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE insights_ia (
    id_insight INT AUTO_INCREMENT PRIMARY KEY,
    tendencias_actuales TEXT,
    analisis_rendimiento TEXT,
    ideas_contenido MEDIUMTEXT,
    fecha_generacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_fecha_gen (fecha_generacion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
