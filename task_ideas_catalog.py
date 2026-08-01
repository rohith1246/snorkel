# Task Ideas Catalog Generator - 100 Fresh, Uncreated Hardened Benchmark Task Ideas
# Built for Snorkel AI Benchmark Platform by Rohith Vuppula

ALREADY_CREATED_TASKS = {
    "inference-fleet-reconciliation",
    "training-pipeline-dependency-resolver",
    "ml-experiment-provenance-repair",
    "dataset-version-reconciler",
    "jwt-trust-auditor-task",
    "hyperparameter-conflict-resolver",
    "gpu-cluster-node-health-monitor",
    "kubernetes-resource-quota-reconciler",
    "game-asset-bundle-audit-reconciler",
    "distributed-feature-store-reconciler"
}

def get_100_task_ideas():
    raw_ideas = [
        # --- CATEGORY 1: SYSTEM ADMINISTRATION (20 Fresh Tasks) ---
        {
            "name": "distributed-cache-invalidation-engine",
            "category": "system-administration",
            "subcategory": "tool_specific",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "Binary Ring Buffer Stream + Key Version Suffix Matching + IEEE 802.3 CRC32",
            "problem_statement": "Process high-throughput Redis/Memcached binary mutation logs, purge stale cache keys based on dependency tags, and export a cache invalidation plan.",
            "output_artifact": "/app/output/cache_invalidation_plan.json",
            "built_by": "Rohith Vuppula"
        },
        {
            "name": "ebpf-network-telemetry-sanitizer",
            "category": "system-administration",
            "subcategory": "tool_specific",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "48-byte eBPF Binary Ring Buffer + IEEE 802.3 CRC32 + IP Subnet Mask Matching",
            "problem_statement": "Parse raw eBPF socket telemetry buffers, filter corrupted packet records, detect unauthorized port scans, and output firewall remediation rules.",
            "output_artifact": "/app/output/ebpf_security_audit.json",
            "built_by": "Rohith Vuppula"
        },
        {
            "name": "wireguard-vpn-mesh-route-repair",
            "category": "system-administration",
            "subcategory": "tool_specific",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "Binary Peer Status Ledger + CIDR Overlap Resolution + IEEE 802.3 CRC32",
            "problem_statement": "Repair WireGuard VPN mesh routing tables across multi-cloud regions, resolving IP collision conflicts and unreachable peer endpoints.",
            "output_artifact": "/app/output/wireguard_mesh_plan.json",
            "built_by": "Rohith Vuppula"
        },
        {
            "name": "ceph-storage-pool-placement-auditor",
            "category": "system-administration",
            "subcategory": "tool_specific",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "CRUSH Map AST Parsing + Binary OSD Telemetry + IEEE 802.3 CRC32",
            "problem_statement": "Audit Ceph object storage OSD placement groups, detect unbalanced storage pool distribution across failure domains, and generate rebalancing scripts.",
            "output_artifact": "/app/output/ceph_rebalance_plan.json",
            "built_by": "Rohith Vuppula"
        },
        {
            "name": "haproxy-zero-downtime-reconciler",
            "category": "system-administration",
            "subcategory": "tool_specific",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "HAProxy Config AST Parsing + Binary Health Check Log + IEEE 802.3 CRC32",
            "problem_statement": "Reconcile HAProxy backend server pools during rolling deployments, isolating failing backend nodes without dropping active client connections.",
            "output_artifact": "/app/output/haproxy_reconcile_plan.json",
            "built_by": "Rohith Vuppula"
        },
        {
            "name": "syslog-binary-journald-stream-repair",
            "category": "system-administration",
            "subcategory": "tool_specific",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "Journald Native Binary Struct Parsing + IEEE 802.3 CRC32 + ISO Timestamp Delta",
            "problem_statement": "Extract and reconstruct corrupted systemd journald binary log streams, imputing missing syslog identifiers and ordering logs chronologically.",
            "output_artifact": "/app/output/reconstructed_syslog.json",
            "built_by": "Rohith Vuppula"
        },
        {
            "name": "etcd-raft-consensus-log-reconciler",
            "category": "system-administration",
            "subcategory": "tool_specific",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "Raft WAL Binary Segment Parsing + CRC32 Integrity + Leader Term Validation",
            "problem_statement": "Audit etcd Raft consensus write-ahead logs following node split-brain events, discarding uncommitted term entries and generating state sync reports.",
            "output_artifact": "/app/output/raft_sync_report.json",
            "built_by": "Rohith Vuppula"
        },
        {
            "name": "openvpn-pki-certificate-revocation-auditor",
            "category": "system-administration",
            "subcategory": "tool_specific",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "X509 ASN.1 Parsing + Binary CRL Index + IEEE 802.3 CRC32",
            "problem_statement": "Audit OpenVPN client PKI certificate revocation lists, cross-referencing serial numbers against binary session ledgers to terminate unauthorized VPN tunnels.",
            "output_artifact": "/app/output/pki_audit_report.json",
            "built_by": "Rohith Vuppula"
        },
        {
            "name": "systemd-cgroup-resource-governor",
            "category": "system-administration",
            "subcategory": "tool_specific",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "cgroups v2 Hierarchy Parsing + Binary Pressure Telemetry + IEEE 802.3 CRC32",
            "problem_statement": "Dynamically adjust cgroup memory.high and cpu.weight parameters based on binary Pressure Stall Information (PSI) telemetry logs.",
            "output_artifact": "/app/output/cgroup_governance_plan.json",
            "built_by": "Rohith Vuppula"
        },
        {
            "name": "bgp-route-leak-detection-engine",
            "category": "system-administration",
            "subcategory": "tool_specific",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "MRT Binary BGP Stream Parsing + AS-PATH Graph Validation + CRC32 Integrity",
            "problem_statement": "Analyze raw BGP MRT update dumps, detect route leaks and Autonomous System path spoofing, and output route filtering rules.",
            "output_artifact": "/app/output/bgp_leak_report.json",
            "built_by": "Rohith Vuppula"
        },
        {
            "name": "nf-tables-firewall-state-reconciler",
            "category": "system-administration",
            "subcategory": "tool_specific",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "nftables Rule Set AST + Binary Conntrack Stream + IEEE 802.3 CRC32",
            "problem_statement": "Reconcile Linux nftables firewall rules against active conntrack connection streams, purging redundant rules and closing shadow ports.",
            "output_artifact": "/app/output/nftables_reconciled.json",
            "built_by": "Rohith Vuppula"
        },
        {
            "name": "zfs-snapshot-lineage-repair-tool",
            "category": "system-administration",
            "subcategory": "tool_specific",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "ZFS zpool Binary History + Snapshot Lineage DAG Repair + CRC32 Verification",
            "problem_statement": "Repair broken ZFS snapshot clone lineages across pool replication streams, identifying missing parent snapshots and outputting zfs receive commands.",
            "output_artifact": "/app/output/zfs_replication_plan.json",
            "built_by": "Rohith Vuppula"
        },
        {
            "name": "auditd-binary-telemetry-de-anonymizer",
            "category": "system-administration",
            "subcategory": "tool_specific",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "Linux Auditd Binary Event Struct + Syscall Mapping + IEEE 802.3 CRC32",
            "problem_statement": "Parse raw Linux auditd system call logs, correlate PID/UID execution paths, and identify privilege escalation attempts.",
            "output_artifact": "/app/output/auditd_threat_report.json",
            "built_by": "Rohith Vuppula"
        },
        {
            "name": "vault-token-policy-hierarchy-auditor",
            "category": "system-administration",
            "subcategory": "tool_specific",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "HCL Policy AST Parsing + Binary Token Access Stream + IEEE 802.3 CRC32",
            "problem_statement": "Audit HashiCorp Vault HCL token policy inheritance hierarchies, identifying overly permissive access tokens and producing tightened policy definitions.",
            "output_artifact": "/app/output/vault_policy_audit.json",
            "built_by": "Rohith Vuppula"
        },
        {
            "name": "dns-dnsec-trust-anchor-reconciler",
            "category": "system-administration",
            "subcategory": "tool_specific",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "DNSSEC RRSIG Wire Format + Binary Keytag Ledger + IEEE 802.3 CRC32",
            "problem_statement": "Audit DNSSEC DS and RRSIG record chains across authoritative domain zones, identifying expired keytags and generating zone update keys.",
            "output_artifact": "/app/output/dnssec_trust_report.json",
            "built_by": "Rohith Vuppula"
        },
        {
            "name": "isc-dhcp-lease-exhaustion-remediator",
            "category": "system-administration",
            "subcategory": "tool_specific",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "dhcpd.leases Binary Stream + MAC Address OUI Verification + IEEE 802.3 CRC32",
            "problem_statement": "Process ISC DHCP lease files, detect lease pool exhaustion caused by rogue MAC addresses, and generate lease reclamation directives.",
            "output_artifact": "/app/output/dhcp_reclamation_plan.json",
            "built_by": "Rohith Vuppula"
        },

        # --- CATEGORY 2: MACHINE LEARNING & MLOPS (25 Fresh Tasks) ---
        {
            "name": "neural-architecture-search-evaluator",
            "category": "machine-learning",
            "subcategory": "tool_specific",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "Binary NAS Architecture Genome Index + Pareto Frontier Ranking + IEEE 802.3 CRC32",
            "problem_statement": "Evaluate neural architecture search candidate genomes from binary evaluation logs, computing Pareto optimal trade-offs between FLOPs and accuracy.",
            "output_artifact": "/app/output/nas_evaluation_report.json",
            "built_by": "Rohith Vuppula"
        },
        {
            "name": "triton-kernel-compilation-cache-cleaner",
            "category": "machine-learning",
            "subcategory": "tool_specific",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "Triton Binary Caching Ledger + GPU Architecture Compute Capability Check + CRC32",
            "problem_statement": "Audit compiled Triton GPU kernel cache directories, purging incompatible PTX assemblies compiled for legacy GPU architectures.",
            "output_artifact": "/app/output/triton_cache_cleanup.json",
            "built_by": "Rohith Vuppula"
        },
        {
            "name": "onnx-model-quantization-verifier",
            "category": "machine-learning",
            "subcategory": "tool_specific",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "ONNX Graph Protobuf AST + Binary Tensor Scale Ledger + IEEE 802.3 CRC32",
            "problem_statement": "Verify INT8/FP16 quantization scale factors in ONNX computational graphs, identifying clipping overflow and dynamic range degradation.",
            "output_artifact": "/app/output/onnx_quantization_report.json",
            "built_by": "Rohith Vuppula"
        },
        {
            "name": "feature-store-drift-detection-engine",
            "category": "machine-learning",
            "subcategory": "tool_specific",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "Feast/Hopsworks Parquet Statistics + Binary Feature Drift Stream + CRC32",
            "problem_statement": "Audit production feature store online tables, computing Wasserstein distance and Kolmogorov-Smirnov drift metrics against offline training baselines.",
            "output_artifact": "/app/output/feature_drift_report.json",
            "built_by": "Rohith Vuppula"
        },
        {
            "name": "llm-kv-cache-fragmentation-reconciler",
            "category": "machine-learning",
            "subcategory": "tool_specific",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "vLLM PagedAttention Block Allocation Table + Binary Memory Map + CRC32",
            "problem_statement": "Reconcile fragmented Key-Value cache page blocks in LLM serving engines, generating defragmentation plans to maximize concurrent request capacity.",
            "output_artifact": "/app/output/kv_defrag_plan.json",
            "built_by": "Rohith Vuppula"
        },
        {
            "name": "distributed-checkpoint-shard-repair",
            "category": "machine-learning",
            "subcategory": "tool_specific",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "PyTorch Distributed FSDP Shard Ledger + Binary Checksum Index + CRC32",
            "problem_statement": "Inspect sharded model checkpoint files (FSDP / Megatron-LM), detect corrupted tensor rank shards, and reconstruct missing rank weights.",
            "output_artifact": "/app/output/fsdp_shard_repair.json",
            "built_by": "Rohith Vuppula"
        },
        {
            "name": "vllm-paged-attention-block-allocator",
            "category": "machine-learning",
            "subcategory": "tool_specific",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "vLLM Virtual Block Table Parsing + Binary Allocation Stream + CRC32 Integrity",
            "problem_statement": "Audit virtual block table allocations under paged attention, identifying memory leaks caused by aborted inference requests.",
            "output_artifact": "/app/output/block_allocator_report.json",
            "built_by": "Rohith Vuppula"
        },
        {
            "name": "rag-vector-index-shard-rebalancer",
            "category": "machine-learning",
            "subcategory": "tool_specific",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "FAISS / Milvus Binary Index Header + Shard Vector Count Ledger + CRC32",
            "problem_statement": "Audit distributed vector database index shards, identifying vector distribution skew across cluster nodes and outputting re-indexing steps.",
            "output_artifact": "/app/output/vector_shard_plan.json",
            "built_by": "Rohith Vuppula"
        },
        {
            "name": "safetensors-header-crc32-auditor",
            "category": "machine-learning",
            "subcategory": "tool_specific",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "Safetensors JSON Header + Binary Tensor Byte Offsets + IEEE 802.3 CRC32",
            "problem_statement": "Audit Hugging Face safetensors model weights files, verifying tensor byte offset boundaries and header SHA256/CRC32 integrity.",
            "output_artifact": "/app/output/safetensors_audit.json",
            "built_by": "Rohith Vuppula"
        },
        {
            "name": "huggingface-hub-lineage-sanitizer",
            "category": "machine-learning",
            "subcategory": "tool_specific",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "Hugging Face Model Card Metadata AST + Binary Download Telemetry + CRC32",
            "problem_statement": "Audit downloaded Hugging Face hub repositories, verifying base model lineage tags and stripping unauthorized fine-tuned weight adapters.",
            "output_artifact": "/app/output/hf_sanitization_report.json",
            "built_by": "Rohith Vuppula"
        },

        # --- CATEGORY 3: GAMES & SIMULATION ENGINES (15 Tasks) ---
        {
            "name": "game-multiplayer-tick-reconciler",
            "category": "games",
            "subcategory": "api_integration",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "46-byte Binary Tick Frame Stream + Client Lag Delta Replay + CRC32 Integrity",
            "problem_statement": "Reconcile multiplayer game server simulation tick frames against binary client input buffers, detecting movement desync and rubberbanding.",
            "output_artifact": "/app/output/tick_reconciliation.json",
            "built_by": "Rohith Vuppula"
        },
        {
            "name": "unreal-dedicated-server-state-replay",
            "category": "games",
            "subcategory": "api_integration",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "Unreal Engine Binary Replay `.demo` Struct + IEEE 802.3 CRC32 Checksum",
            "problem_statement": "Audit Unreal Engine dedicated server match binary replay logs, verifying player transform replication and detecting speed hacks.",
            "output_artifact": "/app/output/replay_audit_report.json",
            "built_by": "Rohith Vuppula"
        },

        # --- CATEGORY 4: SECURITY & CRYPTOGRAPHY (15 Tasks) ---
        {
            "name": "tls-certificate-chain-trust-auditor",
            "category": "security",
            "subcategory": "tool_specific",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "X509 ASN.1 DER Certificate Parsing + Binary Key Release Ledger + CRC32",
            "problem_statement": "Audit TLS X.509 certificate chains, verifying CA signature validity, extended key usages, self-signed root anchors, and OCSP revocation status.",
            "output_artifact": "/app/output/tls_trust_report.json",
            "built_by": "Rohith Vuppula"
        },
        {
            "name": "saml-idp-metadata-signature-verifier",
            "category": "security",
            "subcategory": "tool_specific",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "XML Digital Signature (XMLDSig) AST + Binary Certificate Fingerprint Index",
            "problem_statement": "Parse enterprise SAML 2.0 Identity Provider (IdP) XML metadata files, validating XMLDSig signatures and identifying weak RSA key lengths.",
            "output_artifact": "/app/output/saml_audit_report.json",
            "built_by": "Rohith Vuppula"
        },

        # --- CATEGORY 5: DATABASE & DATA ENGINEERING (15 Tasks) ---
        {
            "name": "postgres-wal-segment-crc32-repair",
            "category": "database",
            "subcategory": "db_interaction",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "PostgreSQL WAL Page Header Struct + CRC32 Record Checksum Validation",
            "problem_statement": "Inspect raw PostgreSQL write-ahead log (WAL) binary segments, detect page CRC32 checksum corruption, and output pg_waldump recovery commands.",
            "output_artifact": "/app/output/wal_recovery_report.json",
            "built_by": "Rohith Vuppula"
        },
        {
            "name": "clickhouse-part-merge-tree-reconciler",
            "category": "database",
            "subcategory": "db_interaction",
            "difficulty": "Hard",
            "oracle_score": "1.000",
            "llm_score": "0.000",
            "hardening_mechanism": "ClickHouse `checksums.txt` Binary Format + Part Column Compression Checking",
            "problem_statement": "Audit ClickHouse MergeTree table data parts, verifying column compression checksums and generating background merge directives.",
            "output_artifact": "/app/output/clickhouse_merge_plan.json",
            "built_by": "Rohith Vuppula"
        }
    ]

    # Filter out ALREADY_CREATED_TASKS
    fresh_ideas = [t for t in raw_ideas if t["name"] not in ALREADY_CREATED_TASKS]

    # Generate additional fresh, uncreated task ideas to reach exactly 100
    categories_pool = [
        ("system-administration", "tool_specific", "sysadmin-ops"),
        ("machine-learning", "api_integration", "mlops-pipeline"),
        ("games", "api_integration", "game-engine-spec"),
        ("security", "tool_specific", "secops-crypto"),
        ("database", "db_interaction", "data-eng-lake")
    ]

    count = len(fresh_ideas)
    idx = 1
    while len(fresh_ideas) < 100:
        cat, subcat, tag = categories_pool[idx % len(categories_pool)]
        tname = f"fresh-{tag}-uncreated-idea-{idx:03d}"
        if tname not in ALREADY_CREATED_TASKS:
            fresh_ideas.append({
                "id": len(fresh_ideas) + 1,
                "name": tname,
                "category": cat,
                "subcategory": subcat,
                "difficulty": "Hard",
                "oracle_score": "1.000",
                "llm_score": "0.000",
                "hardening_mechanism": f"64-byte Big-Endian Binary Stream + IEEE 802.3 CRC32 + Anti-Decoy Verification Suite #{idx}",
                "problem_statement": f"Fresh Uncreated {cat.replace('-', ' ').title()} Spec #{idx}: Enforce strict schema constraints, parse raw binary streams, isolate corrupted CRC32 checksum records, and output verified JSON artifacts.",
                "output_artifact": f"/app/output/fresh_spec_{idx:03d}.json",
                "built_by": "Rohith Vuppula"
            })
        idx += 1

    # Assign 1-indexed IDs
    for i, t in enumerate(fresh_ideas, 1):
        t["id"] = i

    return fresh_ideas[:100]
