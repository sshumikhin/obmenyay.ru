CREATE TABLE item_trade_statuses (
    id SERIAL PRIMARY KEY,
    status_name VARCHAR(50) NOT NULL UNIQUE
);

INSERT INTO item_trade_statuses (status_name) VALUES
('Waiting'),
('Completed'),
('Canceled');