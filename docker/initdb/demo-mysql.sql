-- Banco de demonstracao do robot_rest.
-- Gerado para exercitar a ferramenta: chaves estrangeiras, tabela de
-- juncao N:N, tipos variados e linhas suficientes para ver a paginacao
-- da API (PAGE_SIZE padrao = 10).

CREATE TABLE category (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(80) NOT NULL UNIQUE,
    slug VARCHAR(80) NOT NULL,
    description TEXT NULL
);

CREATE TABLE product (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    sku VARCHAR(32) NOT NULL UNIQUE,
    name VARCHAR(160) NOT NULL,
    description TEXT NULL,
    price DECIMAL(10, 2) NOT NULL,
    weight_kg DECIMAL(6, 3) NULL,
    in_stock INT NOT NULL DEFAULT 0,
    active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL,
    CONSTRAINT fk_product_category FOREIGN KEY (category_id) REFERENCES category (id)
);

CREATE TABLE customer (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(200) NOT NULL UNIQUE,
    phone VARCHAR(30) NULL,
    birth_date DATE NULL,
    newsletter TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL
);

CREATE TABLE customer_address (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    label VARCHAR(40) NOT NULL,
    street VARCHAR(200) NOT NULL,
    city VARCHAR(80) NOT NULL,
    state CHAR(2) NOT NULL,
    postal_code VARCHAR(12) NOT NULL,
    is_default TINYINT(1) NOT NULL DEFAULT 0,
    CONSTRAINT fk_address_customer FOREIGN KEY (customer_id) REFERENCES customer (id)
);

-- 'order' e palavra reservada no MySQL; o nome composto tambem mostra a
-- conversao CamelCase -> rota kebab-case (customer_order -> /v1/customer-order/).
CREATE TABLE customer_order (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    shipping_address_id INT NULL,
    status VARCHAR(20) NOT NULL,
    total DECIMAL(10, 2) NOT NULL,
    placed_at DATETIME NOT NULL,
    shipped_at DATETIME NULL,
    CONSTRAINT fk_order_customer FOREIGN KEY (customer_id) REFERENCES customer (id),
    CONSTRAINT fk_order_address FOREIGN KEY (shipping_address_id) REFERENCES customer_address (id)
);

CREATE TABLE order_item (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    unit_price DECIMAL(10, 2) NOT NULL,
    CONSTRAINT fk_item_order FOREIGN KEY (order_id) REFERENCES customer_order (id),
    CONSTRAINT fk_item_product FOREIGN KEY (product_id) REFERENCES product (id)
);

CREATE TABLE tag (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(40) NOT NULL UNIQUE
);

-- Juncao N:N entre product e tag.
CREATE TABLE product_tag (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    tag_id INT NOT NULL,
    UNIQUE KEY uniq_product_tag (product_id, tag_id),
    CONSTRAINT fk_pt_product FOREIGN KEY (product_id) REFERENCES product (id),
    CONSTRAINT fk_pt_tag FOREIGN KEY (tag_id) REFERENCES tag (id)
);

INSERT INTO category (name, slug, description) VALUES
    ('Notebooks', 'notebooks', 'Notebooks e ultrabooks'),
    ('Perifericos', 'perifericos', 'Teclados, mouses e headsets'),
    ('Monitores', 'monitores', 'Monitores e suportes'),
    ('Armazenamento', 'armazenamento', 'SSDs, HDs e cartoes'),
    ('Redes', 'redes', 'Roteadores, switches e cabos'),
    ('Acessorios', 'acessorios', 'Cabos, adaptadores e capas');

INSERT INTO product (category_id, sku, name, price, weight_kg, in_stock, active, created_at) VALUES
    (1, 'SKU-0001', 'Notebook Pro 14', 8499.00, 1.290, 23, 1, '2026-02-12 09:01:00'),
    (1, 'SKU-0002', 'Notebook Air 13', 6299.00, 1.050, 97, 1, '2026-03-23 09:02:00'),
    (1, 'SKU-0003', 'Notebook Gamer 15', 11250.50, 2.400, 7, 1, '2026-04-07 09:03:00'),
    (1, 'SKU-0004', 'Ultrabook Slim 14', 7150.00, 1.180, 25, 1, '2026-05-18 09:04:00'),
    (2, 'SKU-0005', 'Teclado Mecanico ABNT2', 459.90, 0.980, 126, 1, '2026-06-02 09:05:00'),
    (2, 'SKU-0006', 'Mouse Vertical Ergonomico', 289.90, 0.135, 126, 1, '2026-01-13 09:06:00'),
    (2, 'SKU-0007', 'Headset Estereo USB', 349.00, 0.310, 133, 1, '2026-02-24 09:07:00'),
    (2, 'SKU-0008', 'Mousepad Extra Grande', 129.90, 0.420, 30, 1, '2026-03-08 09:08:00'),
    (2, 'SKU-0009', 'Webcam Full HD', 399.00, 0.180, 52, 1, '2026-04-19 09:09:00'),
    (2, 'SKU-0010', 'Teclado Compacto 60%', 529.00, 0.610, 89, 1, '2026-05-03 09:10:00'),
    (3, 'SKU-0011', 'Monitor 27 QHD', 2199.00, 5.200, 91, 1, '2026-06-14 09:11:00'),
    (3, 'SKU-0012', 'Monitor 24 Full HD', 1099.00, 3.800, 49, 1, '2026-01-25 09:12:00'),
    (3, 'SKU-0013', 'Monitor Ultrawide 34', 4599.00, 7.900, 99, 1, '2026-02-09 09:13:00'),
    (3, 'SKU-0014', 'Suporte Articulado Duplo', 389.00, 2.100, 26, 1, '2026-03-20 09:14:00'),
    (4, 'SKU-0015', 'SSD NVMe 1TB', 649.00, 0.010, 90, 1, '2026-04-04 09:15:00'),
    (4, 'SKU-0016', 'SSD NVMe 2TB', 1189.00, 0.012, 39, 1, '2026-05-15 09:16:00'),
    (4, 'SKU-0017', 'HD Externo 4TB', 899.00, 0.230, 80, 1, '2026-06-26 09:17:00'),
    (4, 'SKU-0018', 'Cartao SD 256GB', 219.90, 0.005, 133, 1, '2026-01-10 09:18:00'),
    (5, 'SKU-0019', 'Roteador Wi-Fi 6', 799.00, 0.640, 10, 1, '2026-02-21 09:19:00'),
    (5, 'SKU-0020', 'Switch 8 Portas Gigabit', 349.00, 0.520, 44, 1, '2026-03-05 09:20:00'),
    (5, 'SKU-0021', 'Cabo de Rede Cat6 5m', 49.90, 0.190, 130, 1, '2026-04-16 09:21:00'),
    (5, 'SKU-0022', 'Repetidor Mesh', 559.00, 0.410, 71, 1, '2026-05-27 09:22:00'),
    (6, 'SKU-0023', 'Hub USB-C 7 em 1', 329.00, 0.145, 67, 1, '2026-06-11 09:23:00'),
    (6, 'SKU-0024', 'Capa para Notebook 14', 159.90, 0.260, 107, 1, '2026-01-22 09:24:00'),
    (6, 'SKU-0025', 'Suporte para Notebook', 199.00, 0.880, 53, 1, '2026-02-06 09:25:00');

INSERT INTO customer (full_name, email, phone, birth_date, newsletter, created_at) VALUES
    ('Ana Ribeiro', 'ana.ribeiro@example.com', '11 98800-1010', '1988-03-12', 1, '2025-02-04 14:05:00'),
    ('Bruno Carvalho', 'bruno.carvalho@example.com', '21 99120-2211', '1992-11-05', 0, '2025-03-07 14:10:00'),
    ('Carla Menezes', 'carla.menezes@example.com', '31 98411-3322', '1979-07-23', 1, '2025-04-10 14:15:00'),
    ('Diego Nunes', 'diego.nunes@example.com', '41 99733-4455', '1995-01-30', 1, '2025-05-13 14:20:00'),
    ('Elisa Prado', 'elisa.prado@example.com', '51 98222-5566', '1983-09-17', 0, '2025-06-16 14:25:00'),
    ('Fabio Toledo', 'fabio.toledo@example.com', '61 99655-6677', '1990-05-02', 1, '2025-07-19 14:30:00'),
    ('Gabriela Lima', 'gabriela.lima@example.com', '71 98344-7788', '1986-12-19', 0, '2025-08-22 14:35:00'),
    ('Henrique Sa', 'henrique.sa@example.com', '81 99577-8899', '1998-08-08', 1, '2025-09-25 14:40:00'),
    ('Isabel Rocha', 'isabel.rocha@example.com', '85 98466-9900', '1975-04-26', 1, '2025-10-01 14:45:00'),
    ('Joao Pedro Alves', 'joao.alves@example.com', '48 99388-0011', '1993-02-14', 0, '2025-11-04 14:50:00'),
    ('Karina Duarte', 'karina.duarte@example.com', '62 98299-1122', '1981-10-09', 1, '2025-12-07 14:55:00'),
    ('Lucas Ferreira', 'lucas.ferreira@example.com', '27 99411-2233', '2000-06-21', 1, '2025-01-10 14:00:00');

INSERT INTO customer_address (customer_id, label, street, city, state, postal_code, is_default) VALUES
    (1, 'Casa', 'Rua B 108', 'Belo Horizonte', 'MG', '30130-010', 1),
    (1, 'Trabalho', 'Rua C 109', 'Curitiba', 'PR', '80010-010', 0),
    (2, 'Casa', 'Rua C 115', 'Curitiba', 'PR', '80010-010', 1),
    (3, 'Casa', 'Rua D 122', 'Porto Alegre', 'RS', '90010-150', 1),
    (4, 'Casa', 'Rua E 129', 'Brasilia', 'DF', '70040-010', 1),
    (5, 'Casa', 'Rua F 136', 'Salvador', 'BA', '40020-000', 1),
    (6, 'Casa', 'Rua G 143', 'Recife', 'PE', '50030-230', 1),
    (7, 'Casa', 'Rua H 150', 'Sao Paulo', 'SP', '01310-100', 1),
    (8, 'Casa', 'Rua I 157', 'Rio de Janeiro', 'RJ', '22071-900', 1),
    (8, 'Trabalho', 'Rua Q 158', 'Belo Horizonte', 'MG', '30130-010', 0),
    (9, 'Casa', 'Rua J 164', 'Belo Horizonte', 'MG', '30130-010', 1),
    (10, 'Casa', 'Rua K 171', 'Curitiba', 'PR', '80010-010', 1),
    (11, 'Casa', 'Rua L 178', 'Porto Alegre', 'RS', '90010-150', 1),
    (12, 'Casa', 'Rua M 185', 'Brasilia', 'DF', '70040-010', 1),
    (12, 'Trabalho', 'Rua Y 186', 'Salvador', 'BA', '40020-000', 0);

INSERT INTO tag (name) VALUES
    ('promocao'),
    ('lancamento'),
    ('mais-vendido'),
    ('importado'),
    ('gamer'),
    ('home-office'),
    ('ultima-unidade'),
    ('frete-gratis');

INSERT INTO product_tag (product_id, tag_id) VALUES
    (1, 2),
    (2, 1),
    (2, 7),
    (2, 8),
    (3, 4),
    (4, 8),
    (5, 2),
    (5, 3),
    (5, 7),
    (6, 1),
    (6, 4),
    (6, 5),
    (7, 2),
    (7, 4),
    (7, 6),
    (8, 1),
    (8, 2),
    (8, 6),
    (9, 4),
    (10, 1),
    (10, 4),
    (11, 2),
    (11, 5),
    (11, 7),
    (12, 3),
    (12, 4),
    (13, 7),
    (14, 1),
    (14, 2),
    (14, 7),
    (15, 2),
    (15, 4),
    (16, 1),
    (16, 6),
    (17, 1),
    (17, 4),
    (18, 3),
    (18, 5),
    (18, 8),
    (19, 3),
    (19, 6),
    (19, 7),
    (20, 8),
    (21, 4),
    (21, 7),
    (22, 4),
    (22, 6),
    (22, 8),
    (23, 8),
    (24, 3),
    (25, 5),
    (25, 7);

INSERT INTO customer_order (customer_id, shipping_address_id, status, total, placed_at, shipped_at) VALUES
    (6, 4, 'pago', 1047.00, '2026-02-03 11:30:00', NULL),
    (11, 7, 'separacao', 868.70, '2026-03-05 12:30:00', '2026-03-06 08:15:00'),
    (4, 10, 'enviado', 1935.70, '2026-04-07 13:30:00', '2026-04-08 08:15:00'),
    (9, 13, 'entregue', 5511.00, '2026-05-09 14:30:00', '2026-05-10 08:15:00'),
    (2, 1, 'cancelado', 2193.70, '2026-06-11 15:30:00', NULL),
    (7, 4, 'novo', 698.00, '2026-07-13 16:30:00', NULL),
    (12, 7, 'pago', 1189.00, '2026-01-15 17:30:00', NULL),
    (5, 10, 'separacao', 1598.00, '2026-02-17 18:30:00', '2026-02-18 08:15:00'),
    (10, 13, 'enviado', 3996.00, '2026-03-19 19:30:00', '2026-03-20 08:15:00'),
    (3, 1, 'entregue', 6354.00, '2026-04-21 10:30:00', '2026-04-22 08:15:00'),
    (8, 4, 'cancelado', 24506.90, '2026-05-23 11:30:00', NULL),
    (1, 7, 'novo', 8105.80, '2026-06-25 12:30:00', NULL),
    (6, 10, 'pago', 1118.00, '2026-07-27 13:30:00', NULL),
    (11, 13, 'separacao', 34847.00, '2026-01-02 14:30:00', '2026-01-04 08:15:00'),
    (4, 1, 'enviado', 658.00, '2026-02-04 15:30:00', '2026-02-06 08:15:00'),
    (9, 4, 'entregue', 6498.00, '2026-03-06 16:30:00', '2026-03-08 08:15:00'),
    (2, 7, 'cancelado', 6597.00, '2026-04-08 17:30:00', NULL),
    (7, 10, 'novo', 28744.70, '2026-05-10 18:30:00', NULL);

INSERT INTO order_item (order_id, product_id, quantity, unit_price) VALUES
    (1, 7, 3, 349.00),
    (2, 18, 1, 219.90),
    (2, 23, 1, 329.00),
    (2, 24, 2, 159.90),
    (3, 9, 3, 399.00),
    (3, 7, 1, 349.00),
    (3, 8, 3, 129.90),
    (4, 7, 3, 349.00),
    (4, 16, 3, 1189.00),
    (4, 25, 1, 199.00),
    (4, 20, 2, 349.00),
    (5, 25, 1, 199.00),
    (5, 21, 3, 49.90),
    (5, 9, 2, 399.00),
    (5, 20, 3, 349.00),
    (6, 7, 2, 349.00),
    (7, 16, 1, 1189.00),
    (8, 19, 2, 799.00),
    (9, 12, 2, 1099.00),
    (9, 17, 2, 899.00),
    (10, 11, 2, 2199.00),
    (10, 15, 2, 649.00),
    (10, 23, 2, 329.00),
    (11, 23, 3, 329.00),
    (11, 5, 1, 459.90),
    (11, 3, 2, 11250.50),
    (11, 22, 1, 559.00),
    (12, 24, 2, 159.90),
    (12, 16, 1, 1189.00),
    (12, 11, 3, 2199.00),
    (13, 22, 2, 559.00),
    (14, 4, 3, 7150.00),
    (14, 2, 2, 6299.00),
    (14, 19, 1, 799.00),
    (15, 23, 2, 329.00),
    (16, 25, 1, 199.00),
    (16, 2, 1, 6299.00),
    (17, 11, 3, 2199.00),
    (18, 6, 3, 289.90),
    (18, 1, 3, 8499.00),
    (18, 16, 2, 1189.00);

