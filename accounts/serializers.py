def public_user(user):
    # Explicit allowlist: phone, student ID and admin flags never belong here.
    return {
        "id": str(user.pk),
        "real_name": user.real_name,
        "class_name": user.class_name,
        "bio": user.bio,
    }


def private_user(user):
    return {**public_user(user), "phone": user.phone, "student_id": user.student_id, "role": user.role}
