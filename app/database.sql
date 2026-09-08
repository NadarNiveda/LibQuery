-- =============================================================
-- LibQuery: Database creation and sample data script
-- =============================================================
-- How to run:
--   1. Open MySQL Workbench or the mysql command-line client.
--   2. Run this entire file (or copy-paste it) to create the
--      library_db database with sample data.
--
--   Command line example:
--     mysql -u root -p < create_database.sql
-- =============================================================

-- Create the database (drop first only if you want a clean slate)
CREATE DATABASE IF NOT EXISTS library_db;
USE library_db;

-- -------------------------------------------------------------
-- Table: categories
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    category_id   INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL
);

-- -------------------------------------------------------------
-- Table: books
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS books (
    book_id           INT AUTO_INCREMENT PRIMARY KEY,
    title             VARCHAR(200) NOT NULL,
    author            VARCHAR(150) NOT NULL,
    category_id       INT,
    isbn              VARCHAR(20),
    published_year    INT,
    total_copies      INT DEFAULT 1,
    available_copies  INT DEFAULT 1,
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

-- -------------------------------------------------------------
-- Table: members
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS members (
    member_id        INT AUTO_INCREMENT PRIMARY KEY,
    name             VARCHAR(150) NOT NULL,
    email            VARCHAR(150) UNIQUE,
    phone            VARCHAR(20),
    membership_date  DATE
);

-- -------------------------------------------------------------
-- Table: borrow_records
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS borrow_records (
    record_id    INT AUTO_INCREMENT PRIMARY KEY,
    book_id      INT,
    member_id    INT,
    borrow_date  DATE,
    due_date     DATE,
    return_date  DATE NULL,
    status       VARCHAR(20) DEFAULT 'borrowed',
    FOREIGN KEY (book_id) REFERENCES books(book_id),
    FOREIGN KEY (member_id) REFERENCES members(member_id)
);

-- =============================================================
-- SAMPLE DATA
-- =============================================================

-- Categories
INSERT INTO categories (category_name) VALUES
('Computer Science'),
('Fiction'),
('Mathematics'),
('History'),
('Self-Help');

-- Books
INSERT INTO books (title, author, category_id, isbn, published_year, total_copies, available_copies) VALUES
('Introduction to Algorithms', 'Thomas H. Cormen', 1, '9780262033848', 2009, 5, 3),
('Database System Concepts', 'Abraham Silberschatz', 1, '9780073523323', 2010, 4, 4),
('Clean Code', 'Robert C. Martin', 1, '9780132350884', 2008, 3, 1),
('The Great Gatsby', 'F. Scott Fitzgerald', 2, '9780743273565', 1925, 6, 5),
('1984', 'George Orwell', 2, '9780451524935', 1949, 6, 6),
('To Kill a Mockingbird', 'Harper Lee', 2, '9780061120084', 1960, 4, 2),
('A Brief History of Time', 'Stephen Hawking', 3, '9780553380163', 1988, 3, 3),
('Calculus and Analytic Geometry', 'George B. Thomas', 3, '9780201531749', 1996, 2, 0),
('Sapiens', 'Yuval Noah Harari', 4, '9780062316097', 2011, 5, 4),
('The Diary of a Young Girl', 'Anne Frank', 4, '9780553296983', 1947, 3, 3),
('Atomic Habits', 'James Clear', 5, '9780735211292', 2018, 6, 4),
('The 7 Habits of Highly Effective People', 'Stephen R. Covey', 5, '9780743269513', 1989, 4, 4);

-- Members
INSERT INTO members (name, email, phone, membership_date) VALUES
('Aarav Sharma', 'aarav.sharma@example.com', '9876543210', '2024-01-15'),
('Niveda Pillai', 'niveda.pillai@example.com', '9876543211', '2024-02-10'),
('Rohan Mehta', 'rohan.mehta@example.com', '9876543212', '2024-03-05'),
('Sneha Iyer', 'sneha.iyer@example.com', '9876543213', '2024-04-20'),
('Kabir Khan', 'kabir.khan@example.com', '9876543214', '2025-01-11');

-- Borrow records
INSERT INTO borrow_records (book_id, member_id, borrow_date, due_date, return_date, status) VALUES
(1, 1, '2025-08-01', '2025-08-15', '2025-08-14', 'returned'),
(3, 2, '2025-08-20', '2025-09-03', NULL, 'borrowed'),
(6, 3, '2025-07-10', '2025-07-24', '2025-07-28', 'returned'),
(8, 4, '2025-06-01', '2025-06-15', NULL, 'borrowed'),
(11, 5, '2025-08-25', '2025-09-08', NULL, 'borrowed'),
(11, 1, '2025-05-01', '2025-05-15', '2025-05-14', 'returned'),
(9, 2, '2025-08-05', '2025-08-19', '2025-08-18', 'returned');

-- =============================================================
-- End of script
-- =============================================================