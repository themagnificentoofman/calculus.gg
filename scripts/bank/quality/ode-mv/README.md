# Offline ODE and multivariable review bundle

This source-bound bundle reconstructs 987 reviewed ODE/multivariable candidates and 18 supplemental integration revisions. It is an offline asset, not a serving dependency or admission authorization. Every copied source retains its original SHA256 in `copy-manifest.json`. Frozen JSONL inputs and prior failed evidence are preserved.

With Python 3.14 and SymPy 1.14 available, import `runtime.py` by its file path. The public API is `catalog()`, `build(route, family, index)`, `verify(route, record, index) -> bool`, `reconstruction_evidence(route, family, index)`, and `close()`. Constructor routes run in separate subprocesses with bundle-local baseline dependencies. `catalog.json` defines the complete finite domains. Unknown routes, families, noninteger indices, and indices outside the listed domain are rejected.

`source-joins.json` binds every record to its raw hash, exact frozen source line, previous identity where applicable, normalized lineage, and source-specific independent review. `admission-plan.json` records the proposed classifications and review rationale; it does not register them. The 10 control-energy display overlays replace 10 earlier rows without increasing the count. Control indices 4, 6, and 9 are Hard in the plan, based on independently checked bounds. Raw author labels remain preserved.

`verify_bundle.py` reconstructs all 1,005 records, compares canonical record bytes and original source-line hashes, and rejects a deliberately altered statement for every record. `reconstruction-report.json` records all 1,005 passes. This checks exact reproduction plus the frozen builders' finite assertions; the copied independent mathematical reviews are separate evidence with their own stated scopes.

The Green-kernel diagonal-integral proof has two observed, algebraically identical SymPy serializations. `certificate_serialization.py` permits only the exact named proof slot and the two bound expressions, proves their difference is zero, requires every other field to match, and restores the original frozen serialization and content hash. Each use is recorded. It does not alter statements, choices, solutions, mathematical values, or unrecognized proof fields. The initial three failures are retained in `reconstruction-report-initial-failure.json`.

Final actual-ID option screening, admission, selection capacity, and publication remain separate parent-owned gates. No central registry or application behavior is changed by this bundle.
