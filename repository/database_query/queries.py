# User queries

# Get user by email
QUERY_GET_USER_BY_EMAIL = "SELECT id::text AS id, password_hash, is_active, created_at, updated_at FROM users WHERE email = $1"

# Create user
QUERY_CREATE_USER = "SELECT * FROM create_user($1, $2, $3, $4, $5, $6, $7, $8, $9)"

# Terms of Service queries
QUERY_GET_TERMS_OF_SERVICE = """
    SELECT 
        tos.id AS terms_id,
        tos.title AS terms_title,
        tos.subtitle AS terms_subtitle,
        tos.content AS terms_content,
        tsc.id AS sub_id,
                    tsc.title AS sub_title,
                    tsc.content AS sub_content,
                    tsc.sort_order
                FROM 
                    terms_of_service tos
                LEFT JOIN 
                    terms_sub_content tsc 
                ON 
                    tos.id = tsc.terms_id
                ORDER BY 
                    tos.id, tsc.sort_order;
            """
