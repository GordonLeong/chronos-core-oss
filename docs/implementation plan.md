Architecture Optimization Plan
Before we begin building out the Phase 0 Domain Models (P0-09 to P0-15), we should do a quick structural optimization pass. While we successfully deleted the universe/scan logic, some naming choices from the previous iteration are now slightly confusing given our new multi-adapter setup.

Proposed Changes
1. Delete Duplicate Files
[DELETE] api/services/ta_registry.py
There is an exact duplicate of this file already living in its correct internal package at api/services/ta/registry.py. The root level one is entirely unused.
2. Rename Folder
[MODIFY] api/services/providers/ -> api/services/adapters/
Why: The MVP heavily emphasizes "Adapter Boundaries". Our concrete implementations (like yahoo_options_adapter.py) currently sit inside a providers folder. Moving them to an adapters folder standardizes the vocabulary across the entire codebase.
3. Expand the Registry
[MODIFY] api/services/provider_registry.py -> api/services/adapter_registry.py
Why: You are completely right! Rather than fragmenting the registries per adapter, creating a cohesive, unified adapter_registry.py that manages all dependencies is much cleaner.
We will rename the file to adapter_registry.py.
We will expand it to house distinct dictionary registries (_PRICE_REGISTRY, _OPTION_REGISTRY, _EXECUTION_REGISTRY, etc.)
We will expose strongly-typed getters like get_price_adapter(name: str), get_option_adapter(name: str), and get_execution_adapter(name: str) to ensure the core trading engine only ever interacts with the proper __Protocol__.
We will update the existing Yahoo and local sim adapters to register themselves in these new categorical mappings.
User Review Required
TIP

Does expanding the single registry file to securely house all 5 typed adapters resolve your concern? If so, I will execute these 3 cleanup steps immediately.

Verification Plan
Automated Tests
Run uv run pytest to ensure that all internal relative imports were updated correctly and nothing breaks at boot.