# Milestone 3 source and coverage research

Access date: 2026-11-03. This bounded review covers every named starting collection, with separate records for both Active Calculus editions, plus six additional references. The machine-readable register contains exact locators, repository revisions or document editions, solution types, license evidence, exceptions and destination mappings for original problems that cite mathematical background. No source-derived problem, explanation, figure or executable script has been imported. Research review was performed by agents, not humans.

## Rights decisions

| Source | Verified terms | Use in this update |
|---|---|---|
| Active Calculus single and multivariable, second editions | [Single colophon](https://activecalculus.org/single2e/frontmatter-3.html) and [multivariable colophon](https://activecalculus.org/multi2e/frontmatter-3.html): CC BY-SA 4.0 | Reference now; adaptation can be considered with exact item checks and an explicit BY-SA content distribution path. |
| UBC CLP | [Project terms](https://personal.math.ubc.ca/~CLP/about/): CC BY-NC-SA 4.0 | Reference only; project distribution compatibility has not been established. |
| WeBWorK OPL | [Pinned OPL license](https://github.com/openwebwork/webwork-open-problem-library/blob/e632b510afd1983e70b0d5bbeb5631dbdcb95823/OPL_LICENSE): default CC BY-NC-SA 3.0, directory/item overrides possible | Reference only. Inspect item lineage and every applicable override before any future import. |
| OpenStax Calculus | [Pinned current license](https://github.com/openstax/osbooks-calculus-bundle/blob/018da4da252bb9c56759e34396efea91852bcf5a/LICENSE): CC BY-NC-SA 4.0 | Reference only. Do not substitute a historical OpenStax license. |
| APEX version 4 | [Pinned README](https://github.com/APEXCalculus/APEXCalculusV4/blob/6120781e01260093d56e6e3a9b8fd92ad2f4520d/README.md): CC BY-NC 4.0 | Reference only. The inspected version is not version 5. |
| MIT OCW | [Current terms](https://ocw.mit.edu/pages/privacy-and-terms-of-use/): CC BY-NC-SA 4.0, exclusions apply | Reference only; assigned textbook exercises and outside resources need separate rights. |
| MIT, UK, Kent and UF integration bees; MAA Putnam | No reuse grant found in the inspected official pages and documents | Reference only. These findings do not prove that no permission exists elsewhere. |
| Differential Equations IBL Workbook | [Author site](https://siefkenj.github.io/IBLODEs/index.html): CC BY-SA 4.0 | Reference now; possible attributed adaptation after item review. |
| Notes on Diffy Qs v6.11 | [Author terms](https://www.jirka.org/diffyqs/): choice of CC BY-SA 4.0 or CC BY-NC-SA 4.0 | The BY-SA option can support a compatible future adaptation. Its separate OPL problem bundle has distinct lineage. |
| NIST DLMF v1.2.8 | [Notices](https://dlmf.nist.gov/about/notices): limited research/teaching copying; commercial and bulk copying prohibited | Mathematical identity reference only. Government hosting does not make all contributed content public domain. |

All register entries currently have `intendedUse: reference_only` and `importQueueEligible: false`. This is a concrete scope choice, not an assertion that the BY-SA sources prohibit adaptation. The implementation may use independently conceived original problems and independently derived classical facts. Renaming variables, changing constants, translating, paraphrasing or adding answer options does not by itself establish originality.

For an actual permitted adaptation, record the exact source item, authors, source copyright/license/disclaimer notices, license URL, modifications and previous changes, and destination problem revision/family IDs. Preserve share-alike on the adapted content and avoid additional restrictions that defeat the license. Do not silently change the license of unrelated application code. The [CC BY-SA 4.0 deed](https://creativecommons.org/licenses/by-sa/4.0/) links the controlling legal terms.

## What the sources can add

These are discovery directions, not counts of authored, verified or active families. Their difficulty must be assigned from the best reasonable solution and multiple-choice shortcuts.

| Topic | Missing decisions worth authoring independently | Specific reviewed leads |
|---|---|---|
| Integration | Symmetry before calculation; involution pairing; geometry versus antiderivatives; piecewise/floor partitioning; internal parameters; recurrence; special-function domains | MIT 2026 qualifier items 1/3/4/8/11/12/17/20; UK sample question 1 with alternative methods; Kent 2025 round 1; DLMF beta and AGM identities |
| Differentiation | Interpret slopes and units; distinguish implicit relation from a single-valued function; handle vertical tangents; decide when Newton iteration fails | Active single §1.1 activities; CLP-1 examples 2.11.1–3 and solutions 2.11.2.1–3/11/12; APEX `ex_newt2`, `ex_newt3` and convergence discussion |
| Limits | Compare one-sided behavior; distinguish theorem guarantee from nonexistence; recognize iterative convergence and failure; control central and tail asymptotics | Active single §1.1; OPL `S02.05.IntermediateValueThm.PTP02.pg`; APEX Newton discussion; Putnam 2024 B6 |
| Series | Check hypotheses before using a test; distinguish term limit from sum convergence; estimate error; distinguish absolute/conditional convergence; understand rearrangement | OpenStax volume 2 §5.5 examples 5.19/5.20/5.22 and exercises 294–301; Putnam 2024 B6 |
| Differential equations | Restore equilibria lost by division; read stability; compare local and global existence; linearize; infer a model from rates; distinguish numerical instability from actual dynamics | MIT 18.03 problem sets 1/3; OPL `ur_de_6_1.pg`; IBL module 3; Diffy Qs §§1.2/1.5 |
| Multivariable | Hold the right variable fixed; interpret mixed partials and units; distinguish surfaces with identical first-order information; follow a path through a scalar field | Active multi §11.5 activity 11.5.2 and exercises 14/15; multivariable chain-rule section |

The original local `scripts/bank/families.py` shows why these directions matter: much of the existing variety changes coefficients inside three fixed kernels. The research register does not certify the deployed baseline or replace the implementation team's per-cell audit.

## Solution and provenance distinctions

- MIT 2026 qualifier and final-round documents provide answer keys. UF's 2024 document calls itself a solution manual but supplies final answers. These are not worked derivations.
- UK sample solutions and Kent 2025 solutions include actual worked reasoning; the UK sample pack also offers alternatives. Its revised solutions reuse the 2020 sample set, so do not count mirrors or revisions as new constructions.
- CLP has distinct hints, answers and worked-solutions appendices. Active single Appendix B omits preview-activity answers. Diffy Qs supplies short answers or reasoning for selected exercise numbers; not every answer is a full solution.
- The sampled OPL IVT file cites a Stewart textbook item. The sampled OPL stability file has stale, inconsistent legacy XML metadata. Preserve current repository paths and inspect credited origins.
- The UF techniques handout credits exercises from other contests. The IBL existence/uniqueness module credits Lebl. Hosting and collection licenses must not erase these upstream attributions.
- OpenStax's [current preface](https://openstax.org/books/calculus-volume-2/pages/preface) also states AI-inclusion and commercial-printing permission requirements, excludes trademarks, and specifies page/view attribution. These are recorded separately; this update proposes no source-content reuse.
- Repository HEAD and the published website build are recorded separately where equivalence was not established. The Active landing URLs redirect using HTML meta refresh; the exact frontmatter and colophon pages are accessible.

The register contains 18 collections and 35 inspected item records. Its 144 destination mappings are theorem-reference links to independently authored content, not copied or adapted source items. Supplemental references include CMU probability notes, Illinois occupancy notes, and MIT number-theory notes. Their exact locators and terms are in the register.

No files in this research directory count toward playable coverage. Keep discovered, authored, verified, quarantined, imported and active counts separate. Destination mappings must be filled only when a real item is admitted; an original item can cite a source as mathematical background without claiming that it was adapted.
