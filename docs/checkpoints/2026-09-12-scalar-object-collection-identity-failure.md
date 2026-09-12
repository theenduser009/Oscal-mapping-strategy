# Scalar-object / collection-identity registry failure

Date: 2026-09-12  
Evidence: owner-provided Snowflake notebook screenshot  
Status: blocked before mapping-context compilation

## Observed failure

Cell 3 failed at:

```text
ValueError: Scalar object operator cannot define collection identity metadata
```

Visible traceback:

```text
Cell 3, line 971, module
  MAPPING_CONTEXTS = compile_mapping_contexts(...)

Cell 3, line 760, compile_mapping_contexts
  model_contracts = decode_registry_model_contracts(...)

Cell 3, line 634, decode_registry_model_contracts
  elements = {path: _decode_registry_element(by_path[path], root, by_path) ...}

Cell 3, line 539, _decode_registry_element
  raise ValueError(
      "Scalar object operator cannot define collection identity metadata"
  )
```

## What this evidence proves

- The failure occurred while decoding registry model contracts.
- `compile_mapping_contexts(...)` did not complete.
- `MAPPING_CONTEXTS` was not established by the shown execution.
- The graph builder and persistence stages were not reached in the shown run.
- The screenshot does not identify the offending model or registry path.
- No target DML is shown or established by this evidence.

## Likely contract conflict to inspect

At least one registry element appears to use the scalar-object operator while
also defining metadata reserved for collection instance identity. This is a
metadata-contract inconsistency, not evidence that the decoder guard is wrong.

Do not remove or weaken the guard without identifying the exact row.

## Single safest next action

Run a read-only registry inspection that returns every active row whose decoded
operator is scalar-object and whose collection identity fields are populated.
Report the exact OSCAL model, node path, operator, collection flag, instance-key
rule, item path, and any parent-instance identity setting. Do not update the
registry, change Cell 3, or enable DIM/FACT writes until the conflicting row is
reviewed.
