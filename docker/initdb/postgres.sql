-- Mesmo esquema do MySQL, para que os testes de integracao possam afirmar
-- que as duas engines produzem os mesmos modelos e rotas.
CREATE TABLE customer (
    id SERIAL PRIMARY KEY,
    email VARCHAR(200) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NULL
);

CREATE TABLE order_item (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(50) NOT NULL,
    qty INTEGER NOT NULL DEFAULT 1,
    price NUMERIC(10, 2) NULL,
    customer_id INTEGER NULL REFERENCES customer (id)
);

INSERT INTO customer (email, active) VALUES ('ana@example.com', TRUE), ('bruno@example.com', FALSE);
INSERT INTO order_item (sku, qty, price, customer_id) VALUES ('SKU-1', 2, 9.99, 1);
