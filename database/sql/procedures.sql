-- Drop and recreate a test procedure
DROP PROCEDURE IF EXISTS test_procedure();
CREATE OR REPLACE PROCEDURE test_procedure()
LANGUAGE plpgsql
AS $$
BEGIN
    SELECT 'Hello, World!';
END;
$$;

-- Drop and recreate a test function with required attributes
DROP FUNCTION IF EXISTS test_function();
CREATE OR REPLACE FUNCTION test_function()
RETURNS VARCHAR
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN 'Hello, World!';
END;
$$;

