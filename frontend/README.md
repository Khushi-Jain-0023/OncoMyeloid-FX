# Research explorer

A read-only website over the completed five-phase research release. Native HTML,
CSS and JavaScript; no frontend runtime dependencies, accounts or API keys.

From the repository root, using the existing research environment:

```powershell
& .\work\release-venv\Scripts\python.exe build_frontend.py
& .\work\release-venv\Scripts\python.exe serve_frontend.py
```

Open http://127.0.0.1:8765. Stop with Ctrl+C. Alternatively use any Python
environment with the project's existing pandas/pyarrow dependencies to build;
the preview server itself uses only Python's standard library.

The build creates `frontend/dist`. Serve this directory through HTTP, rather
than opening index.html directly. It can also be deployed as a static website.
No research pipeline is run by the website. Rebuild after changing source results.

## Integration

- Phase 1: feasibility report and study interpretation.
- Phase 2: cohort metadata and human association statistics.
- Phase 3: all 6,124 genes for each of MHCII, CD40 and PD-L1, with source provenance.
- Phase 4: patient-bootstrap stability and validation decision.
- Phase 5: verified release metadata, report and reproducibility downloads.

The exporter checks Phase 3/4 input hashes before building. Missing evidence stays
null and never becomes a negative result. The UI supports search, endpoint and
evidence filters, sorting, pagination, gene details and filtered CSV downloads.
Filter state is retained in the URL. Scores remain exploratory heuristics.

Run frontend logic checks with `node --test frontend/model.test.mjs` and export/server
checks with `python -m pytest frontend/test_export.py -q` in the research environment.
Generated exports are ignored by Git; source files are versioned.

## Design decisions and references

Claymorphism uses ivory and muted sage, rounded surfaces, subtle outer shadows
and inset controls. System fonts, semantic controls, visible keyboard focus,
44px control targets and stacked mobile layouts keep the interface restrained.
There are no animations, gradients, remote fonts or UI libraries.

Reviewed [Impeccable](https://github.com/pbakaus/impeccable) (commit
2b86d9c07b97d4bed7de23583e1bd1e58dd2baae), including its skill, new-work and
craft-floor guidance, and [Taste skill](https://github.com/leonxlnx/taste-skill)
(commit f6b76575f949707b4e3c37cd86cb44b0b98643e8), including its skill, system
and copy references. Applied their relevant hierarchy, spacing, accessibility,
responsive layout and specific-copy guidance. The user's minimal architecture
and no-animation requirements take precedence over optional toolkit or motion
recommendations. No third-party implementation code was copied.

Browser visual verification is pending: this execution environment could not
reach its persistent localhost preview. Responsive CSS is implemented but has
not yet been visually confirmed on desktop and mobile.
