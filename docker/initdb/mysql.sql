-- Esquema de teste usado pelos testes de integracao.
-- Cobre chave estrangeira, tipos variados e nome de tabela com underscore
-- (que exercita a conversao CamelCase -> rota kebab-case).
CREATE TABLE customer (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(200) NOT NULL,
    active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NULL
);

CREATE TABLE order_item (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sku VARCHAR(50) NOT NULL,
    qty INT NOT NULL DEFAULT 1,
    price DECIMAL(10, 2) NULL,
    customer_id INT NULL,
    CONSTRAINT fk_order_item_customer FOREIGN KEY (customer_id) REFERENCES customer (id)
);

INSERT INTO customer (email, active) VALUES ('ana@example.com', 1), ('bruno@example.com', 0);
INSERT INTO order_item (sku, qty, price, customer_id) VALUES ('SKU-1', 2, 9.99, 1);
