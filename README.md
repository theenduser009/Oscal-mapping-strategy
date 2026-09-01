Yes — now I can see the full Cell 5 flow clearly. We only need to replace one function: _get_collection_instances(). Do not touch the node/edge building sections below it.

Why? Right now that function does this:

source field
→ UserList[]
→ each Archer user object
→ PAYLOAD = raw Archer user object

That is exactly why your DIM contains HasRead, HasUpdate, Id, etc.

We want it to do:

source field
→ UserList[]
→ each user
→ apply Transform rule
→ PAYLOAD = {"role-id": ..., "party-ids": [...]}

Replace _get_collection_instances() in Cell 5

Replace the whole function starting around line 121 through its return list(instances.values()) with this:

def _get_collection_instances(
    source_record,
    mappings,
    instance_key_rule,
    item_path="$"
):
    source_obj = _parse_source_json(source_record)
    instances = {}

    for mapping in mappings:

        source_field = mapping.get("SOURCE_FIELD_NAME")

        if not source_field:
            continue

        value = resolve_json_path(
            source_obj,
            source_field
        )

        if value in (None, "", [], {}):
            continue

        mapping_type = str(
            mapping.get("MAPPING_TYPE") or ""
        ).strip().lower()

        # ---------------------------------------------------------
        # TRANSFORM COLLECTIONS
        # Example: metadata.responsible-parties[]
        # ---------------------------------------------------------
        if mapping_type == "transform":

            # Get individual source collection items first.
            # For responsible-parties this extracts UserList[].
            items = _extract_collection_items(
                value,
                item_path
            )

            for item in items:

                # Preserve the original item for identity generation
                instance_key = _get_instance_key(
                    item,
                    instance_key_rule,
                    source_field
                )

                if instance_key is None:
                    continue

                instance_key = str(instance_key).strip()

                if not instance_key:
                    continue

                # Rebuild the expected Archer UserList shape so the
                # generic Transform handler can process this one user.
                transform_input = {
                    "UserList": [item]
                }

                transformed = transform_mapping_value(
                    transform_input,
                    mapping
                )

                if transformed in (None, "", [], {}):
                    continue

                instances[instance_key] = {
                    "INSTANCE_KEY": instance_key,
                    "PAYLOAD": transformed
                }

            continue

        # ---------------------------------------------------------
        # EXISTING COLLECTION BEHAVIOR
        # Direct / TBD / Reference / etc.
        # ---------------------------------------------------------
        items = _extract_collection_items(
            value,
            item_path
        )

        for item in items:

            instance_key = _get_instance_key(
                item,
                instance_key_rule,
                source_field
            )

            if instance_key is None:
                continue

            instance_key = str(instance_key).strip()

            if not instance_key:
                continue

            if instance_key not in instances:

                instances[instance_key] = {
                    "INSTANCE_KEY": instance_key,
                    "PAYLOAD": item
                }

            else:
                existing = instances[instance_key]["PAYLOAD"]

                if (
                    not isinstance(existing, dict)
                    and isinstance(item, dict)
                ):
                    instances[instance_key]["PAYLOAD"] = item

    return list(instances.values())

Why this fits your current design

Your registry already says:

responsible-parties[]
IS_COLLECTION = TRUE
INSTANCE_KEY_RULE = SOURCE_FIELD_NAME+ID
ITEM_PATH = UserList[]

So we keep all of that unchanged.

For an Archer field like:

INFORMATION_SYSTEM_OWNER_ISO
User Id = 111016

Cell 5 will now produce one collection instance:

{
  "role-id": "system-owner",
  "party-ids": ["111016"]
}

and its internal node identity remains something like:

INFORMATION_SYSTEM_OWNER_ISO|111016

That is good because two different roles held by the same Archer user remain distinct responsible-party instances.

The TBD rows remain on the old path, so we're not pretending they're finished.

After replacing this function, run Cell 5 only. Don't run Cell 6 yet. Show me the new responsible-parties count from the Cell 5 summary.