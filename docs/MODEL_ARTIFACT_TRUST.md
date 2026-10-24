# Research model custody and signature gate — NOT clinical approval

## Threat addressed

A model JSON with an attacker-computed SHA-256 could previously be accepted even if it was never trained. Since v0.9, `read_model` fails closed unless an **installation-pinned trusted Ed25519 verification key** authenticates a separate attestation sidecar. The trusted key is configured outside the model JSON using `WAVEASSURE_TRUSTED_RESEARCH_KEY=<path to raw 32-byte public key>`.

The model file `models/vtac/vt_model.json` still contains a SHA-256 digest over its canonical JSON body. The distinct `models/vtac/vt_model.attestation.json` has these keys:

```
{
  "schema": "waveassure-model-attestation-v1",
  "model_sha256": "<lowercase SHA-256 of the model's canonical content>",
  "scope": "research_integrity_only",
  "signer_id": "<signed artifact reviewer identifier>",
  "signature_base64": "<base64 Ed25519 signature>"
}
```

The Ed25519 message is `b'waveassure-model-attestation-v1\n' + canonical_json_bytes(all attestation fields except signature_base64)`. The key **must be independently provisioned**. No signing private key is bundled or auto-generated at runtime, and the model builder alone does not get to claim external approval. Never commit the private key. A signature alone is insufficient: verify training code, real dataset manifests, held-out patient/site-partitioned metrics, security controls and protocol evidence separately.

Runtime refuses files without trusted signature or with a changed model, signer identity, or wrong key. The signed metadata **only** establishes an integrity check against a pinned key. A dishonest signer can still sign a fabricated model. This feature does not substantiate any independent clinical validation, ISO certification or CDSCO approval.

The built-in trainer performs a clearly labelled *internal numerical parity check* on its own unsigned output, not the operational trust check. This cannot install the trained model into the clinical or review process automatically.
