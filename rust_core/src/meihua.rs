#[cfg(feature = "python")]
use pyo3::prelude::*;

#[cfg_attr(feature = "python", pyfunction)]
pub fn mei_hua_hexagram_from_time(year: i32, month: i32, day: i32, hour: i32) -> (usize, usize, usize) {
    let upper = (year + month + day) % 8;
    let upper_trigram = if upper == 0 { 8 } else { upper as usize };

    let lower = (year + month + day + hour) % 8;
    let lower_trigram = if lower == 0 { 8 } else { lower as usize };

    let moving = (year + month + day + hour) % 6;
    let moving_line = if moving == 0 { 6 } else { moving as usize };

    (upper_trigram, lower_trigram, moving_line)
}
