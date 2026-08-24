Yes — that is exactly the design I have in mind, and I checked your latest Cell 1 against it carefully.

The **engine is not being built for `metadata` or even just SSP**. SSP is only the first test case. The intended behavior is:

```text
Mapping CSV
     ↓
canonical_mapping_df
     ↓
element_registry_df
     ↓
system-security-plan          ← discovered/configured node
metadata                      ← discovered/configured node
import-profile                ← discovered/configured node
components[]                  ← discovered/configured node
props[]                       ← discovered/configured node
...
     ↓
SAME build_nodes()
     ↓
SAME build_dependencies()
```

So there will **not** be code like:

```python
build_metadata()
build_ssp_root()
build_import_profile()
build_component()
build_prop()
```

Instead, one generic builder receives the metadata describing the element.

And relationships are also dynamic. We will not hardcode:

```python
SSP -> metadata
```

The registry will establish:

```text
NODE_PATH                         PARENT_NODE_PATH

system-security-plan             NULL
system-security-plan.metadata    system-security-plan
system-security-plan.import...   system-security-plan
```

Then the generic relationship builder creates the FACT edges.

### About your current Cell 1

I approve the direction shown in the screenshot.

Importantly, you now have:

```python
"OSCAL_MODEL": "SSP"
```

and you **do not** have:

```python
ROOT_NODE_PATH_PREFIX = "system-security-plan"
```

That's exactly what we wanted.

One distinction I want us both to keep very clear:

**Dynamic for elements:** yes, absolutely. The CSV + element registry drive all root/child/repeated elements.

**Dynamic for OSCAL models:** also the intended architecture, but right now Cell 1 selects:

```python
"OSCAL_MODEL": "SSP"
```

and the target tables are currently SSP targets:

```text
DIM_OSCAL_SSP_ELEMENT
FACT_OSCAL_SSP_DEPENDENCY
```

That's okay because SSP is our first run. Later the **configuration**, not the processing code, can say something like:

```text
SSP  → SSP DIM / FACT
POAM → POAM DIM / FACT
AP   → AP DIM / FACT
```

The engine functions should remain unchanged.

So the production principle we're freezing is:

> **New element = metadata change, not Python rewrite.**
>
> **New OSCAL model = configuration/mapping change, not engine rewrite.**

And one more thing I'm keeping firmly in mind: repeated elements such as `components[]`, `props[]`, etc. are why we marked:

```python
"identity_version": "v1_legacy_singleton"
```

as **legacy** rather than pretending it is final. We will resolve the repeated-instance identity once the element registry exists, before we build production nodes.

So yes — I am tracking the exact architecture we agreed on. **Cell 1 can now be frozen. Don't modify it again right now.**

Next is **Cell 2 only: load `source_df` + the real mapping CSV into `mapping_df`, without transforming either one.**
