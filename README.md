# Cell 8E — Check REAL LevelId collisions
# READ ONLY

real_level_collisions = {}

for content_id, levels in content_levels.items():

    non_null_levels = {
        level for level in levels
        if level is not None
    }

    if len(non_null_levels) > 1:
        real_level_collisions[content_id] = non_null_levels

print(
    "ContentIds with multiple NON-NULL LevelIds:",
    len(real_level_collisions)
)

for cid, levels in list(real_level_collisions.items())[:20]:
    print(cid, levels)
