Use this exact prompt:

> **Do not rewrite Cell 4. Fix only the identity helpers.**
>
> 1. `build_node_seed()` must be exactly:
>
> ```python
> def build_node_seed(source_system, source_table, content_id, node_type):
>     cid = content_id.strip() if content_id is not None else ""
>     return f"{source_system}|{source_table}|{cid}|{node_type}"
> ```
>
> 2. Edge identity must be directional:
>
> ```text
> parent/source -> child/target
> ```
>
> Use the frozen edge seed format:
>
> ```text
> SOURCE_NODE_KEY_HEX::TARGET_NODE_KEY_HEX::EDGE_TYPE
> ```
>
> Default `EDGE_TYPE = "parent_of"`.
>
> `compute_edge_key()` must return MD5 digest bytes for `BINARY(16)`.
>
> 3. Do not change any other function in Cell 4.
>
> 4. Do not create Cell 5.
>
> Show only the corrected identity helper section and stop.
