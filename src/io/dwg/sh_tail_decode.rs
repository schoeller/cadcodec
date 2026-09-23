//! Phase B tail decoders for the raw-retained solid-history node classes.
//!
//! The four raw-retained tails (`SolidHistorySweep::shsw_raw_tail` for
//! ACSH_SWEEP_CLASS and ACSH_EXTRUSION_CLASS, `SolidHistoryLoft::raw_tail`,
//! `SolidHistoryRevolve::raw_tail`) are captured verbatim by the reader
//! (Phase A); these decoders project the SEMANTIC content of those bits
//! into the typed tail views on the model. The classes are DEBUGGING
//! classes in gold — there is no oracle walk for their payloads — so
//! every anchor here is derived from the two non-oracle instruments
//! documented in IMPLEMENTATION.md §18.5:
//!
//! 1. Cross-specimen comparison: all four fixtures per family carry
//!    bit-identical tails across DWG 2007/2010/2013/2018, so the shapes
//!    below are version-portable statements about the wires themselves.
//! 2. The R2010 live-oracle fragment: where a tail entry overlaps values
//!    gold parses elsewhere (the 3DSOLID wireframe anchor read from the
//!    same modeler backing), the gold-parsed value names the semantics
//!    (Polysolid: direction unit components and the doubled segment end;
//!    Extrude: the (0, 0, 2.0) extrusion length vector; Loft: the 5.0
//!    top height with the two 90-degree draft angles).
//!
//! Write rule: the captured raw tail is the authority and re-emitted
//! verbatim; the decoders merely supply a typed view. A writer-token
//! re-encode exists for the raw LE64 spans (same bit length always):
//! `render_*_tail` splices the current model values into the stored bits
//! only where they differ from the decode, so a programmatic field edit
//! lands bit-locally while an untouched record stays byte-identical.

use crate::objects::{SolidHistoryLoftTail, SolidHistoryRevolveTail, SolidHistorySweepTail};

/// A bit range within a tail, MSB-packed ([start, start+len)).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) struct Span {
    pub start: u32,
    pub len: u32,
}

/// MSB-packed read/write window over the captured tail bytes.
struct TailBits {
    bytes: Vec<u8>,
    bit_len: u32,
}

impl TailBits {
    fn new(bytes: &[u8], bit_len: u32) -> Self {
        Self {
            bytes: bytes.to_vec(),
            bit_len,
        }
    }

    fn get(&self, index: u32) -> Option<u8> {
        if index >= self.bit_len {
            return None;
        }
        Some((self.bytes[(index / 8) as usize] >> (7 - index % 8)) & 1)
    }

    fn code(&self, index: u32) -> Option<u8> {
        Some((self.get(index)? << 1) | self.get(index + 1)?)
    }

    /// Raw LE64 double at `start`: the eight wire bytes (each MSB-first on
    /// the DWG bit stream) are the double's little-endian bytes in
    /// transmission order (the same convention as `DwgBitReader::read_raw_double`).
    fn le64(&self, start: u32) -> Option<f64> {
        if start.checked_add(64)? > self.bit_len {
            return None;
        }
        let mut raw = [0u8; 8];
        for (j, byte) in raw.iter_mut().enumerate() {
            for k in 0..8 {
                // Wire bit (start + 8j) is the byte's MSB (weight 2^7).
                *byte |= self.get(start + (j as u32) * 8 + (7 - k as u32))? << k;
            }
        }
        Some(f64::from_bits(u64::from_le_bytes(raw)))
    }

    fn set_le64(&mut self, start: u32, value: f64) -> bool {
        if start.checked_add(64).map_or(true, |end| end > self.bit_len) {
            return false;
        }
        let raw = value.to_bits().to_le_bytes();
        for (j, byte) in raw.iter().enumerate() {
            for k in 0..8 {
                let bit = (byte >> k) & 1;
                let index = start + (j as u32) * 8 + (7 - k as u32);
                let byte_slot = &mut self.bytes[(index / 8) as usize];
                let mask = 1 << (7 - index % 8);
                if bit == 1 {
                    *byte_slot |= mask;
                } else {
                    *byte_slot &= !mask;
                }
            }
        }
        true
    }

    fn set_pair(&mut self, start: u32, code: u8) -> bool {
        if start.checked_add(2).map_or(true, |end| end > self.bit_len) {
            return false;
        }
        for (offset, bit) in [(0, code >> 1), (1, code & 1)] {
            let byte = &mut self.bytes[((start + offset) / 8) as usize];
            let mask = 1 << (7 - (start + offset) % 8);
            if bit == 1 {
                *byte |= mask;
            } else {
                *byte &= !mask;
            }
        }
        true
    }

    /// Byte-aligned plausible-double run starting at `start` (start must
    /// itself be byte aligned). Returns (positions, values) until the first
    /// implausible entry.
    fn aligned_run(&self, start: u32) -> (Vec<u32>, Vec<f64>) {
        debug_assert_eq!(start % 8, 0);
        let mut positions = Vec::new();
        let mut values = Vec::new();
        let mut pos = start;
        while let Some(value) = self.le64(pos) {
            if !plausible(value) {
                break;
            }
            positions.push(pos);
            values.push(value);
            pos += 64;
        }
        (positions, values)
    }
}

/// IEEE-plausibility gate used by the collectors: finite, not denormal
/// junk and inside a sane modeling range. `0.0` is accepted (raw zero
/// runs appear inside byte-aligned geometry blocks).
fn plausible(value: f64) -> bool {
    if !value.is_finite() {
        return false;
    }
    let abs = value.abs();
    if abs == 0.0 {
        return true;
    }
    (1e-4..=1e12).contains(&abs)
}

/// Plausibility gate for raw BD ('00'-marked) doubles: a wire writer
/// encodes an exact `0.0` as the short BD form, so a raw-marked zero is
/// always a misaligned alias, not an entry.
fn plausible_raw(value: f64) -> bool {
    plausible(value) && value != 0.0
}

/// Decoded BD form with its bit span.
#[derive(Debug, Clone, Copy)]
struct BdEntry {
    value: f64,
    span: Span,
}

/// Read one BD at `pos`. Returns the entry or `None` when the form does
/// not fit the window. The reserved '11' code decodes as 0.0 (matching
/// the bitcode table) so callers decide whether it is still acceptable.
fn read_bd(bits: &TailBits, pos: u32) -> Option<BdEntry> {
    let code = bits.code(pos)?;
    match code {
        0b00 => {
            let value = bits.le64(pos + 2)?;
            Some(BdEntry {
                value,
                span: Span {
                    start: pos,
                    len: 66,
                },
            })
        }
        0b01 => Some(BdEntry {
            value: 1.0,
            span: Span { start: pos, len: 2 },
        }),
        0b10 => Some(BdEntry {
            value: 0.0,
            span: Span { start: pos, len: 2 },
        }),
        _ => Some(BdEntry {
            value: 0.0,
            span: Span { start: pos, len: 2 },
        }),
    }
}

/// Maximum entries collected in a head run (shape guard).
const MAX_HEAD: usize = 16;
/// Maximum raw BD entries collected (shape guard).
const MAX_RAWS: usize = 64;

/// Sweep/revolve shared head: BD shorts until the first raw/reserved
/// form. Returns the values with their spans and the end position.
fn read_head_shorts(bits: &TailBits, start: u32) -> (Vec<f64>, Vec<Span>, u32) {
    let mut values = Vec::new();
    let mut spans = Vec::new();
    let mut pos = Some(start);
    while let Some(position) = pos {
        if values.len() >= MAX_HEAD {
            break;
        }
        match bits.code(position) {
            Some(0b01) => {
                values.push(1.0);
                spans.push(Span {
                    start: position,
                    len: 2,
                });
                pos = Some(position + 2);
            }
            Some(0b10) => {
                values.push(0.0);
                spans.push(Span {
                    start: position,
                    len: 2,
                });
                pos = Some(position + 2);
            }
            _ => break,
        }
    }
    let end = spans.last().map_or(start, |span| span.start + span.len);
    (values, spans, end)
}

/// Sweep-family frame entries: raw BD doubles found at '00' markers
/// between `start` and `bound` (exclusive), advancing 2 bits at a time
/// when a marker does not decode to a plausible raw double.
fn scan_raws(bits: &TailBits, start: u32, bound: u32) -> (Vec<f64>, Vec<Span>) {
    let mut values = Vec::new();
    let mut spans = Vec::new();
    let mut pos = start;
    while values.len() < MAX_RAWS && pos + 66 <= bound {
        if bits.code(pos) == Some(0b00) {
            if let Some(value) = bits.le64(pos + 2) {
                if plausible_raw(value) {
                    values.push(value);
                    spans.push(Span {
                        start: pos + 2,
                        len: 64,
                    });
                    pos += 66;
                    continue;
                }
            }
        }
        pos += 2;
    }
    (values, spans)
}

/// Byte-aligned plausible-double runs with at least `min_entries` members.
fn aligned_runs(bits: &TailBits, min_entries: usize, max_runs: usize) -> Vec<(Vec<u32>, Vec<f64>)> {
    let mut runs = Vec::new();
    let mut pos = 0u32;
    while pos + 64 <= bits.bit_len {
        if pos % 8 != 0 {
            pos += 1;
            continue;
        }
        let (positions, values) = bits.aligned_run(pos);
        if positions.len() >= min_entries {
            let next = positions.last().map_or(pos, |last| last + 64);
            runs.push((positions, values));
            if runs.len() >= max_runs {
                break;
            }
            // Resume after this run; `next` is byte aligned (the run
            // started byte aligned and advanced in 8-byte steps).
            pos = next;
        } else {
            pos += 8;
        }
    }
    runs
}

/// Decode spans + view payload of a sweep-family tail.
pub(crate) struct SweepTailInfo {
    pub direction: [f64; 3],
    pub direction_spans: [Span; 3],
    pub view: SolidHistorySweepTail,
    pub option_spans: Vec<Span>,
    pub raw_spans: Vec<Span>,
    pub corner_spans: Vec<[Span; 2]>,
    pub segment_end_spans: Option<[Span; 2]>,
}

/// Decode a captured sweep/extrusion tail (ACSH_SWEEP_CLASS /
/// ACSH_EXTRUSION_CLASS). Returns `None` when the anchor layout does not
/// hold (tail shorter than a direction, or the reserved code inside the
/// head run) — the record then keeps its verbatim-only behavior.
pub(crate) fn decode_sweep_tail(bytes: &[u8], bit_len: u32) -> Option<SweepTailInfo> {
    if bit_len < 6 || bytes.len() * 8 < bit_len as usize {
        return None;
    }
    let bits = TailBits::new(bytes, bit_len);
    let mut pos = 0;
    let mut direction = [0.0; 3];
    let mut direction_spans = [Span { start: 0, len: 0 }; 3];
    for axis in 0..3 {
        // All four BD codes are legal for a direction component; the
        // reserved code decodes as 0.0 per the bitcode table.
        let entry = read_bd(&bits, pos)?;
        direction[axis] = entry.value;
        direction_spans[axis] = entry.span;
        pos += entry.span.len;
    }
    let (options, option_spans, head_end) = read_head_shorts(&bits, pos);
    if options.is_empty() {
        return None;
    }
    // Byte-aligned geometry runs bound the raw-marker scan: the sweep
    // profile corners are a run of >= 4 byte-aligned LE64 doubles, and no
    // raw BD frame entry can live inside one.
    let runs = aligned_runs(&bits, 4, 4);
    let raw_bound = runs.first().map_or(bit_len, |(positions, _)| positions[0]);
    let (raw_values, raw_spans) = scan_raws(&bits, head_end, raw_bound);
    let mut view = SolidHistorySweepTail {
        option_doubles: options,
        raw_doubles: raw_values,
        profile_corners: Vec::new(),
        segment_end: None,
    };
    let mut corner_spans = Vec::new();
    if let Some((positions, values)) = runs.first() {
        // Pair the (x, height) corner entries; a trailing unpaired entry
        // (the specimen's run ends on the block-boundary double) is left
        // out of the view but keeps its verbatim bits in the tail.
        let pairs = values.len() / 2;
        for pair in 0..pairs {
            let x = values[pair * 2];
            let height = values[pair * 2 + 1];
            view.profile_corners.push([x, height]);
            corner_spans.push([
                Span {
                    start: positions[pair * 2],
                    len: 64,
                },
                Span {
                    start: positions[pair * 2 + 1],
                    len: 64,
                },
            ]);
        }
    }
    let mut segment_end_spans = None;
    if let Some((positions, values)) = runs.last() {
        if positions.len() >= 2 && values.len() >= 2 {
            // The final raw pair must end within the last 16 bits of the
            // tail (the capture window closes on the segment end).
            let last_end = positions[positions.len() - 1] + 64;
            if last_end.saturating_add(16) >= bit_len {
                let x = values[values.len() - 2];
                let y = values[values.len() - 1];
                view.segment_end = Some([x, y]);
                segment_end_spans = Some([
                    Span {
                        start: positions[positions.len() - 2],
                        len: 64,
                    },
                    Span {
                        start: positions[positions.len() - 1],
                        len: 64,
                    },
                ]);
            }
        }
    }
    Some(SweepTailInfo {
        direction,
        direction_spans,
        view,
        option_spans,
        raw_spans,
        corner_spans,
        segment_end_spans,
    })
}

/// Decode spans + view of a loft tail.
pub(crate) struct LoftTailInfo {
    pub view: SolidHistoryLoftTail,
    pub option_spans: Vec<Span>,
    pub raw_spans: Vec<Span>,
}

pub(crate) fn decode_loft_tail(bytes: &[u8], bit_len: u32) -> Option<LoftTailInfo> {
    if bit_len < 2 || bytes.len() * 8 < bit_len as usize {
        return None;
    }
    let bits = TailBits::new(bytes, bit_len);
    let (options, option_spans, head_end) = read_head_shorts(&bits, 0);
    if options.is_empty() {
        return None;
    }
    let (raw_values, raw_spans) = scan_raws(&bits, head_end, bit_len);
    Some(LoftTailInfo {
        view: SolidHistoryLoftTail {
            option_doubles: options,
            raw_doubles: raw_values,
        },
        option_spans,
        raw_spans,
    })
}

/// Decode spans + view of a revolve tail.
pub(crate) struct RevolveTailInfo {
    pub view: SolidHistoryRevolveTail,
    pub option_spans: Vec<Span>,
    pub angle_span: Option<Span>,
    pub raw_spans: Vec<Span>,
}

pub(crate) fn decode_revolve_tail(bytes: &[u8], bit_len: u32) -> Option<RevolveTailInfo> {
    if bit_len < 2 || bytes.len() * 8 < bit_len as usize {
        return None;
    }
    let bits = TailBits::new(bytes, bit_len);
    let (options, option_spans, head_end) = read_head_shorts(&bits, 0);
    if options.is_empty() {
        return None;
    }
    let (mut raw_values, mut raw_spans) = scan_raws(&bits, head_end, bit_len);
    let revolve_angle = raw_values.first().copied();
    let angle_span = raw_spans.first().copied();
    if !raw_values.is_empty() {
        raw_values.remove(0);
        // Keep the remaining spans index-aligned with the remaining
        // values: raw_doubles[0] is the entry AFTER the angle, so its
        // span must be raw_spans[0] in the render.
        raw_spans.remove(0);
    }
    Some(RevolveTailInfo {
        view: SolidHistoryRevolveTail {
            option_doubles: options,
            revolve_angle,
            raw_doubles: raw_values,
        },
        option_spans,
        angle_span,
        raw_spans,
    })
}

/// Public per-family entry points used by the reader to populate the
/// model's tail views (spans are the writer's business, rebuilt at
/// write time from the same captured bits).
pub fn sweep_tail_view(bytes: &[u8], bit_len: u32) -> Option<SolidHistorySweepTail> {
    decode_sweep_tail(bytes, bit_len).map(|info| info.view)
}

pub fn loft_tail_view(bytes: &[u8], bit_len: u32) -> Option<SolidHistoryLoftTail> {
    decode_loft_tail(bytes, bit_len).map(|info| info.view)
}

pub fn revolve_tail_view(bytes: &[u8], bit_len: u32) -> Option<SolidHistoryRevolveTail> {
    decode_revolve_tail(bytes, bit_len).map(|info| info.view)
}

/// Same-form short-span splice: only 0.0 <-> 1.0 flips are expressible
/// in 2 bits; any other edit would need a length-shifting form change
/// (outside the Phase B write rule) and keeps the stored bits.
fn splice_short(bits: &mut TailBits, span: Span, value: f64) {
    if value == 0.0 {
        let _ = bits.set_pair(span.start, 0b10);
    } else if value == 1.0 {
        let _ = bits.set_pair(span.start, 0b01);
    }
}

/// Re-encode a sweep family tail from the model. Returns the bytes to
/// write: bit-identical to the stored tail when no decoded field was
/// programmatically modified, with only the edited raw spans changed
/// otherwise (the tail — and the record — never changes length).
pub(crate) fn render_sweep_tail(
    bytes: &[u8],
    bit_len: u32,
    direction: [f64; 3],
    view: Option<&SolidHistorySweepTail>,
) -> Option<Vec<u8>> {
    let info = decode_sweep_tail(bytes, bit_len)?;
    let mut bits = TailBits::new(bytes, bit_len);
    for (axis, component) in direction.iter().enumerate() {
        let span = info.direction_spans[axis];
        let raw = span.len == 66;
        if component != &info.direction[axis] {
            if raw {
                // A raw BD span covers the 2-bit marker plus the LE64
                // value; the payload bits start two past the marker.
                let _ = bits.set_le64(span.start + 2, *component);
            } else {
                splice_short(&mut bits, span, *component);
            }
        }
    }
    if let Some(view) = view {
        splice_short_run(&mut bits, &info.option_spans, &view.option_doubles, &info.view.option_doubles);
        splice_raw_run(&mut bits, &info.raw_spans, &view.raw_doubles, &info.view.raw_doubles);
        slice_pairs(&mut bits, &info.corner_spans, &view.profile_corners, &info.view.profile_corners);
        if let (Some(new), Some(old), Some(spans)) = (
            view.segment_end,
            info.view.segment_end,
            info.segment_end_spans,
        ) {
            if new != old {
                let _ = bits.set_le64(spans[0].start, new[0]);
                let _ = bits.set_le64(spans[1].start, new[1]);
            }
        }
    }
    Some(bits.bytes)
}

pub(crate) fn render_loft_tail(
    bytes: &[u8],
    bit_len: u32,
    view: Option<&SolidHistoryLoftTail>,
) -> Option<Vec<u8>> {
    let info = decode_loft_tail(bytes, bit_len)?;
    if view.is_none() {
        return Some(bytes.to_vec());
    }
    let view = view?;
    let mut bits = TailBits::new(bytes, bit_len);
    splice_short_run(&mut bits, &info.option_spans, &view.option_doubles, &info.view.option_doubles);
    splice_raw_run(&mut bits, &info.raw_spans, &view.raw_doubles, &info.view.raw_doubles);
    Some(bits.bytes)
}

pub(crate) fn render_revolve_tail(
    bytes: &[u8],
    bit_len: u32,
    view: Option<&SolidHistoryRevolveTail>,
) -> Option<Vec<u8>> {
    let info = decode_revolve_tail(bytes, bit_len)?;
    if view.is_none() {
        return Some(bytes.to_vec());
    }
    let view = view?;
    let mut bits = TailBits::new(bytes, bit_len);
    splice_short_run(&mut bits, &info.option_spans, &view.option_doubles, &info.view.option_doubles);
    if let (Some(new), Some(old), Some(span)) = (view.revolve_angle, info.view.revolve_angle, info.angle_span)
    {
        if new != old {
            let _ = bits.set_le64(span.start, new);
        }
    }
    splice_raw_run(&mut bits, &info.raw_spans, &view.raw_doubles, &info.view.raw_doubles);
    Some(bits.bytes)
}

fn slice_pairs(
    bits: &mut TailBits,
    spans: &[[Span; 2]],
    new: &[[f64; 2]],
    old: &[[f64; 2]],
) {
    for (index, (spans_pair, new_pair)) in spans.iter().zip(new).enumerate() {
        let old_pair = old.get(index).copied().unwrap_or([f64::NAN, f64::NAN]);
        if new_pair != &old_pair {
            let _ = bits.set_le64(spans_pair[0].start, new_pair[0]);
            let _ = bits.set_le64(spans_pair[1].start, new_pair[1]);
        }
    }
}

fn splice_short_run(
    bits: &mut TailBits,
    spans: &[Span],
    new: &[f64],
    old: &[f64],
) {
    for (index, value) in new.iter().enumerate() {
        let old_value = old.get(index);
        if Some(value) == old_value {
            continue;
        }
        if let Some(span) = spans.get(index) {
            splice_short(bits, *span, *value);
        }
    }
}

fn splice_raw_run(
    bits: &mut TailBits,
    spans: &[Span],
    new: &[f64],
    old: &[f64],
) {
    for (index, value) in new.iter().enumerate() {
        let old_value = old.get(index);
        if Some(value) == old_value {
            continue;
        }
        if let Some(span) = spans.get(index) {
            let _ = bits.set_le64(span.start, *value);
        }
    }
}

#[cfg(all(test, feature = "serde"))]
mod tests {
    use super::*;

    /// Minimal synthetic sweep tail: [3BD direction with raw z] [option
    /// shorts 1.0, 0.0] [raw BD 2.0] — enough to drive the render rules.
    fn synthetic_sweep_tail() -> (Vec<u8>, u32) {
        let mut bits: Vec<u8> = Vec::new();
        fn pair(bits: &mut Vec<u8>, code: u8) {
            bits.push(code >> 1);
            bits.push(code & 1);
        }
        pair(&mut bits, 0b10); // BD 0.0 (direction x)
        pair(&mut bits, 0b10); // BD 0.0 (direction y)
        // direction z: raw BD with LE64 2.0.
        pair(&mut bits, 0b00);
        for byte in 2.0f64.to_bits().to_le_bytes() {
            for bit in (0..8).rev() {
                bits.push((byte >> bit) & 1);
            }
        }
        pair(&mut bits, 0b01); // option 1.0 (scale)
        pair(&mut bits, 0b10); // option 0.0
        let bit_len = bits.len() as u32;
        let mut bytes = vec![0u8; (bit_len as usize + 7) / 8];
        for (index, bit) in bits.iter().enumerate() {
            if *bit == 1 {
                bytes[index / 8] |= 1 << (7 - index % 8);
            }
        }
        (bytes, bit_len)
    }

    #[test]
    fn unmodified_renders_stay_verbatim() {
        let (bytes, bit_len) = synthetic_sweep_tail();
        let info = decode_sweep_tail(&bytes, bit_len).expect("synthetic tail decodes");
        let rendered = render_sweep_tail(
            &bytes,
            bit_len,
            info.direction,
            Some(&info.view),
        )
        .expect("render works");
        assert_eq!(rendered, bytes, "an untouched model must re-emit verbatim");
    }

    #[test]
    fn direction_edits_splice_only_their_span() {
        let (bytes, bit_len) = synthetic_sweep_tail();
        let rendered = render_sweep_tail(&bytes, bit_len, [0.0, 0.0, 3.0], None)
            .expect("render works");
        // Only the direction-z raw span moved; bit length is unchanged.
        assert_eq!(rendered.len(), bytes.len());
        let differing: Vec<usize> = rendered
            .iter()
            .zip(bytes.iter())
            .enumerate()
            .filter(|(_, (a, b))| a != b)
            .map(|(index, _)| index)
            .collect();
        assert!(!differing.is_empty());
        assert!(differing.iter().all(|index| (1..10).contains(index)));
        // Re-decode: the new direction reads back through the spans.
        let info = decode_sweep_tail(&rendered, bit_len).unwrap();
        assert_eq!(info.direction, [0.0, 0.0, 3.0]);
    }

    #[test]
    fn option_short_edits_flip_only_same_form_pairs() {
        let (bytes, bit_len) = synthetic_sweep_tail();
        let info = decode_sweep_tail(&bytes, bit_len).unwrap();
        let mut view = info.view.clone();
        view.option_doubles[1] = 1.0; // 0.0 -> 1.0 stays a valid short code
        let rendered = render_sweep_tail(&bytes, bit_len, info.direction, Some(&view))
            .expect("render works");
        assert_eq!(rendered.len(), bytes.len());
        let differing: Vec<usize> = rendered
            .iter()
            .zip(bytes.iter())
            .enumerate()
            .filter(|(_, (a, b))| a != b)
            .map(|(index, _)| index)
            .collect();
        // The option pair sits at bits [72..74): byte 9 only.
        assert_eq!(differing, vec![9]);
        // A form-changing value (0.7) cannot be expressed in the short
        // span, so the render keeps the stored bits (Phase B write rule:
        // no length-shifting re-encode for short spans).
        let mut view = info.view.clone();
        view.option_doubles[1] = 0.7;
        let rendered = render_sweep_tail(&bytes, bit_len, info.direction, Some(&view))
            .expect("render works");
        assert_eq!(rendered, bytes);
        // A raw-span family member (the 2.0 direction z) takes any f64.
        let rendered = render_sweep_tail(&bytes, bit_len, [0.0, 0.0, 2.5], None).unwrap();
        let differing: Vec<usize> = rendered
            .iter()
            .zip(bytes.iter())
            .enumerate()
            .filter(|(_, (a, b))| a != b)
            .map(|(index, _)| index)
            .collect();
        assert!(!differing.is_empty());
        assert!(differing.iter().all(|index| (1..10).contains(index)));
    }

    #[test]
    fn render_without_decode_stays_verbatim() {
        // A head with a reserved pair anchors nothing: the tail keeps
        // its verbatim-only behavior (no view, no splices).
        let bytes = vec![0b1100_0000, 0, 0, 0];
        assert!(decode_sweep_tail(&bytes, 32).is_none());
    }
}
