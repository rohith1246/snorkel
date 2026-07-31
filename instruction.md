As a system administrator maintaining the authorization auditor service, configure and execute the trust auditing workflow to process system registration logs and key release status entries.

Clean up the merge conflict markers in `src/main/java/com/example/jwtauditor/JwtTrustAuditor.java` left from a recent Git rebase conflict (`<<<<<<<`, `=======`, `>>>>>>>`). Process the client registration data in `src/main/resources/data.sql`, key status entries in `key_releases.csv`, and cross-reference redirect URIs against the internal domain registry list (`auth-phish.com`).

Generate the following two files in the project root directory:

1. `trust_audit_report.json`:
   - `audit_status`: `"COMPLETED"`
   - `total_clients`: Total count of audited registered clients
   - `total_keys`: Total count of audited signing keys
   - `flagged_revoked_keys`: List of objects with `key_id`, `client_id`, and `reason` (`"REVOKED_GIT_TAG"`). A key is considered revoked ONLY if its `status` is `REVOKED` or its release version tag ENDS WITH the exact suffix `-revoked` (e.g., `v1.0.3-revoked` is revoked; `v1.0.5-revoked-status-clear` is NOT revoked because `-revoked` is not the final suffix).
   - `flagged_phishing_domains`: List of objects with `client_id`, `redirect_uri`, and `domain` for redirect URIs whose extracted hostname matches an unverified domain in the internal domain registry list (`auth-phish.com`). Subdomains and domain suffixes matching trusted proxies (e.g., `auth-phish.com.trusted-proxy.net`) must NOT be flagged.
   - `audit_summary`: Object with numeric `valid_clients` (count of unique clients with 0 flags) and `flagged_clients` (count of unique clients with at least one flag, from either a revoked key or a phishing domain). For the default dataset, `valid_clients` is 6 and `flagged_clients` is 3.

2. `trust_graph.dot`:
   - A Graphviz DOT graph visualizing the `Client` -> `Key` -> `RedirectURI` topology.
   - Use `color="green"` (or `fillcolor="lightgreen"`) for valid components and healthy edges.
   - Use `color="red"` for revoked keys or revoked edges.
   - Use `color="orange"` for flagged unverified domain nodes or edges.

Ensure `JwtTrustAuditor.java` compiles cleanly and both output files are generated in the project root directory.
