//! Merkle provenance and acyclicity helpers for the v3 derivation DAG.
//!
//! The hash format follows the v3 storage specification:
//! `SHA256(canonical_payload || "||" || sorted_parent_hashes)`.
//! Root nodes use `ROOT_NODE` in place of the parent hash concatenation.

use std::collections::{HashMap, HashSet, VecDeque};

const SHA256_INITIAL_STATE: [u32; 8] = [
    0x6a09_e667,
    0xbb67_ae85,
    0x3c6e_f372,
    0xa54f_f53a,
    0x510e_527f,
    0x9b05_688c,
    0x1f83_d9ab,
    0x5be0_cd19,
];

const SHA256_ROUND_CONSTANTS: [u32; 64] = [
    0x428a_2f98,
    0x7137_4491,
    0xb5c0_fbcf,
    0xe9b5_dba5,
    0x3956_c25b,
    0x59f1_11f1,
    0x923f_82a4,
    0xab1c_5ed5,
    0xd807_aa98,
    0x1283_5b01,
    0x2431_85be,
    0x550c_7dc3,
    0x72be_5d74,
    0x80de_b1fe,
    0x9bdc_06a7,
    0xc19b_f174,
    0xe49b_69c1,
    0xefbe_4786,
    0x0fc1_9dc6,
    0x240c_a1cc,
    0x2de9_2c6f,
    0x4a74_84aa,
    0x5cb0_a9dc,
    0x76f9_88da,
    0x983e_5152,
    0xa831_c66d,
    0xb003_27c8,
    0xbf59_7fc7,
    0xc6e0_0bf3,
    0xd5a7_9147,
    0x06ca_6351,
    0x1429_2967,
    0x27b7_0a85,
    0x2e1b_2138,
    0x4d2c_6dfc,
    0x5338_0d13,
    0x650a_7354,
    0x766a_0abb,
    0x81c2_c92e,
    0x9272_2c85,
    0xa2bf_e8a1,
    0xa81a_664b,
    0xc24b_8b70,
    0xc76c_51a3,
    0xd192_e819,
    0xd699_0624,
    0xf40e_3585,
    0x106a_a070,
    0x19a4_c116,
    0x1e37_6c08,
    0x2748_774c,
    0x34b0_bcb5,
    0x391c_0cb3,
    0x4ed8_aa4a,
    0x5b9c_ca4f,
    0x682e_6ff3,
    0x748f_82ee,
    0x78a5_636f,
    0x84c8_7814,
    0x8cc7_0208,
    0x90be_fffa,
    0xa450_6ceb,
    0xbef9_a3f7,
    0xc671_78f2,
];

fn sha256_hex(input: &[u8]) -> String {
    let bit_length = (input.len() as u64) * 8;
    let mut message = input.to_vec();
    message.push(0x80);
    while message.len() % 64 != 56 {
        message.push(0);
    }
    message.extend_from_slice(&bit_length.to_be_bytes());

    let mut state = SHA256_INITIAL_STATE;
    for chunk in message.chunks_exact(64) {
        let mut schedule = [0u32; 64];
        for (index, word) in schedule[..16].iter_mut().enumerate() {
            let offset = index * 4;
            *word = u32::from_be_bytes([
                chunk[offset],
                chunk[offset + 1],
                chunk[offset + 2],
                chunk[offset + 3],
            ]);
        }
        for index in 16..64 {
            let small_sigma0 = schedule[index - 15].rotate_right(7)
                ^ schedule[index - 15].rotate_right(18)
                ^ (schedule[index - 15] >> 3);
            let small_sigma1 = schedule[index - 2].rotate_right(17)
                ^ schedule[index - 2].rotate_right(19)
                ^ (schedule[index - 2] >> 10);
            schedule[index] = schedule[index - 16]
                .wrapping_add(small_sigma0)
                .wrapping_add(schedule[index - 7])
                .wrapping_add(small_sigma1);
        }

        let [mut a, mut b, mut c, mut d, mut e, mut f, mut g, mut h] = state;
        for index in 0..64 {
            let big_sigma1 = e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25);
            let choice = (e & f) ^ ((!e) & g);
            let temporary1 = h
                .wrapping_add(big_sigma1)
                .wrapping_add(choice)
                .wrapping_add(SHA256_ROUND_CONSTANTS[index])
                .wrapping_add(schedule[index]);
            let big_sigma0 = a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22);
            let majority = (a & b) ^ (a & c) ^ (b & c);
            let temporary2 = big_sigma0.wrapping_add(majority);
            [h, g, f, e, d, c, b, a] = [
                g,
                f,
                e,
                d.wrapping_add(temporary1),
                c,
                b,
                a,
                temporary1.wrapping_add(temporary2),
            ];
        }

        for (value, addition) in state.iter_mut().zip([a, b, c, d, e, f, g, h]) {
            *value = value.wrapping_add(addition);
        }
    }

    state.iter().map(|word| format!("{word:08x}")).collect()
}

/// Compute a deterministic SHA-256 content hash for a derivation-DAG node.
///
/// `payload_canonical_json` must already be RFC 8785/JCS canonical JSON. Parent
/// hashes are sorted lexicographically before concatenation, so callers can
/// provide them in any order without changing the resulting hash.
pub fn compute_merkle_node_hash(payload_canonical_json: &str, parent_hashes: &[String]) -> String {
    let parent_material = if parent_hashes.is_empty() {
        "ROOT_NODE".to_owned()
    } else {
        let mut sorted_parents = parent_hashes.to_vec();
        sorted_parents.sort_unstable();
        sorted_parents.concat()
    };

    let mut input = Vec::with_capacity(payload_canonical_json.len() + 2 + parent_material.len());
    input.extend_from_slice(payload_canonical_json.as_bytes());
    input.extend_from_slice(b"||");
    input.extend_from_slice(parent_material.as_bytes());

    sha256_hex(&input)
}

/// Return whether `to_node` is reachable from `from_node` in a directed graph.
///
/// Edges are represented as `(source, destination)` pairs. The traversal is
/// iterative and tracks visited nodes, so malformed cyclic input cannot cause
/// unbounded recursion or repeated work.
pub fn check_reachability(edges: &[(String, String)], from_node: &str, to_node: &str) -> bool {
    if from_node == to_node {
        return true;
    }

    let mut adjacency: HashMap<&str, Vec<&str>> = HashMap::new();
    for (source, destination) in edges {
        adjacency
            .entry(source.as_str())
            .or_default()
            .push(destination.as_str());
    }

    let mut queue = VecDeque::from([from_node]);
    let mut visited = HashSet::new();
    visited.insert(from_node);

    while let Some(current) = queue.pop_front() {
        if let Some(neighbors) = adjacency.get(current) {
            for &neighbor in neighbors {
                if neighbor == to_node {
                    return true;
                }
                if visited.insert(neighbor) {
                    queue.push_back(neighbor);
                }
            }
        }
    }

    false
}

#[cfg(test)]
mod tests {
    use super::{check_reachability, compute_merkle_node_hash};

    #[test]
    fn hash_generation_is_deterministic_and_parent_order_independent() {
        let parents = vec!["parent-b".to_owned(), "parent-a".to_owned()];
        let reordered = vec!["parent-a".to_owned(), "parent-b".to_owned()];

        let first = compute_merkle_node_hash(r#"{"stage":"L2"}"#, &parents);
        let second = compute_merkle_node_hash(r#"{"stage":"L2"}"#, &reordered);

        assert_eq!(first, second);
        assert_eq!(first.len(), 64);
        assert!(first.chars().all(|character| character.is_ascii_hexdigit()));
    }

    #[test]
    fn sha256_implementation_matches_known_vector() {
        assert_eq!(
            super::sha256_hex(b"abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        );
    }

    #[test]
    fn hash_changes_when_payload_changes() {
        let parents = vec!["parent-a".to_owned()];

        let original = compute_merkle_node_hash(r#"{"value":1}"#, &parents);
        let altered = compute_merkle_node_hash(r#"{"value":2}"#, &parents);

        assert_ne!(original, altered);
    }

    #[test]
    fn root_hash_uses_root_node_marker() {
        let root = compute_merkle_node_hash(r#"{"stage":"L1"}"#, &[]);
        let explicit_marker =
            compute_merkle_node_hash(r#"{"stage":"L1"}"#, &["ROOT_NODE".to_owned()]);

        assert_eq!(root, explicit_marker);
    }

    #[test]
    fn reachability_finds_paths_and_rejects_missing_paths() {
        let edges = vec![
            ("A".to_owned(), "B".to_owned()),
            ("B".to_owned(), "C".to_owned()),
            ("C".to_owned(), "D".to_owned()),
        ];

        assert!(check_reachability(&edges, "A", "D"));
        assert!(check_reachability(&edges, "B", "C"));
        assert!(!check_reachability(&edges, "D", "A"));
        assert!(!check_reachability(&edges, "A", "missing"));
    }

    #[test]
    fn cycle_guard_detects_a_b_c_a_cycle() {
        let existing_edges = vec![
            ("A".to_owned(), "B".to_owned()),
            ("B".to_owned(), "C".to_owned()),
        ];

        // Before inserting C -> A, the insertion guard checks Reachable(A, C).
        assert!(check_reachability(&existing_edges, "A", "C"));
        assert!(!check_reachability(&existing_edges, "C", "A"));

        let cycle_edges = vec![
            ("A".to_owned(), "B".to_owned()),
            ("B".to_owned(), "C".to_owned()),
            ("C".to_owned(), "A".to_owned()),
        ];
        assert!(check_reachability(&cycle_edges, "A", "C"));
        assert!(check_reachability(&cycle_edges, "B", "A"));
        assert!(check_reachability(&cycle_edges, "C", "B"));
    }
}
