"""PostgreSQL queries for user operations"""

# User queries
GET_ALL_USERS = "SELECT * FROM users"

GET_USER_BY_EMAIL = "SELECT id, password, is_verified, is_active, created_at, updated_at FROM users WHERE email = $1"

GET_USER_BY_ID = "SELECT id, name, email, phone_no, password, is_verified, is_active, created_at, updated_at FROM users WHERE id = $1"

CREATE_USER = """
    INSERT INTO users (
        id, name, email, password, phone_no, is_verified,
        is_active, created_at, updated_at
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
"""

# OTP queries
GET_OTP_BY_EMAIL = """
    SELECT otp, created_at 
    FROM otps 
    WHERE email = $1 AND is_used = 0 
    ORDER BY created_at DESC 
    LIMIT 1
"""

VERIFY_USER_OTP = """
    SELECT * FROM otps 
    WHERE email = $1 AND otp = $2 AND is_used = 0
"""

UPDATE_USER_VERIFICATION = """
    UPDATE users 
    SET is_verified = TRUE, updated_at = $1 
    WHERE email = $2
"""

MARK_OTP_USED = """
    UPDATE otps 
    SET is_used = 1 
    WHERE email = $1 AND otp = $2
""" 