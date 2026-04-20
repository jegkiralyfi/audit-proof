# Custom provider profile

Use a custom provider when you want Audit-Proof to call your own Python integration layer.

Format:
- `custom:module_path:ClassName`
- or directly `module_path:ClassName`

The class must inherit from `EvidenceProvider`.

This is the preferred route for non-standard serving stacks or special internal routing logic.
