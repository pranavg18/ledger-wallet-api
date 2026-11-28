# Diagrams

Diagram sources (Mermaid `.mmd` or PlantUML `.puml`) for `docs/architecture.md` and the SRS.
Keep each diagram's source here and embed or link it from the document that uses it.

Done:

| File | Diagram | Used in |
|---|---|---|
| `use-case.tex` → `use-case.svg` | UML use case diagram (TikZ). Build: `tectonic docs/diagrams/use-case.tex && pdftocairo -svg docs/diagrams/use-case.pdf docs/diagrams/use-case.svg` | SRS 2.2 (`docs/srs.md`, Figure 2 in `docs/srs.pdf`) |
| [`deployment.mmd`](deployment.mmd) | Local development and CI deployment diagram | [Architecture §5](../architecture.md#5-deployment-view) |

Planned for Stage 2 (SE-2):

| File | Diagram | Task |
|---|---|---|
| `component.mmd` | Component / layer diagram | T2.10 |
| `er.mmd` | Entity-relationship diagram of the ledger schema | T2.2 |
| `sequence-transfer.mmd` | Transfer with locking and idempotency | T2.6 |
| `sequence-reversal.mmd` | Reversal | T2.6 |
| `sequence-reconciliation.mmd` | Reconciliation | T2.6 |
| `class-domain.mmd` | Domain class diagram (Money, Transaction, Entry) | T2.2 |

Preview Mermaid in VS Code (Mermaid extension), Obsidian, GitHub, or https://mermaid.live.
