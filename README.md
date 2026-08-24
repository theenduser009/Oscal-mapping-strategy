Great. Next is **one read-only identity check for `responsible-parties[]`**. We need to know whether the correct instance identity is just `User Id` or `role/source-field + User Id`.

### Cell 10 — Responsible Party Identity Check

```python
# ============================================================
# Cell 10 — Validate responsible-parties[] identity
# READ ONLY
# ============================================================

from collections import defaultdict
from snowflake.snowpark.functions import col

NODE_PATH = "system-security-plan.metadata.responsible-parties[]"

# Fields mapped to responsible-parties[]
role_fields = [
    r["SOURCE_FIELD_NAME"]
    for r in (
        canonical_mapping_df
        .filter(col("OSCAL_ELEMENT_PATH") == NODE_PATH)
        .select("SOURCE_FIELD_NAME")
        .distinct()
        .collect()
    )
]

user_occurrences = []
group_occurrences = []

for record in source_df.to_local_iterator():

    source_obj = _parse_source_json(record)
    source_record_id = str(record["SOURCE_RECORD_ID"])

    for source_field in role_fields:

        value = resolve_json_path(source_obj, source_field)

        if not isinstance(value, dict):
            continue

        # Users
        for user in value.get("UserList", []) or []:

            if not isinstance(user, dict):
                continue

            user_id = user.get("Id")

            if user_id is not None:
                user_occurrences.append(
                    (
                        source_record_id,
                        source_field,
                        str(user_id)
                    )
                )

        # Groups
        for group in value.get("GroupList", []) or []:

            if not isinstance(group, dict):
                continue

            group_id = group.get("Id")

            if group_id is not None:
                group_occurrences.append(
                    (
                        source_record_id,
                        source_field,
                        str(group_id)
                    )
                )


# ------------------------------------------------------------
# User identity analysis
# ------------------------------------------------------------

unique_role_users = set(user_occurrences)

user_roles_by_record = defaultdict(set)

for source_record_id, source_field, user_id in unique_role_users:
    user_roles_by_record[
        (source_record_id, user_id)
    ].add(source_field)

multi_role_users = {
    key: roles
    for key, roles in user_roles_by_record.items()
    if len(roles) > 1
}


print("=== Responsible Party Identity Check ===")

print("Mapped role fields:", len(role_fields))

print("\nUser occurrences:", len(user_occurrences))
print(
    "Unique source + role + user:",
    len(unique_role_users)
)

print(
    "Duplicate source + role + user occurrences:",
    len(user_occurrences) - len(unique_role_users)
)

print(
    "Users serving multiple roles in same source record:",
    len(multi_role_users)
)

print("\nGroup occurrences:", len(group_occurrences))


# Show a few multi-role examples
if multi_role_users:

    print("\n=== Sample Multi-Role Users ===")

    for (record_id, user_id), roles in list(
        multi_role_users.items()
    )[:10]:

        print(
            "SOURCE_RECORD_ID:", record_id,
            "| USER_ID:", user_id,
            "| ROLES:", sorted(roles)
        )
```

The most important result is:

```text
Users serving multiple roles in same source record: ?
```

If that is greater than `0`, then **`USER_ID` alone must not be our node identity** because the same person can represent multiple responsible-party roles. We would likely need a deterministic identity based on:

```text
SOURCE_RECORD_ID + SOURCE_FIELD_NAME + USER_ID
```

But we’ll make that decision only after seeing this output. No changes to Cells 3–7 yet.
