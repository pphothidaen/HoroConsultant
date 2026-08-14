/*!
 * rust_core/src/liu_yao.rs
 * High-performance Liu Yao (六爻) computation core.
 */

use pyo3::prelude::*;

/// Generate Na Jia (納甲) Earthly Branches for a trigram.
/// Trigram indices based on binary: 
/// 0:Kun, 1:Zhen, 2:Kan, 3:Dui, 4:Gen, 5:Li, 6:Xun, 7:Qian
/// Returns a vector of 3 branch indices (0-11 for 子-亥).
#[pyfunction]
pub fn liu_yao_najia(trigram_idx: usize, is_upper: bool) -> Vec<usize> {
    match trigram_idx {
        7 | 1 => { // Qian & Zhen
            if is_upper { vec![6, 8, 10] } else { vec![0, 2, 4] }
        }
        2 => { // Kan
            if is_upper { vec![8, 10, 0] } else { vec![2, 4, 6] }
        }
        4 => { // Gen
            if is_upper { vec![10, 0, 2] } else { vec![4, 6, 8] }
        }
        0 => { // Kun
            if is_upper { vec![1, 11, 9] } else { vec![7, 5, 3] }
        }
        6 => { // Xun
            if is_upper { vec![7, 5, 3] } else { vec![1, 11, 9] }
        }
        5 => { // Li
            if is_upper { vec![9, 7, 5] } else { vec![3, 1, 11] }
        }
        3 => { // Dui
            if is_upper { vec![11, 9, 7] } else { vec![5, 3, 1] }
        }
        _ => vec![0, 0, 0]
    }
}

/// Calculate the Five Relatives (五親) based on line element and day master element.
/// Elements: 0=Wood, 1=Fire, 2=Earth, 3=Metal, 4=Water.
#[pyfunction]
pub fn liu_yao_five_relatives(line_element: usize, day_master_element: usize) -> String {
    if line_element == day_master_element {
        "兄弟".to_string() // Sibling
    } else if (day_master_element + 1) % 5 == line_element {
        "子孫".to_string() // Offspring
    } else if (line_element + 1) % 5 == day_master_element {
        "父母".to_string() // Parent
    } else if (day_master_element + 2) % 5 == line_element {
        "妻財".to_string() // Wife-Wealth
    } else if (line_element + 2) % 5 == day_master_element {
        "官鬼".to_string() // Officer-Ghost
    } else {
        "未知".to_string() // Unknown
    }
}
