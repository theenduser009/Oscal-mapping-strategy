Almost. **Node identity is correct now. One edge function is still wrong.**

The screenshot still has:

```python
return f"{source_node_key}|{target_node_key}|{edge_type}"
```

It must use the frozen `::` format and hex key inputs.

Paste this to the other AI:

> **Only fix `build_edge_seed()`. Change nothing else.**
>
> Replace it with:
>
> ```python
> def build_edge_seed(
>     source_node_key_hex,
>     target_node_key_hex,
>     edge_type="parent_of"
> ):
>     return f"{source_node_key_hex}::{target_node_key_hex}::{edge_type}"
> ```
>
> Keep `compute_edge_key()` exactly as:
>
> ```python
> def compute_edge_key(seed):
>     return hashlib.md5(seed.encode("utf-8")).digest()
> ```
>
> Do not modify any other Cell 4 function.
> Do not create Cell 5.
> Show only these two functions and stop.

After that, **identity section is frozen.**
