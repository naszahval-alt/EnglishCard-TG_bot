CREATE TABLE Words (
id SERIAl PRIMARY KEY,
english_word VARCHAR (50) NOT NULL,
russian_translation VARCHAR (50) NOT NULL,
word_type VARCHAR(20)
);

-- Добавляем слова в таблицу Words
INSERT INTO Words (english_word, russian_translation, word_type) VALUES
('Peace', 'Мир', 'noun'),
('Green', 'Зелёный', 'adjective'),
('White', 'Белый', 'adjective'),
('Hello', 'Привет', 'greeting'),
('Car', 'Машина', 'noun'),
('House', 'Дом', 'noun'),
('Book', 'Книга', 'noun'),
('Water', 'Вода', 'noun'),
('Sun', 'Солнце', 'noun'),
('Tree', 'Дерево', 'noun');


CREATE TABLE Users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(100),
    step INT NOT NULL DEFAULT 0,
    target_word VARCHAR(100),
    translate_word VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);


CREATE TABLE UserWords (
id SERIAL PRIMARY KEY,
user_id BIGINT REFERENCES Users(user_id),
english_word VARCHAR(50) NOT NULL,
russian_translation VARCHAR (50) NOT NULL
);

