# SSP component source contract checkpoint

Date: 2026-09-09
Mode: read-only
Writes executed: `False`
Source records scanned: **2,813**
Expected reference fields: **6**
Fields with component mapping rows: **6**
Records with cross-field shared governed IDs: **7**
Unique governed IDs shared across fields: **12**

## Field observations

### SUBSYSTEMS
- Mapping rows: 1
- Mapping type: REFERENCE
- Declared component-type signal: `system`
- Populated records: 0
- Governed-ID candidates: 0
- ContentId occurrences: 0
- Scalar references: 0
- Generic IDs: 0
- Within-field duplicate governed-ID occurrences: 0
- Root value type: NONE

### SOFTWARE
- Mapping rows: 1
- Mapping type: REFERENCE
- Declared component-type signal: `software`
- Populated records: 2
- Records with governed-ID candidate: 2
- Populated records without governed-ID candidate: 0
- Explicit ContentId occurrences: 7
- Scalar references: 0
- Generic IDs: 0
- Within-field duplicate governed-ID occurrences: 0
- Identifier-bearing objects: 7
- Root value type: array=2
- Top object key signature: `ContentId,LevelId`

### HARDWARE
- Mapping rows: 1
- Mapping type: REFERENCE
- Declared component-type signal: `hardware`
- Populated records: 1
- Records with governed-ID candidate: 1
- Populated records without governed-ID candidate: 0
- Explicit ContentId occurrences: 1
- Scalar references: 0
- Generic IDs: 0
- Within-field duplicate governed-ID occurrences: 0
- Identifier-bearing objects: 1
- Root value type: array=1
- Top object key signature: `ContentId,LevelId`

### INTERCONNECTIONS
- Mapping rows: 1
- Mapping type: REFERENCE
- Declared component-type signal: `interconnection`
- Populated records: 912
- Records with governed-ID candidate: 912
- Populated records without governed-ID candidate: 0
- Explicit ContentId occurrences: 4,444
- Scalar references: 0
- Generic IDs: 0
- Within-field duplicate governed-ID occurrences: 0
- Identifier-bearing objects: 4,444
- Root value type: array=912
- Top object key signature: `ContentId,LevelId`

### INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM
- Mapping rows: 1
- Mapping type: REFERENCE
- Declared component-type signal: `interconnection`
- Populated records: 331
- Records with governed-ID candidate: 331
- Populated records without governed-ID candidate: 0
- Explicit ContentId occurrences: 0
- Scalar reference occurrences: 352
- Generic ID occurrences: 0
- Within-field duplicate governed-ID occurrences: 0
- Identifier-bearing objects: 0
- Root value type: array=331
- Top object key signature: NONE

### SAP_INTAKE_FORM_INTERCONNECTIONS
- Mapping rows: 1
- Mapping type: REFERENCE
- Declared component-type signal: `interconnection`
- Populated records: 0
- Governed-ID candidates: 0
- ContentId occurrences: 0
- Scalar references: 0
- Generic IDs: 0
- Within-field duplicate governed-ID occurrences: 0
- Root value type: NONE

## Result

`COMPONENT SOURCE CONTRACT EVIDENCE CAPTURED`

No database objects or rows were changed.