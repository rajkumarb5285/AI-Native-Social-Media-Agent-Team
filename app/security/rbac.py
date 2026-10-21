from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"

# Hierarchy: ADMIN > EDITOR > VIEWER
ROLE_PERMISSIONS = {
    Role.ADMIN: {"read", "create_run", "approve", "publish", "manage_integrations", "manage_users", "delete"},
    Role.EDITOR: {"read", "create_run", "approve", "publish"},
    Role.VIEWER: {"read"}
}

def has_permission(user_role: str, permission: str) -> bool:
    role = Role(user_role) if user_role in [r.value for r in Role] else Role.VIEWER
    return permission in ROLE_PERMISSIONS.get(role, set())
