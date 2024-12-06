CREATE TABLE item_statuses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);


INSERT INTO item_statuses (name) VALUES
('Active'),
('Not Active'),
('Traded');