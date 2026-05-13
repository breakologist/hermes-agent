"""
Phase 5 — Full-Track Orchestration (SongBuilder)
=================================================

Each section = independent ModComposer call. Sections share no samples
(we rename per-section to avoid collision inside the single .mod).
Pattern rows capped at 64. Order list linearly chains section patterns.

CLI: python -m mod_writer.cli --song arrangement.json --output song.mod
"""

import json
import datetime
import hashlib
from typing import Dict, List, Optional, Any
from .composer import ModComposer
from .writer import ModWriter, Sample

class SongBuilder:
    def __init__(self, title: str = "Song", bpm: int = 125, just_intonation: bool = False):
        self.title   = title[:20]
        self.bpm     = bpm
        self.just_intonation = just_intonation
        self.sections: List[Dict[str, Any]] = []
        self._pattern_cache: Dict[str, "Pattern"] = {}
        self._sample_counter = 0

    def add_section(
        self,
        *,
        motif: Optional[str] = None,
        zone: Optional[int] = None,
        gate: int = 0,
        current: str = "A",
        rows: int = 16,
        triangular: bool = False,
        syzygy: bool = False,
        syzygy_channels: int = 3,
        entropy: Optional[float] = None,
        entropy_seed: Optional[int] = None,
        aq_seed: Optional[str] = None,
        title: Optional[str] = None,
    ) -> None:
        if motif is None and zone is None:
            raise ValueError("Either motif or zone must be provided")
        if not (1 <= rows <= 64):
            raise ValueError("rows must be 1-64")
        self.sections.append({
            'motif':   motif,
            'zone':    zone,
            'gate':    gate,
            'current': current,
            'rows':    rows,
            'triangular': triangular,
            'syzygy':    syzygy,
            'syzygy_channels': syzygy_channels,
            'entropy':   entropy,
            'entropy_seed': entropy_seed,
            'aq_seed':   aq_seed,
            'title':     title or f"Section {len(self.sections)+1}",
        })

    def from_dict(self, data: Dict[str, Any]) -> "SongBuilder":
        self.title = data.get('title', self.title)[:20]
        self.bpm   = data.get('bpm', self.bpm)
        for sec in data.get('sections', []):
            self.add_section(**sec)
        return self

    # Internal helpers
    def _param_hash(self, sec: Dict[str, Any]) -> str:
        sig = { k: sec[k] for k in (
            'motif','zone','gate','current','rows','triangular',
            'syzygy','syzygy_channels','entropy','entropy_seed','aq_seed'
        ) }
        return hashlib.sha256(json.dumps(sig, sort_keys=True).encode()).hexdigest()[:16]

    def _populate(self, comp: ModComposer, sec: Dict[str, Any]) -> None:
        if sec['motif']:
            meta = comp.apply_triad_motif(
                motif   = sec['motif'],
                rows    = sec['rows'],
                gate    = sec['gate'],
                current = sec['current'],
                channels = [0,1,2],
            )
        else:
            for r in range(sec['rows']):
                comp.add_note(
                    zone    = sec['zone'],
                    gate    = sec['gate'],
                    current = sec['current'],
                    row     = r,
                    channel = 0,
                )
            if sec['syzygy']:
                comp.apply_syzygy_harmony(
                    partner_channels = list(range(1, sec['syzygy_channels']+1))
                )
            if sec['entropy'] is not None:
                comp.inject_entropy(rate=sec['entropy'], rng_seed=sec['entropy_seed'])
            if sec['aq_seed']:
                comp.constrain_gates_by_aq(sec['aq_seed'])
        comp._triangular = sec['triangular']

    def _merge_samples(self, modw: ModWriter, comp: ModComposer, section_no: int) -> None:
        prefix = f"S{section_no}-"
        for old in comp.writer.samples:
            new_name = prefix + old.name.ljust(8)[:8]
            new_samp = Sample(name=new_name, data=old.data)
            # Copy optional tuning/loop metadata (respect __slots__)
            new_samp.finetune     = old.finetune
            new_samp.volume       = old.volume
            new_samp.repeat_offset = old.repeat_offset
            new_samp.repeat_length = old.repeat_length
            modw.add_sample(new_samp)


    def build(self, verbose: bool = False) -> ModWriter:
        modw = ModWriter(title=f"{self.title} [BPM={self.bpm}]")
        for i, sec in enumerate(self.sections, 1):
            uniq_title = f"{self.title}-S{i}"
            param_key = self._param_hash(sec)
            if param_key in self._pattern_cache:
                pat = self._pattern_cache[param_key].clone()
                if verbose:
                    print(f"  Section {i} (cache): {param_key[:8]}")
            else:
                comp = ModComposer(title=uniq_title, just_intonation=self.just_intonation)
                self._populate(comp, sec)
                comp._ensure_samples()  # Critical: build sample instruments before pattern & merge
                pat  = comp.build_patterns_from_grid(length=sec['rows'], triangular=sec['triangular'])
                self._pattern_cache[param_key] = pat.clone()
                if verbose:
                    print(f"  Section {i} (generated): {param_key[:8]}")
                self._merge_samples(modw, comp, section_no=i)
            pat_idx = modw.add_pattern(pat)
            modw.orders.append(pat_idx)
        if len(modw.samples) > 31:
            raise ValueError(f"Sample limit exceeded: {len(modw.samples)} > 31 (Protracker max)")
        return modw

    def write(self, path: str, verbose: bool = False) -> str:
        modw = self.build(verbose=verbose)
        modw.write(path)
        if verbose:
            print(f"✔ Song: {path}  sections={len(self.sections)} patterns={len(modw.patterns)} samples={len(modw.samples)}")
        return path

    def write_manifest(self, base_path: str, stem: Optional[str] = None) -> str:
        manifest = {
            'title': self.title,
            'bpm': self.bpm,
            'total_sections': len(self.sections),
            'total_patterns': len(self.sections),
            'created': datetime.datetime.utcnow().isoformat() + "Z",
            'sections': [
                { 'no': i+1, 'title': s['title'], 'motif': s['motif'],
                  'zone': s['zone'], 'rows': s['rows'],
                  'gate': s['gate'], 'current': s['current'] }
                for i,s in enumerate(self.sections)
            ],
        }
        mf_path = (stem or base_path).removesuffix('.mod') + '.manifest.json'
        with open(mf_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        return mf_path


# Functional convenience wrapper
def build_song(
    title: str,
    sections: List[Dict[str, Any]],
    bpm: int = 125,
    output: str = "song.mod",
    verbose: bool = False,
) -> str:
    builder = SongBuilder(title=title, bpm=bpm)
    for sec in sections:
        builder.add_section(**sec)
    return builder.write(output, verbose=verbose)
