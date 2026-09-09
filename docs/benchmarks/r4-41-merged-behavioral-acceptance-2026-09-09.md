# R4-41 Merged Behavioral Acceptance — 2026-09-09

## Scope

This acceptance run executed the Unified Canvas modules and their SQLite routes,
not source-text assertions alone. The test set combines JavaScript VM lifecycle
tests (real production module code), runtime command tests, and persistence/API
integration tests. It was run on local `main` after the R4-41 evidence-harness
correction.

```text
Ran 27 tests in 0.487s
OK
```

## Gate E — Interaction

- Node drag/resize sessions dispatch through the shared controller.
- Selection is a single change-tracked authority; viewport anchor zoom keeps
  world coordinates stable.
- Keyboard dispatch stops at the first registered handler that handles an
  event.
- Connection gesture lifecycle and revision-safe connection-result projection
  are exercised together.
- The resource audit exercises the global preview/compare pointer pair and
  idempotent remote-sync start/stop lifecycle.

Tests: `test_classic_node_drag_and_resize_sessions_are_cut_over_to_the_controller`,
`test_selection_authority_store_is_set_compatible_with_change_tracking`,
`test_classic_selection_is_cut_over_to_the_single_authority`,
`test_viewport_coordinates_and_anchor_zoom_are_shared`,
`test_keyboard_runtime_dispatches_to_registered_handlers_until_handled`,
`test_connection_gesture_controller_owns_the_gesture_lifecycle`,
`test_connection_result_projection_is_shared_and_revision_safe`,
`test_output_preview_and_compare_share_one_global_pointer_pair`, and
`test_remote_sync_start_stop_is_idempotent`.

## Gate G — Graph and group

- A move-driven membership transition removes the old membership, adds the
  target membership, and hands off generator edges without duplicating an
  already present group edge.
- Veto, prompt-group and repeated no-op cases are covered.
- Normal and historical Smart-node graph connects are persisted atomically;
  group add/remove is then reloaded under its single resulting revision.

Tests: `test_group_membership_transition_algorithm_is_owned_by_the_shared_module`,
`test_group_input_handoff_algorithm_is_shared_by_group_creation`,
`test_classic_connect_side_effects_apply_the_policy_projection`,
`test_registered_graph_route_connects_two_existing_nodes_atomically`,
`test_registered_graph_route_connects_smart_nodes_with_input_sync`, and
`test_add_and_remove_persist_and_reload_under_one_revision`.

## Gate H — Media lifecycle

- Media state is transport/DOM-lifecycle neutral and survives a renderer
  remount.
- Native playback preservation and media renderer state signatures are
  exercised; RenderSweep covers live-media DOM reuse, per-node isolation, and
  its refresh/full-sweep fallback.
- Media kind classification, preview/original URL normalization, image-size
  selection, output-resolution metadata, and compare URL projection cover the
  supported image/video/audio and preview/fallback/original/high-resolution
  selection boundary.
- Repeated player binding and reload storm risks are bounded by the idempotent
  initialization/resource tests in the runtime audit.

Tests: `test_media_playback_state_is_transport_and_dom_lifecycle_neutral`,
`test_editor_adapters_share_native_media_playback_state_preservation`,
`test_render_runtime_projects_media_state_across_remounts`,
`test_media_renderer_elements_carry_the_state_signature_url`, and
`test_render_sweep_owns_rebuild_isolation_reuse_and_refresh_fallback`.
Supplemental run (5 tests, `OK`):
`test_editor_adapters_share_pure_media_kind_classification`,
`test_editor_adapters_share_pure_media_url_normalization`,
`test_editor_adapters_share_image_size_calculation`,
`test_media_tools_owns_output_resolution_metadata_projection`, and
`test_media_tools_owns_output_compare_url_projection`.

## Gate J — Clipboard, workflow and reload parity

- Clipboard fallback behavior is exercised; a clipboard-sourced node persists
  across legacy record types through the registered local route.
- Workflow import normalization removes empty records; both workflow envelope
  and batch export projections are exercised.
- SQLite authority is reopened across restart and remains the routing source
  of truth, providing the reload-parity persistence proof.

Tests: `test_editor_adapters_share_clipboard_fallbacks`,
`test_registered_local_route_persists_clipboard_sourced_nodes_across_legacy_record_types`,
`test_workflow_transfer_client_normalizes_import_shapes_and_removes_empty_records`,
`test_workflow_transfer_client_owns_export_envelope_projection`,
`test_workflow_transfer_module_owns_export_projection_batch`, and
`test_authority_persists_across_restart_and_decides_routing`.

## Interpretation

This record demonstrates actual behavior of the modules and routes under their
test hosts. Browser-specific rendering/interaction/resource timings and
repeat-render duplicate checks are recorded separately in
`r4-41-runtime-audit-2026-09-09.md`; no claim here relies only on source
searches.
