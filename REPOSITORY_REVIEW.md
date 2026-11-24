# Repository Review

**Scope:** Full repository review of the Python, ROOT, OMS integration, CLI entry points, environment, fixture data, and documentation.

**Review status:** Static review plus Python syntax compilation and direct parsing of `test/BSFit_Fill11740_BX72.txt`. Runtime OMS and ROOT behavior could not be exercised without the external OMS credentials, Kerberos setup, and the repository's pinned scientific environment.

## Executive summary

The repository is a compact data-processing and plotting utility for CMS beamspot fits. Its core separation into parsing, OMS enrichment, formatting, and plotting is reasonable, and the default input parser successfully handles the supplied fixture.

The main risks are:

- Several database-format, empty-result, and malformed-record paths fail with uncaught exceptions or missing required fields.
- Multiprocessing does not implement its progress reporting as intended and is not robust to invalid stream counts or worker failures.
- The plotting modules contain definite runtime bugs in `multiplot()`, dual-axis plots, and CMS canvas rendering.
- CLI paths and output directory handling are inconsistent and in one case write tabular output outside the requested directory.
- The repository lacks an automated test suite and has documentation/environment drift.

## Repository map

| Area | Purpose |
|---|---|
| `cls/BSFormat.py` | Parses VDM/database text formats and writes tabular text |
| `cls/BSParser.py` | Filters fit types, fetches OMS metadata, and calculates true widths |
| `cls/OMSUtils.py` | Creates the OMS API authenticator and executes API queries |
| `cls/MPUtils.py` | Multiprocessing pool and progress bar |
| `cls/BSPlotter.py` | ROOT graph, canvas, and plot orchestration |
| `cls/BSCanvas.py`, `cls/BSGraph.py`, `cls/BSLatex.py`, `cls/BSLine.py` | ROOT style subclasses |
| `plotter_bylumi.py` | Luminosity/time-oriented CLI |
| `plotter_byrun.py` | Fill/run-oriented CLI |
| `multiplotter.py` | Combined-axis plotting CLI |
| `test/` | One text fixture and reference plots/text outputs |

## Findings

### High severity

#### 1. Database-format parsing does not provide the covariance required by downstream code

**Location:** `cls/BSFormat.py:42-75`; `cls/BSParser.py:92-139`

`_fetcher_database()` extracts beamspot values but does not create `covariance` or `pvcovariance`. `_compute_proper_widths()` then unconditionally reads `beamspot['covariance'][6][6]`, `[7][7]`, `[3][3]`, `[4][4]`, `[5][5]`, and `[0][1]`. The database flavour therefore raises `KeyError` after successful OMS enrichment, even if parsing otherwise succeeds.

The write tabular default format also requires `covariance`, `beginTime`, `endTime`, `dxdy`, and `npvs`, while database parsing does not populate all of these.

**Recommendation:** Define a complete normalized beamspot schema, including absent covariance fields as `None` or a covariance object of zeros of the correct size. Reject incompatible flavors explicitly and only export fields that are available. Add fixture coverage for database-format input.

#### 2. The success case silently loses all IOV data for missing OMS records

**Location:** `cls/BSParser.py:43-61`, `104-106`

When a run, lumisection, fill, or intermediate lumisection is missing, `_fetch_timestamps_from_OMS()` returns an empty result and `fetch_timestamps_from_OMS()` removes that IOV from `beamspot`. Missing intermediate lumisections are especially easy to hide because lumisection responses are merely omitted from the average.

This makes the distinction between “no OMS match” and “partial OMS metadata” implicit. It also prevents reporting counts or reasons for rejected data.

**Recommendation:** Keep IOV records and attach an enrichment status/error, or return structured partial results. Fail fast only for fatal configuration errors; for ordinary missing API records, retain records, skip plots that require missing data, and emit an aggregated summary.

#### 3. Luminosity averaging divides by a potentially empty list

**Location:** `cls/BSParser.py:59-66`

`lumlist` starts with `lsjsn`, so it is not empty for the normal path. If `lsjsn` or `lejsn` is malformed rather than absent, however, code may index missing fields or produce a `ZeroDivisionError`/incorrect average. Malformed lumisection entries are not validated before accessing `init_lumi`, `pileup`, and timestamps.

**Recommendation:** Validate response JSON with explicit helpers and skip or aggregate only valid lumisection records. Never assume API payload structure.

#### 4. `IOVbegin` and `IOVend` use inconsistent endpoints

**Location:** `cls/BSParser.py:69-70`

The code sets `IOVbegin` from `lsjsn['start_time']` but `IOVend` from `lsjsn['end_time']`, even when `ls < le` and `lejsn` represents a later final lumisection. For a multi-lumisection IOV, the end value is therefore wrong.

**Recommendation:** Set `IOVbegin` from `lsjsn.start_time` and `IOVend` from `lejsn.end_time`.

#### 5. `plotter_bylumi.py` computes an output directory from an unsafe path transformation

**Location:** `plotter_bylumi.py:29`

This line:

```python
'/'.join(args.output.split('/')[:-2]) + '/txt'
```

does not use the input or output base name and is especially wrong for relative paths such as `test`, `results`, or `out/plots`. It can write to an unintended absolute `/txt` path or elsewhere in the filesystem.

**Recommendation:** Add a dedicated `--tabular-output` option or derive a stable sibling directory explicitly, for example `os.path.join(os.path.dirname(args.output), 'txt')`.

### Medium severity

#### 6. `multiplot()` is not callable

**Location:** `cls/BSPlotter.py:98-116`

`multiplot()` has multiple definite defects:

- `p.name` is never defined by `BSPlot1D`.
- `var` is undefined in `can.SaveAs('{}/{}.pdf'.format(output, var), 'pdf')`.
- `cosmetics = plots[0].cosmetics` is read before `add_cosmetics()` is called.
- It does not call `can.DrawExtra()`.

**Recommendation:** Refactor it to accept explicit names and output basenames, call `add_cosmetics()` for every plot, and centralize the CMS canvas drawing workflow.

#### 7. `multiaxes()` can divide by zero or scale using invalid ranges

**Location:** `cls/BSPlotter.py:119-149`

The right-axis scale factor is:

```python
(left_range) / (right_range)
```

A constant or nearly constant right-hand variable gives a zero or tiny range, causing division by zero or unstable scaling. It also assumes `GetXmin()`/`GetXmax()` are meaningful before autoscaling and that `left` is non-empty.

**Recommendation:** Compute explicit axis ranges after drawing or use normalized/right-axis-safe API support. Reject empty datasets and skip scaling if both ranges are invalid or zero.

#### 8. Combined-axis plotting does not add cosmetics

**Location:** `cls/BSPlotter.py:119-149`; `multiplotter.py:20-25`

`multiaxes()` reads `left[0].cosmetics`, but `BSPlot1DByTime.add_cosmetics()` has not been called by `multiplotter.py`. The combined plot therefore has no fill/run lines or labels.

**Recommendation:** Call `add_cosmetics()` once for all plots before constructing a combined canvas, and store cosmetics on a deduplicated owner.

#### 9. CMS header text is not rendered

**Location:** `cls/BSCanvas.py:39-46`; `cls/BSPlotter.py:30-40`

`DrawExtra()` draws CMS, extra, and luminosity text, but `BSPlot1D.save()`, `multiplot()`, and `multiaxes()` never invoke it. Saving a canvas also does not call this custom method, since `SaveAs()` is inherited ROOT behavior.

**Recommendation:** Call `can.DrawExtra()` immediately before every `SaveAs()` call.

#### 10. OOR fill/run labels can format integers with string concatenation

**Location:** `cls/BSPlotter.py:70-73`, `92-95`

Out-of-range fill/run labels use expressions such as `"since fill " + f` and `"since run " + r`. OMS fill and run IDs are strings or numeric values depending on the API payload; if numeric, these expressions raise `TypeError`.

**Recommendation:** Convert IDs to `str()` at the formatter boundary and centralize OOR label formatting.

#### 11. Plot objects require every requested field and use unsorted dictionaries

**Location:** `cls/BSPlotter.py:42-60`, `80-95`

Plot construction indexes `bs[self.yvar]` and `bs[self.xvar]` directly. One missing field in an otherwise valid record prevents the entire plot. TGraph input points also preserve dictionary insertion order rather than explicitly sorting by time, run, or fill.

**Recommendation:** Filter invalid entries individually, sort by the plot x key, and construct graphs with validated finite values and associated uncertainties where available.

#### 12. Unknown or empty fit selections lead to empty or invalid plots

**Location:** `cls/BSParser.py:16-21`, `24-39`; `cls/BSFormat.py:9-39`, `44-75`

`readTxtFile()` returns an empty dictionary if no chunks match a fit type. `fetch_timestamps_from_OMS()` then creates a pool with no useful work and self.beamspot becomes empty. Plot constructors then create graphs from empty arrays and cosmetics/axis ranges can behave unpredictably.

**Recommendation:** Raise a clear `NoMatchingFitsError`, or return a typed result and CLI exit code with a user-facing “no matching fits” message.

#### 13. Multiprocessing progress and stream handling are fragile

**Location:** `cls/MPUtils.py:10-43`; `cls/BSParser.py:31-36`

- `mp.Pool.map()` blocks until every job finishes, so the progress process is started only after work is complete.
- `pool.map()` is all-at-once rather than incremental, so memory use grows with result size.
- `threads=0`, negative values, booleans, or non-integral values are not validated.
- The progress process is not joined or cleaned up reliably.
- `_progressbar()` can call `os.get_terminal_size()` outside a terminal or fail in some redirected contexts.
- Worker exceptions are not converted to domain-level errors.

**Recommendation:** Use `pool.imap_unordered()` with a shared `queue` or call a pool executor that reports completed jobs. Validate positive integer stream counts and handle terminal size, interruption, and worker failures explicitly.

#### 14. Authentication occurs at import time and has to be performed even for offline parsing

**Location:** `cls/BSParser.py:12-15`; `cls/OMSUtils.py:3-7`

`AUTHENTICATOR=get_authenticator(...)` runs while the module is imported. Importing `BSParser` therefore initiates OMS authentication and external side effects, before argument parsing or a check for local-only operations.

**Recommendation:** Lazy-initialize/authenticate inside `fetch_timestamps_from_OMS()` or expose explicit `get_authenticator()`/`close()` lifecycle methods. Cache only after authentication succeeds.

### Low severity

#### 15. Text parsing is based on brittle substring and whitespace heuristics

**Location:** `cls/BSFormat.py:5-8`, `42-43`

The parser splits on display delimiters such as `Runnumber` and `for runs:`, then greps with substring tokens and `split(' ')`. It silently substitutes `-99` for missing values, and a malformed line can become `missing -99` or trigger `IndexError`/`ValueError`.

**Recommendation:** Implement a line-oriented parser with explicit field states, regex-validated numeric values, row count validation, and per-record parsing errors. Preserve raw parsing diagnostics instead of converting every missing value to `-99`.

#### 16. Covariance parsing is not structurally validated

**Location:** `cls/BSFormat.py:16-28`, `116`

Only the 9 expected covariance rows are built, but no check verifies 9 columns or that entries are finite. Negative diagonal covariance is handled later with `max(0, ...)`, but off-diagonal and malformed values are not validated.

**Recommendation:** Validate square symmetric covariance matrices, finite values, and non-negative variances, and include parsing metadata for corrected matrices.

#### 17. The approximate true-width error calculation appears to use a dimensions-incompatible value

**Location:** `cls/BSParser.py:132-133`

In approximate mode, `widthXTrueerr` computes:

```python
sqrt(s_true.n) * sqrt(widthXerr) / widthX
```

This mixes the true-width scale, covariance units, and nominal width; it is not obviously the propagated uncertainty. The same formula is used for Y. The comment explicitly states that non-approximate uncertainties look wrong, but approximate propagation is also not clearly justified.

**Recommendation:** Define and document the covariance propagation formula, use it consistently for both approximate and full modes, and add a numerical unit test that compares against an independent covariance transformation.

#### 18. OMS timestamps are parsed with a narrow format

**Location:** `cls/BSParser.py:42-43`, `63-70`

`datetime.strptime(..., "%Y-%m-%dT%H:%M:%SZ")` assumes UTC `Z` format and exact whole-second precision. It will fail for ISO-8601 offsets or fractional seconds and has no timezone object in the return type.

**Recommendation:** Parse OMS values using `datetime.fromisoformat()` after normalizing `Z`, and explicitly return timezone-aware UTC values.

#### 19. Fetch retry logic performs retries incorrectly

**Location:** `cls/OMSUtils.py:10-18`

The first `query.data()` call is immediately followed by up to five more calls through the `while` loop. It does not back off, check HTTP status, log failures, or expose the response text/status. A slow or transient API response may be repeated aggressively.

**Recommendation:** Use a small retry helper with bounded exponential backoff and final structured error reporting. Respect API rate limits and distinguish HTTP failures from JSON parsing failures.

#### 20. There is no automated test suite

**Location:** repository-wide

Only fixture and reference-output files exist under `test/`; no test runner or assertions are present. The supplied fixture does contain useful coverage for 373 successful fits, 52 failed-track fits, and 6 unknown-status fits, but no automated test invokes it.

**Recommendation:** Add pytest tests for:

- default and database parsing
- malformed/missing fields
- fit filtering
- duplicate IOV keys
- OMS payload conversion
- true-width covariance propagation
- empty OMS data
- CLI output paths
- graph creation and plotting with no/constant data

#### 21. Documentation and environment files have drifted

**Location:** `README.md:5-8`, `README.md:28-32`; `env/python3.11.yaml`

The README asks users to install `environment.yaml`, but only `env/python3.11.yaml` exists. It demonstrates `plotter.py`, but that file does not exist; the real entry points are `plotter_bylumi.py`, `plotter_byrun.py`, and `multiplotter.py`. The README recommends ROOT 6.30.4 while the environment pins ROOT 6.32.2. The environment name `beamspot-old` conflicts with the README's `beamspot` name.

**Recommendation:** Consolidate installation instructions around a stable environment filename and environment name. Update every command example and explicitly document authentication and the ROOT compatibility constraint.

#### 22. Dependencies are not represented as a small, testable project package

**Location:** repository-wide

The repository has a machine-exported 350-plus-line Conda YAML with an absolute environment prefix, exact platform builds, and no `pyproject.toml` or requirements file. This harms reproducibility on different machines and makes dependency-level testing difficult.

**Recommendation:** Add a minimal exported environment plus pinned direct dependencies. Do not rely on a machine-specific prefix. Add package metadata or at least a lock/reproducibility convention.

#### 23. There are commented-out production features and stale imports

**Location:** `plotter_byrun.py:17-20,38-40`; `multiplotter.py:2,33-36`

Unused imports (`MPManager`, `BSPlot1DByRun`, `BSPlot1DByFill`, `multiplot`) and large commented blocks make behavior unclear. The named methods `elaborate_runnumbers()` and `writeTxtFile()` are not implemented in `BSParser`, so the commented example is stale.

**Recommendation:** Remove dead code or implement and test intended features. Use a CLI deprecation/removal plan for old interfaces.

#### 24. Mutation of dictionaries in tabular export is avoidable and surprising

**Location:** `cls/BSFormat.py:78-116`

`FormatOutputTxt()` mutates each beamspot record with a `runnumber` key. This is a side effect and can make data dictionaries inconsistent across repeated exports or between PV/default modes.

**Recommendation:** Format `runnumber` from the dictionary key in the getter closure or build a local normalized row without mutating source data.

## Syntax and fixture verification

The following checks passed:

- All Python source files parsed successfully with `ast.parse()`.
- `python3 -m compileall -q cls *.py` completed with exit status 0.
- `FormatInputTxt(..., flavour='default')` on the supplied fixture returned:
  - `-1`: 6 IOV records
  - `0`: 52 IOV records
  - `2`: 373 IOV records

These checks confirm basic syntax and default-format parsing only. They do not validate OMS integration, ROOT rendering, authentication, or multiprocessing behavior.

## Prioritized remediation plan

1. **Fix the data contract:** normalize default/database/OMS fields and eliminate silent `-99`/missing-value behavior.
2. **Fix correctness bugs:** IOV end timestamp, tabular output path, database covariance, and OOR label types.
3. **Repair plotting:** CMS text, combined plots, axis scaling, empty data, sorting, and `p.name`/`var` defects.
4. **Make OMS and multiprocessing reliable:** lazy authentication, response validation, bounded retries, stream validation, and structured progress.
5. **Add tests:** begin with parser, covariance, OMS payload, and CLI unit tests using fixtures and mocks.
6. **Restore documentation and environment consistency:** correct README commands, environment file names, and dependency pins.
