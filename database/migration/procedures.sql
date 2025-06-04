-- 1. Create or replace function to assign all permissions to roles
CREATE OR REPLACE FUNCTION assign_all_permissions_to_roles()
RETURNS void
LANGUAGE plpgsql AS $$
DECLARE
   v_role_id INTEGER;
   v_module_id INTEGER;
   v_permission_id INTEGER;
BEGIN
   FOR v_role_id IN SELECT id FROM roles LOOP
       FOR v_module_id IN SELECT id FROM modules LOOP
           INSERT INTO role_modules (role_id, module_id)
           VALUES (v_role_id, v_module_id)
           ON CONFLICT (role_id, module_id) DO NOTHING;


           FOR v_permission_id IN SELECT id FROM permissions LOOP
               INSERT INTO role_module_permissions (role_module_id, permission_id)
               VALUES (
                   (SELECT id FROM role_modules WHERE role_id = v_role_id AND module_id = v_module_id),
                   v_permission_id
               )
               ON CONFLICT (role_module_id, permission_id) DO NOTHING;
           END LOOP;
       END LOOP;
   END LOOP;
END;
$$;


DROP FUNCTION IF EXISTS create_user(
    VARCHAR,        -- p_first_name
    VARCHAR,        -- p_last_name
    VARCHAR,        -- p_email
    VARCHAR,        -- p_password_hash
    VARCHAR,        -- p_phone_no
    TEXT,           -- p_picture
    VARCHAR,        -- p_verification_token
    INET,           -- p_ip_address
    TIMESTAMPTZ     -- p_accepted_at
);


CREATE OR REPLACE FUNCTION create_user(
    p_first_name VARCHAR,
    p_last_name VARCHAR,
    p_email VARCHAR,
    p_password_hash VARCHAR,
    p_phone_no VARCHAR,
    p_picture TEXT,
    p_verification_token VARCHAR,
    p_ip_address INET,
    p_accepted_at TIMESTAMPTZ
)
RETURNS TABLE (
    user_id TEXT,
    is_verified BOOLEAN
) AS $$
DECLARE
    uuid_id UUID;
BEGIN
    -- Insert into users table and get UUID
    INSERT INTO users (
        first_name, last_name, email, password_hash, phone_no, picture, role_id
    ) VALUES (
        p_first_name, p_last_name, p_email, p_password_hash, p_phone_no, p_picture, 1
    )
    RETURNING id INTO uuid_id;

    -- User provider linkage
    INSERT INTO user_providers (
        user_id, provider, provider_sub, created_at
    ) VALUES (
        uuid_id, 'email', p_email, NOW()
    );

    -- Email verification record
    INSERT INTO email_verifications (
        user_id, verification_token, is_verified, created_at, expires_at
    ) VALUES (
        uuid_id, p_verification_token, FALSE, NOW(), NOW() + INTERVAL '1 day'
    );

    -- TOS acceptance record using frontend-supplied time
    INSERT INTO user_tos_acceptance (
        user_id, accepted_at, ip_address
    ) VALUES (
        uuid_id, p_accepted_at, p_ip_address
    );

    -- Return values
    user_id := uuid_id::TEXT;
    is_verified := FALSE;

    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;





-- Execute the permission assignment function
SELECT assign_all_permissions_to_roles();
