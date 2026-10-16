-- Run once after selecting the expense_tracker database.
-- Existing expense records are not changed by this migration.
CREATE TABLE IF NOT EXISTS monthly_income (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    income_month DATE NOT NULL,
    source VARCHAR(80) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    INDEX idx_monthly_income_month (income_month)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
