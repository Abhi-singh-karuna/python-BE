-- Drop and recreate a test procedure
DROP PROCEDURE IF EXISTS test_procedure;
CREATE PROCEDURE test_procedure()
BEGIN
    SELECT 'Hello, World!';
END;

-- Drop and recreate a test function with required attributes
DROP FUNCTION IF EXISTS test_function;
CREATE FUNCTION test_function()
RETURNS VARCHAR(255)
DETERMINISTIC
READS SQL DATA
BEGIN
    RETURN 'Hello, World!';
END;

