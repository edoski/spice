# Pydantic public seams for the configuration algebra

## Scope and stopping rule

Question: can one small config-file module hydrate the complete train, tune, and evaluate request algebra without owner coercers, structural dispatch, `SerializeAsAny`, or registries?

Cheapest discriminating observation: define the root and nested alternatives as `Annotated` unions with common `Literal` fields, construct one module-level `TypeAdapter`, and check validation plus schema-driven dumping. Maximum effort was 45 minutes of read-only repository inspection, Pydantic 2.12 documentation/source behavior, PyYAML documentation, and an in-memory probe against the locked Pydantic 2.12.5. Stop condition: every validation, strictness, serialization, and YAML seam has a public owner and no observed behavior contradicts the proposed interface. That condition is met.

## Findings

Pydantic directly supports the required root seam. A discriminated union validates only the branch selected by a common field; each branch declares its value as a `Literal`. Pydantic recommends this over untagged unions because dispatch is predictable and errors stay branch-local. A `TypeAdapter` validates or serializes a union without a wrapper `BaseModel` ([discriminated unions](https://docs.pydantic.dev/2.12/concepts/unions/#discriminated-unions-with-str-discriminators), [union-only `TypeAdapter`](https://docs.pydantic.dev/2.12/concepts/unions/#nested-discriminated-unions), [TypeAdapter purpose](https://docs.pydantic.dev/2.12/concepts/type_adapter/)).

Use string fields, not callable discriminators. Pydantic calls a callable discriminator during serialization too, so it must understand both mappings and model instances. That recreates the structural guessing this issue removes ([callable discriminator warning](https://docs.pydantic.dev/2.12/concepts/unions/#discriminated-unions-with-callable-discriminator)). A single-variant discriminated union is impossible because Python collapses `Union[T]` to `T`; this supports deleting speculative one-entry registries and using the concrete model directly until two real alternatives exist ([single-variant caution](https://docs.pydantic.dev/2.12/concepts/unions/#discriminated-unions-with-str-discriminators)).

Construct the adapter once. Each `TypeAdapter` construction builds a validator and serializer; Pydantic recommends one reusable instance ([performance guidance](https://docs.pydantic.dev/2.12/concepts/performance/#typeadapter-instantiated-once)). `TypeAdapter.validate_python()` and `dump_python(mode="json")` are public methods. The latter produces JSON-compatible Python values suitable for safe YAML output ([validation interface](https://docs.pydantic.dev/2.12/api/type_adapter/#pydantic.type_adapter.TypeAdapter.validate_python), [dump interface](https://docs.pydantic.dev/2.12/api/type_adapter/#pydantic.type_adapter.TypeAdapter.dump_python)). `BaseModel.model_validate()` remains the direct seam only when a caller already knows one concrete model class ([model validation interface](https://docs.pydantic.dev/2.12/api/base_model/#pydantic.main.BaseModel.model_validate)).

Do not treat blanket `strict=True` as synonymous with strict configuration. Strict Python validation rejects textual values for semantic Python types such as datetimes; JSON strictness is intentionally looser for types JSON cannot represent ([strict-mode behavior](https://docs.pydantic.dev/2.12/concepts/strict_mode/)). The locked 2.12.5 probe also rejected YAML strings for `datetime`, `UUID`, and `Path` under `validate_python(..., strict=True)`. This repository quotes timestamps, so a blanket flag would reject valid authored YAML or force a YAML-to-JSON re-encoding detour.

The direct policy is:

- every request/config model owns `extra="forbid"`;
- executable tags are `Literal` fields;
- integers, booleans, and other authored scalars use field-level strictness where coercion would hide an error;
- corpus digests and UUIDv4 identities remain canonical validated strings at the YAML seam;
- textual timestamps and paths use explicit field validators only where the owning contract requires typed runtime values.

Do not try to impose this through `TypeAdapter(..., config=...)`. Pydantic models are configuration boundaries; adapter or parent configuration does not propagate into nested models ([configuration propagation](https://docs.pydantic.dev/2.12/concepts/config/#configuration-propagation)). Model-owned policy is both more explicit and more reliable.

`SerializeAsAny` is unnecessary and unsafe for this algebra. Pydantic normally serializes a model-valued field according to its declared schema. `SerializeAsAny` instead inspects the runtime subtype and includes all of its fields, including fields absent from the declared schema ([subclass serialization](https://docs.pydantic.dev/2.12/concepts/serialization/#subclasses-of-model-like-types), [`SerializeAsAny` behavior](https://docs.pydantic.dev/2.12/concepts/serialization/#serializeasany-annotation)). A discriminated union declares every allowed concrete branch, so normal schema-driven serialization retains the selected branch's fields without duck typing. An unexpected subtype then cannot silently widen persisted or displayed output.

PyYAML's `safe_load` and `safe_dump` are the correct parser/emitter primitives: they restrict construction and emission to standard YAML tags rather than arbitrary Python objects ([official PyYAML documentation](https://pyyaml.org/wiki/PyYAMLDocumentation)). `safe_load` alone is not the complete application seam. Standard YAML can still yield non-string mapping keys and non-JSON Python scalars. The config-file module should recursively accept only `None`, `bool`, `int`, finite `float`, `str`, lists, and mappings with string keys. It should reject unsupported values instead of stringifying or guessing them.

## Recommended module and interface

Use one `config` module with three public entry points:

```python
def read_config(path: Path) -> dict[str, JsonValue]: ...
def write_config(path: Path, value: Mapping[str, JsonValue]) -> None: ...
def hydrate_request(value: Mapping[str, JsonValue]) -> WorkflowRequest: ...
```

`read_config` performs UTF-8 read, `yaml.safe_load`, root-mapping validation, and the recursive JSON-value check. `write_config` runs the same check, emits with `yaml.safe_dump(sort_keys=False)`, and replaces the file atomically. Raw show reads the validated file text, edit validates after the editor returns, and seed calls `write_config`. These operator flows never need typed hydration.

`hydrate_request` calls one private module-level adapter:

```python
WorkflowRequest = Annotated[
    TrainRequest | TuneRequest | EvaluateRequest,
    Field(discriminator="workflow"),
]

_REQUEST_ADAPTER = TypeAdapter(WorkflowRequest)
```

This is a deep module. Its interface exposes three ordinary operations. Its implementation hides YAML safety, recursive raw-value checks, adapter construction, Pydantic error normalization, and canonical output. The filesystem is local-substitutable; tests use a temporary directory. No port or adapter interface is earned. Deleting the module would spread YAML and hydration rules back across CLI, benchmark, and remote callers, so the seam earns its locality.

Usage stays linear. A new-run seed/preparer inserts and writes the destination UUID before this sequence:

```python
raw = read_config(path)          # show/edit/seed surface
request = hydrate_request(raw)   # execution surface
run(request)
```

Do not combine these with a `typed=True` flag or a return union. Raw operator documents and executable requests have different callers and failure meanings.

## Workflow algebra

The root tag is `workflow: Literal["train", "tune", "evaluate"]`. It is executable selection, not a durable identity. Recipe filenames are human labels only. They do not appear as stable IDs and do not need to equal a field inside the file.

Stable identities remain visibly different:

- corpus IDs are validated full lowercase SHA-256 strings;
- study, artifact, and evaluation IDs are validated canonical UUIDv4 strings;
- a model-family discriminator should be `family: Literal["lstm", "transformer", "transformer_lstm"]`, not an `id`;
- temporal/window/action alternatives use the explicit Literal fields owned by Issue 46, never the presence of `start_block`, `duration`, or another structural clue.

Model configuration is one nested discriminated union over the three real families. Each family class owns only its config fields and invariants. There is no generic `ModelSpec`, config-type registry, loader registry, or `SerializeAsAny` base field. Runtime model construction can use one direct `match config:` owner function. Tuning can use the same family union for its real alternatives; a single concrete alternative stays a concrete type.

`TrainRequest` requires a pre-minted `artifact_id` and an explicit, tagged training source. The baseline source carries its `corpus_id`. The selected-study source carries `study_id` and the complete `corpus_id`; pre-work loading verifies that the study records the same corpus before training. No branch is inferred from nullable IDs.

`TuneRequest` requires a pre-minted `study_id`, its `corpus_id`, model-family config, and the exact Issue 46 temporal/action config consumed by tuning. `EvaluateRequest` requires a pre-minted `evaluation_id`, `artifact_id`, `corpus_id`, and only active evaluation controls. It does not repeat model, preprocessing, loss, or temporal training semantics already owned by the artifact record.

Train and tune embed the Issue 46-owned window/K/action/regime contract once. They do not copy its derived values into workflow-specific “resolved” records. Evaluate's requested scoring window remains active input; artifact and corpus loaders provide the durable parent facts. Cross-field validators enforce parent completeness and source consistency after branch selection.

UUID minting is outside hydration. The new-run seed/workflow preparer mints the destination UUID once, inserts it into the raw request, and writes it before typed hydration. After hydration, it asks the Issue 34 durable-record owner to persist the request/intent before acquisition, tuning, training, or evaluation work begins. Missing destination IDs are validation errors at the executable-request seam. Retries reload the persisted ID; they never mint during model validation or execution.

## Invariants, ordering, and errors

Invariants visible at the interface:

- one explicit tag selects every genuine alternative;
- recipe names, executable tags, and stable IDs are distinct;
- every request has all source and destination IDs required for its branch;
- no extra fields, non-string mapping keys, non-finite numbers, arbitrary YAML objects, or unknown runtime subclasses pass the seam;
- hydration has no I/O, identity minting, registry lookup, or framework construction;
- normal schema-driven serialization is the only typed serializer behavior.

Ordering is fixed: mint a new destination identity during seed/preparation; write the complete raw request; apply explicit operator edits; hydrate; persist durable intent through the Issue 34 owner; then begin work. A retry starts from the persisted complete request.

Normalize parser, raw-shape, and `ValidationError` failures to the existing config-facing error with the path and Pydantic error locations preserved. Missing or invalid tags remain `union_tag_not_found`/`union_tag_invalid`; branch fields remain branch-local; extra fields remain `extra_forbidden`. File read/write failures keep their filesystem cause. Runtime loader mismatches, such as a selected study naming a different corpus, are pre-work domain validation failures, not YAML errors.

## Trade-offs

The interface loses plugin-style config extension. That is intentional: the repository has three concrete model families and no earned third-party registration seam. Adding a fourth in-repo family changes one union and one direct construction function, keeping change local and grep-visible.

Targeted strictness is slightly more annotation work than one global `strict=True`. It preserves beginner-friendly quoted YAML timestamps and avoids a hidden YAML-to-JSON conversion. The resulting contract is stricter where coercion is dangerous and explicit where text must become a semantic value.

Raw YAML and typed requests remain separate paths. This costs one explicit `hydrate_request` call. It prevents show/edit/seed from accidentally applying runtime defaults or rewriting a user's recipe through a typed serializer.
