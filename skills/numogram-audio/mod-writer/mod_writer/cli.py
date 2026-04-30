"""CLI for mod writer — full Phase 2 integration.

Generates .mod files with:
- Zone → pentatonic note mapping
- Gate → Protracker effect encoding
- Current → instrument selection
- Metadata embedded in sample names and title (within 20/22-char limits)
"""

import sys
import os
import argparse
import json
import datetime

DIR = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(DIR)
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)

from mod_writer.writer import ModWriter, Pattern, Sample, period_for_note, NOTE_OFFSET, PERIOD_TABLE
from mod_writer.song import SongBuilder, build_song
from mod_writer.utils import generate_square_wave, generate_triangle_wave, generate_noise
from mod_writer.mapping import (
    note_and_octave_from_zone,
    mod_effect_from_gate,
    CURRENT_TO_INSTRUMENT,
    ZONE_TO_NOTE,
)
# Import triad‑motif policy to expose available motif names as cli choices
from mod_writer.composer import TRIAD_MOTIF_POLICY, ModComposer

# MIR audio profiling (Phase 6 — optional, graceful degradation)
try:
    from mod_writer.mir_profiler import MIRFeatureExtractor
    _MIR_AVAILABLE = True
except ImportError as e:
    _MIR_AVAILABLE = False
    _MIR_IMPORT_ERROR = str(e)

# Audio rendering & analysis (Phase 4)
AUDIO_RENDERER_DIR = os.path.normpath(os.path.join(DIR, '..', '..', 'audio-renderer'))
if AUDIO_RENDERER_DIR not in sys.path:
    sys.path.insert(0, AUDIO_RENDERER_DIR)
try:
    from renderer import render_mod_to_wav, generate_spectrogram, analyze_wav, play_audio, describe_audio
    _AUDIO_AVAILABLE = True
except ImportError as e:
    # audio-renderer skill not present or broken
    _AUDIO_AVAILABLE = False
    _IMPORT_ERROR = str(e)


def _sample_name(base_wave: str, zone: int, gate: int, current: str) -> str:
    """Build an informative 22-char sample name: WAVE-Zz-Ggg-Cc."""
    # Abbreviate: SQ/TRI/NO
    abbr = {'square': 'SQ', 'triangle': 'TR', 'noise': 'NO'}.get(base_wave, base_wave[:2].upper())
    name = f"{abbr}-Z{zone}-G{gate}-{current}"
    # Pad/truncate to 22
    if len(name) < 22:
        name = name.ljust(22)
    return name[:22]


def _run_phase4(mod_path: str, args) -> None:
    """Handle --render / --spectrogram / --play / --analyze / --manifest pipeline."""
    if not _AUDIO_AVAILABLE:
        print(f"⚠ Audio renderer unavailable: {_IMPORT_ERROR}")
        print("  Ensure ~/.hermes/skills/numogram-audio/audio-renderer/ is intact.")
        return

    # Step 1: render .mod → WAV
    wav_path = None
    if args.render or args.spectrogram or args.play or args.analyze:
        print(f"🎧 Rendering {mod_path} → WAV …")
        wav_path = render_mod_to_wav(mod_path)
        print(f"  WAV: {wav_path} ({os.path.getsize(wav_path)} bytes)")

    # Step 2: spectrogram
    if args.spectrogram:
        if wav_path is None:
            print("⚠ --spectrogram requires --render or a prior WAV file")
        else:
            print(f"🎨 Generating spectrogram ({args.colormap}, {args.spec_size})…")
            spec = generate_spectrogram(wav_path, colormap=args.colormap, size=args.spec_size)
            print(f"  Spec: {spec} ({os.path.getsize(spec)} bytes)")

    # Step 3: playback
    if args.play:
        if wav_path is None:
            print("⚠ --play requires --render")
        else:
            print(f"▶ Playing via {args.player} …")
            try:
                play_audio(wav_path, player=args.player)
            except Exception as e:
                print(f"✗ Playback failed: {e}")

    # Step 4: unified analysis (driven by --analyze / --describe / --verify)
    analysis = None
    need_analysis = any([args.analyze, args.describe, args.verify])
    if need_analysis:
        if wav_path is None:
            print("⚠ analysis/describe/verify requires --render")
        else:
            print("🔬 Analyzing audio features …")
            analysis = analyze_wav(wav_path)
            if args.analyze:
                analysis_json = wav_path.replace('.wav', '_analysis.json')
                with open(analysis_json, 'w') as f:
                    json.dump(analysis, f, indent=2)
                print(f"  Analysis: {analysis_json}")
            if args.describe:
                portrait = describe_audio(analysis, args.zone, f"{args.gate}", args.current)
                print("🎙", portrait)
            if args.verify:
                q = analysis.get("quality", "pass")
                if q != "pass":
                    print(f"❌ Quality check failed: {q.upper()}")
                    sys.exit(2)
                else:
                    print("✅ Quality check passed")

    # Step 5: manifest JSON (track meta + analysis link)
    if args.manifest:
        manifest = {
            'title': args.title,
            'zone': args.zone,
            'gate': args.gate,
            'current': args.current,
            'rows': args.rows,
            'syzygy': args.syzygy,
            'entropy': args.entropy,
            'triangular': args.triangular,
            'aq_seed': args.aq_seed,
            'mod_file': os.path.abspath(mod_path),
            'wav_file': os.path.abspath(wav_path) if wav_path else None,
            'spectrogram': wav_path.replace('.wav', '_spec.png') if wav_path else None,
            'analysis': analysis,
            'generated_at': datetime.datetime.now().isoformat(),
        }
        manifest_path = mod_path.replace('.mod', '_manifest.json')
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        print(f"📄 Manifest: {manifest_path}")

    # Step 6: compact JSON for TD/automation
    if args.json:
        status = {
            'zone': args.zone,
            'gate': args.gate,
            'current': args.current,
            'title': args.title,
            'wav': os.path.abspath(wav_path) if wav_path else None,
            'spectrogram': spec if args.spectrogram else None,
            'palette': args.colormap if args.spectrogram else None,
            'timestamp': datetime.datetime.now().isoformat(),
        }
        # Merge analysis if available
        if need_analysis and analysis:
            status['analysis'] = analysis
        json_path = mod_path.replace('.mod', '.json')
        with open(json_path, 'w') as f:
            json.dump(status, f, indent=2)
        print(f"🖥  TD status: {json_path}")



def main():
    import json  # ensure local binding despite later conditional import
    p = argparse.ArgumentParser(description="Generate .mod modules with numogram mapping.")
    p.add_argument('--title', default='HermesTracker', help='Song title (max 20 chars)')
    p.add_argument('--zone', type=int, default=1, help='Zone (1-9)')
    p.add_argument('--gate', type=int, default=0, help='Gate (0-36)')
    p.add_argument('--current', choices=['A', 'B', 'C'], default='A', help='Current A/B/C')
    p.add_argument('--syzygy', action='store_true', help='Add syzygy harmony on channels 1-3')
    p.add_argument('--syzygy-channels', type=int, default=3, help='Number of harmony channels (default 3)')
    p.add_argument('--entropy', type=float, help='Entropy injection rate 0-1')
    p.add_argument('--entropy-seed', type=int, help='Entropy RNG seed')
    p.add_argument('--triangular', action='store_true', help='Pattern length = triangular number of zone')
    p.add_argument('--aq-seed', help='AQ seed string to constrain gate progression')
    p.add_argument('--triad-motif', choices=sorted(TRIAD_MOTIF_POLICY.keys()),
                 help='Generate triad texture aligned to motif (overrides --zone/--gate/--current). '
                      'Numogram currents: Sink/Warp/Hold/Rise/Void; Quadrivium systems: '
                      'Monochord/Pythagorean/Ptolemaic/Harmonic.')
    p.add_argument('--validate-motif', choices=sorted(TRIAD_MOTIF_POLICY.keys()),
                  help='Dry-run: validate triad-motif zone mapping and print JSON report (no .mod written).')
    p.add_argument('--validate-all', action='store_true',
                  help='Dry-run: validate all 24 canonical triads (12 roots × 2 qualities)')
    p.add_argument('--inspect-motif', choices=sorted(TRIAD_MOTIF_POLICY.keys()),
                  help='Dry-run: inspect full grid for a triad motif (table/JSON/CSV); no .mod written.')
    p.add_argument('--inspect-format', choices=['table','json','csv'], default='table',
                  help='Output format for --inspect-motif (default: table)')
    p.add_argument('--rows', type=int, default=16, help='Base pattern row count (default 16)')
    p.add_argument('--output', default='output.mod', help='Output .mod filename')

    # Phase 4 — rendering & perception
    p.add_argument('--render', action='store_true', help='Render .mod → WAV via audio-renderer (implies --output must be set)')
    p.add_argument('--spectrogram', action='store_true', help='Generate spectrogram PNG from rendered WAV')
    p.add_argument('--colormap', default='viridis',
                   choices=['viridis', 'magma', 'plasma', 'cool', 'inferno'],
                   help='Spectrogram colormap (ffmpeg: viridis, magma, plasma, cool; inferno may unavailable)')
    p.add_argument('--spec-size', default='800x400', help='Spectrogram image size WxH (default 800x400)')
    p.add_argument('--play', action='store_true', help='Play rendered WAV via system audio (requires --render)')
    p.add_argument('--player', default='ffplay', choices=['ffplay', 'aplay', 'pw-play', 'mpg123'], help='Audio player backend')
    p.add_argument('--analyze', action='store_true', help='Extract audio features to JSON (requires --render)')
    p.add_argument('--manifest', action='store_true', help='Write a JSON manifest with track + analysis metadata')
    p.add_argument('--json', action='store_true', help='Emit compact JSON status file for TD/automation')
    # Phase 4.5 — auditory verification & description
    p.add_argument('--verify', action='store_true', help='Run quality checks; exit non-zero on clipping/DC offset')
    p.add_argument('--describe', action='store_true', help='Print a textual portrait of the rendered sound')
    # Phase 6 — MIR audio profiling (optional, see mod-writer-mir-profile.md)
    p.add_argument('--profile-audio', metavar='AUDIO_FILE',
                   help='Extract full MIR feature profile from an audio file (requires optional MIR deps). Prints JSON to stdout.')
    p.add_argument('--mir-seed', metavar='AUDIO_FILE',
                   help='Derive an AQ seed from audio fingerprint, then generate a module (implies --aq-seed). '
                        'Uses the same feature profile as --profile-audio.')
    # Phase 3.4 — AQ classifier (real-audio validation → CLI)
    p.add_argument('--classify', metavar='AUDIO_FILE',
                   help='Run AQ classifier on a single audio file.')
    p.add_argument('--classify-dir', metavar='DIRECTORY',
                   help='Batch-classify all audio files in a directory (max --classify-limit).')
    p.add_argument('--classify-limit', type=int, default=100,
                   help='Maximum files to classify in --classify-dir mode (default 100)')
    p.add_argument('--classify-format', choices=['table','json','csv'], default='table',
                   help='Output format: table (default), json, or csv')
    p.add_argument('--from-audio', metavar='AUDIO_FILE',
                   help='[Prototype] Transcribe audio directly into a tracker pattern (Phase 7a). '
                        'Captures onset peaks and spectral allocation as notes.')
    p.add_argument('--accompaniment', metavar='AUDIO_FILE',
                   help='[Prototype] Generate a complementary module that fills frequency gaps around the given audio (Phase 7b).')

    p.add_argument('--song', metavar='ARRANGEMENT.json',
                  help='Load multi-section arrangement from JSON file')
    p.add_argument('--bpm', type=int, default=125,
                  help='Global tempo for the song (stored in title/metadata)')
    p.add_argument('--warn-clamp', action='store_true', help='Warn if any notes exceed period table range and get clamped to period 0')
    p.add_argument('--just-intonation', action='store_true', help='Use just intonation ratios (5/4 or 6/5 for third, 3/2 for fifth) in triad motifs')
    p.add_argument('--song-manifest', action='store_true', help='Write JSON manifest for song mode alongside .mod')


    args = p.parse_args()

    # ── Phase 2c: standalone triad-motif inspection (dry-run) ─────────────────────
    if args.inspect_motif:
        comp = ModComposer(title=args.title, just_intonation=args.just_intonation)
        result = comp.inspect_motif(
            motif=args.inspect_motif,
            rows=args.rows,
            gate=args.gate,
            current=args.current,
            channels=[0, 1, 2],
        )
        if args.inspect_format == 'table':
            meta = result['meta']
            print(f"Motif: {meta['motif']}  Root: {meta['root']} ({meta['quality']}) octave={meta['octave']}")
            print(f"Zones: {meta['zones']}  Channels: {meta['channels']}  Rows: {meta['rows']}")
            print(f"Zone distribution: {result['zone_distribution']}")
            print()
            print("Row  Ch0           Ch1           Ch2")
            print("-----------------------------------------------")
            for row_entry in result['grid']:
                row = row_entry['row']
                ch0 = row_entry['channels'].get(0)
                ch1 = row_entry['channels'].get(1)
                ch2 = row_entry['channels'].get(2)
                def fmt(ch):
                    if ch is None:
                        return "---"
                    return f"{ch['note']}{ch['octave']} (z{ch['zone']}, p{ch['period']})"
                print(f"{row:3d}  {fmt(ch0):20s} {fmt(ch1):20s} {fmt(ch2):20s}")
        elif args.inspect_format == 'json':
            print(json.dumps(result, indent=2))
        elif args.inspect_format == 'csv':
            print("row,channel,note,octave,zone,gate,current,period")
            for row_entry in result['grid']:
                row = row_entry['row']
                for ch_idx, ch_data in row_entry['channels'].items():
                    if ch_data is None:
                        print(f"{row},{ch_idx},,,,,,")
                    else:
                        print(f"{row},{ch_idx},{ch_data['note']},{ch_data['octave']},{ch_data['zone']},{ch_data['gate']},{ch_data['current']},{ch_data['period']}")
        sys.exit(0)

    # ── Phase 2c: exhaustive triad validation (dry-run) ─────────────────────────
    if args.validate_all:
        # Load canonical vectors
        import json
        vectors_path = os.path.join(DIR, 'canonical_vectors.json')
        with open(vectors_path) as f:
            vectors = json.load(f)

        # Rebuild period reverse mapping (same as validate-motif)
        PERIOD_TO_NOTE = {}
        for octv in range(0, 9):
            for note in NOTE_OFFSET:
                p = period_for_note(note, octv)
                if p not in PERIOD_TO_NOTE:
                    PERIOD_TO_NOTE[p] = (note, octv)

        def digital_root(n: int) -> int:
            while n > 9:
                n = sum(int(d) for d in str(n))
            return n

        all_passed = True
        results = []
        for vec in vectors:
            root = vec['root']
            quality = vec['quality']
            octave = vec['octave']
            expected_zones = sorted(set(vec['zones']))

            # Build a temporary composer with this triad
            comp = ModComposer(title=f"val-{root}-{quality}")
            third_int = 3 if quality == 'minor' else 4
            fifth_int = 7
            root_offset = NOTE_OFFSET[root]
            root_semi = octave * 12 + root_offset
            third_semi = root_semi + third_int
            fifth_semi = root_semi + fifth_int
            zones_calc = [
                digital_root(root_semi + 1),
                digital_root(third_semi + 1),
                digital_root(fifth_semi + 1),
            ]
            chromatic = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
            def note_name(offset): return chromatic[offset % 12]
            root_note = note_name(root_offset)
            third_note = note_name((root_offset + third_int) % 12)
            fifth_note = note_name((root_offset + fifth_int) % 12)
            octave_root = root_semi // 12
            octave_third = third_semi // 12
            octave_fifth = fifth_semi // 12

            for r in range(args.rows):
                comp.add_note(zone=zones_calc[0], gate=args.gate, current=args.current, row=r, channel=0,
                              note=root_note, octave=octave_root)
                comp.add_note(zone=zones_calc[1], gate=args.gate, current=args.current, row=r, channel=1,
                              note=third_note, octave=octave_third)
                comp.add_note(zone=zones_calc[2], gate=args.gate, current=args.current, row=r, channel=2,
                              note=fifth_note, octave=octave_fifth)

            pat = comp.build_patterns_from_grid(length=args.rows, triangular=args.triangular)
            zones_observed = set()
            for row in range(args.rows):
                for ch in range(3):
                    period = pat.rows[row][ch][0]
                    if period == 0:
                        continue
                    note_oct = PERIOD_TO_NOTE.get(period)
                    if note_oct is None:
                        zones_observed.add('UNKNOWN')
                    else:
                        note, octv = note_oct
                        semi = octv * 12 + NOTE_OFFSET[note]
                        zones_observed.add(digital_root(semi + 1))
            match = sorted(zones_observed) == expected_zones
            if not match:
                all_passed = False
            results.append({
                'root': root,
                'quality': quality,
                'octave': octave,
                'expected_zones': expected_zones,
                'observed_zones': sorted(zones_observed),
                'match': match,
            })

        report = {
            'mode': 'validate-all',
            'total': len(vectors),
            'passed': sum(1 for r in results if r['match']),
            'failed': sum(1 for r in results if not r['match']),
            'all_passed': all_passed,
            'details': results,
        }
        print(json.dumps(report, indent=2))
        sys.exit(0 if all_passed else 1)

    # ── Phase 2c: standalone triad-motif validation (dry-run) ────────────────────
    if args.validate_motif:

        def digital_root(n):
            while n > 9:
                n = sum(int(d) for d in str(n))
            return n
        # Build period reverse mapping
        PERIOD_TO_NOTE = {}
        for octv in range(0, 9):
            for note in NOTE_OFFSET:
                p = period_for_note(note, octv)
                if p not in PERIOD_TO_NOTE:
                    PERIOD_TO_NOTE[p] = (note, octv)
        comp = ModComposer()
        ret = comp.apply_triad_motif(args.validate_motif, rows=args.rows, gate=args.gate, current=args.current)
        pat = comp.build_patterns_from_grid(length=args.rows, triangular=args.triangular)
        zones_observed = set()
        for row in range(args.rows):
            for ch in range(3):
                period = pat.rows[row][ch][0]
                if period == 0:
                    continue
                note_oct = PERIOD_TO_NOTE.get(period)
                if note_oct is None:
                    zones_observed.add('UNKNOWN')
                else:
                    note, octv = note_oct
                    semi = octv * 12 + NOTE_OFFSET[note]
                    zones_observed.add(digital_root(semi + 1))
        report = {
            'mode':            'validate-motif',
            'motif':           args.validate_motif,
            'rows':            args.rows,
            'gate':            args.gate,
            'current':         args.current,
            'triangular':      args.triangular,
            'expected_zones':  sorted(set(ret['zones'])),
            'observed_zones':  sorted(zones_observed),
            'match':           sorted(zones_observed) == sorted(set(ret['zones'])),
            'detail':          ret,
        }
        print(json.dumps(report, indent=2))
        sys.exit(0 if report['match'] else 1)

    # ── Phase 6: MIR audio profiling ——————————————————————————————————————————
    if getattr(args, 'profile_audio', None):
        if not _MIR_AVAILABLE:
            print("❌ MIR profiling requires optional extras: pip install mod-writer[mir]")
            print(f"   Import error: {_MIR_IMPORT_ERROR}")
            sys.exit(1)
        profile = MIRFeatureExtractor.extract(args.profile_audio)
        print(json.dumps(profile, indent=2))
        sys.exit(0)

    if getattr(args, 'mir_seed', None):
        if not _MIR_AVAILABLE:
            print("❌ MIR profiling requires optional extras: pip install mod-writer[mir]")
            sys.exit(1)
        profile = MIRFeatureExtractor.extract(args.mir_seed)
        derived_seed = MIRFeatureExtractor.profile_to_seed(profile)
        args.aq_seed = derived_seed
        print(f"🔮 Derived AQ seed from audio fingerprint: {args.aq_seed}")

    # ── Phase 3.4: AQ classifier ————————————————————————————————————————————————
    if getattr(args, 'classify', None):
        if not _MIR_AVAILABLE:
            print("❌ Classification requires MIR extras: pip install mod-writer[mir]")
            print(f"   Import error: {_MIR_IMPORT_ERROR}")
            sys.exit(1)
        from mod_writer.classifier import predict_audio
        try:
            result = predict_audio(args.classify)
        except Exception as e:
            print(f"❌ Classification failed: {e}")
            sys.exit(1)
        if args.classify_format == 'json':
            print(json.dumps(result, indent=2))
        elif args.classify_format == 'csv':
            print("file,predicted_aq,zone,duration_s,bpm,key,scale")
            print(f"{result['file']},{result['predicted_aq']},{result['zone']},"
                  f"{result['duration_s']},{result['bpm'] or ''},{result['key'] or ''},{result['scale'] or ''}")
        else:
            print(f" file:               {result['file']}")
            print(f" predicted AQ:       {result['predicted_aq']}")
            print(f" zone:               {result['zone']}")
            print(f" duration:           {result['duration_s']:.1f}s")
            print(f" bpm:                {result['bpm'] if result['bpm'] else 'unknown'}")
            print(f" key:                {result['key'] or 'unknown'} {result['scale'] or ''}")
        sys.exit(0)

    if getattr(args, 'classify_dir', None):
        if not _MIR_AVAILABLE:
            print("❌ Classification requires MIR extras: pip install mod-writer[mir]")
            sys.exit(1)
        from mod_writer.classifier import batch_predict
        try:
            results = batch_predict(args.classify_dir, limit=args.classify_limit)
        except Exception as e:
            print(f"❌ Batch classification failed: {e}")
            sys.exit(1)
        if args.classify_format == 'json':
            print(json.dumps(results, indent=2))
        elif args.classify_format == 'csv':
            print("file,predicted_aq,zone,duration_s,bpm,key,scale")
            for r in results:
                print(f"{r['file']},{r['predicted_aq']},{r['zone']},"
                      f"{r['duration_s']},{r['bpm'] or ''},{r['key'] or ''},{r['scale'] or ''}")
        else:
            print(f"{'FILE':<50} {'AQ':>7} {'Z':>3} {'DUR':>6} {'BPM':>5} {'KEY':>6}")
            print("-" * 80)
            for r in results:
                bpm_str = f"{r['bpm']:.1f}" if r['bpm'] else "?"
                key_str = (r['key'] or '?') + (' ' + r['scale'][:3] if r['scale'] else '')
                print(f"{r['file'][:50]:<50} {r['predicted_aq']:>7.1f} {r['zone']:>3} "
                      f"{r['duration_s']:>6.1f} {bpm_str:>5} {key_str:>6}")
        sys.exit(0)

    # ── Phase 7: Audio transcription (prototype stubs) ————————————————————————
    if getattr(args, 'from_audio', None):
        print("⚠ --from-audio not yet implemented (Phase 7a, planned)")
        sys.exit(1)

    if getattr(args, 'accompaniment', None):
        print("⚠ --accompaniment not yet implemented (Phase 7b, planned)")
        sys.exit(1)

        # Phase 2b/3: if any advanced flag present, use ModComposer
    advanced = any([
        args.syzygy,
        args.entropy is not None,
        args.triangular,
        args.aq_seed is not None,
        args.triad_motif is not None,
    ])
    if args.song:
        # ——— Phase 5 — Song orchestration ———————————————————————————————————
        with open(args.song) as f:
            arrangement = json.load(f)

        builder = SongBuilder(
            title = arrangement.get('title', 'Song'),
            bpm   = arrangement.get('bpm', args.bpm),
            just_intonation = args.just_intonation,
        )
        builder.from_dict(arrangement)
        builder.write(args.output, verbose=True)

        if args.warn_clamp:
            print("⚠ --warn-clamp not yet implemented in song mode (section-level TBD)")

        # Phase 4 pipeline (render/spectrogram/play/analyze)
        _run_phase4(args.output, args)

        if args.song_manifest:
            manifest_path = args.output.replace('.mod', '.json')
            builder.write_manifest(manifest_path)
            print(f"✔ Wrote song manifest: {manifest_path}")

        sys.exit(0)

    if advanced:
        comp = ModComposer(title=args.title, just_intonation=args.just_intonation)
        if args.triad_motif:
            # Triad‑motif generates its own note texture; ignore --zone/--gate/--current for channel 0
            meta = comp.apply_triad_motif(
                motif=args.triad_motif,
                rows=args.rows,
                gate=args.gate,
                current=args.current,
                channels=[0, 1, 2]  # three‑voice triad texture
            )
        if args.warn_clamp:
            clamped_info = meta.get('clamped', {})
            if any([clamped_info.get('root'), clamped_info.get('third'), clamped_info.get('fifth')]):
                print("⚠ Clamping warnings (notes exceeded period table range):")
                for tone in meta.get('tone_data', []):
                    if tone.get('clamped'):
                        print(f"  • {tone['name']} (octave {tone['octave']}, index {tone['semitone_index']}) -> period 0 (clamped)")
                print(f"  Valid semitone indices: 0–{clamped_info.get('max_valid_index', '?')} (period table size {len(PERIOD_TABLE)})")


        else:
            comp.apply_seed_pattern(
                zone=args.zone,
                gate=args.gate,
                current=args.current,
                rows=args.rows,
                triangular=args.triangular,
                syzygy=args.syzygy,
                syzygy_channels=args.syzygy_channels,
                entropy=args.entropy,
                entropy_seed=args.entropy_seed,
                aq_seed=args.aq_seed,
            )
        # Common flags
        comp._triangular = args.triangular
        comp.write_mod(args.output)
        print(f"✔ Composed {args.output}")
        if args.triad_motif:
            print(f"  Triad motif={args.triad_motif} rows={args.rows} gate={args.gate} current={args.current}")
        else:
            print(f"  Zone={args.zone} Gate={args.gate} Current={args.current} Rows={args.rows}")
            if args.syzygy:
                print(f"  Syzygy harmony on ch1-{args.syzygy_channels}")
            if args.entropy is not None:
                print(f"  Entropy rate={args.entropy} seed={args.entropy_seed}")
            if args.triangular:
                print(f"  Triangular pattern length (T({args.zone})={args.zone*(args.zone+1)//2})")
            if args.aq_seed:
                print(f"  AQ‑seeded gate progression: {args.aq_seed}")

        # Phase 4 post‑render pipeline
        _run_phase4(args.output, args)
        sys.exit(0)


    zone = args.zone
    gate = args.gate
    current = args.current

    # Title encoding: prefix small meta tag to keep within 20 chars
    title_prefix = f"Z{zone}G{gate}{current}"
    raw_title = args.title[: (20 - len(title_prefix) - 1)]  # space for hyphen
    title_str = f"{title_prefix}-{raw_title}" if raw_title else title_prefix[:20]
    title_str = title_str[:20]

    writer = ModWriter(title=title_str)

    # Generate all three base samples, but label them with current context
    samples_cfg = [
        ('square', generate_square_wave(0.15, 440, 8363, 0.7)),
        ('triangle', generate_triangle_wave(0.15, 440, 8363, 0.7)),
        ('noise', generate_noise(0.15, 8363, 0.5)),
    ]
    for wave_name, data in samples_cfg:
        samp_name = _sample_name(wave_name, zone, gate, current)
        writer.add_sample(Sample(name=samp_name, data=data))

    # Build a single pattern row encoding the note + gate effect
    pat = Pattern()
    note, octave = note_and_octave_from_zone(zone)
    sample_idx = CURRENT_TO_INSTRUMENT[current]  # 1,2,3 respectively

    if note != 'REST':
        period = period_for_note(note, octave)
    else:
        period = 0  # rest

    eff_cmd, eff_param = mod_effect_from_gate(gate)

    pat.set_cell(row=0, channel=0, period=period, sample=sample_idx,
                 effect=eff_cmd, param=eff_param)

    writer.add_pattern(pat)
    writer.write(args.output)
    print(f"✓ Written {args.output}")
    print(f"  Title: {title_str}")
    print(f"  Zone={zone} Note={note} Oct={octave} Period={period}")
    print(f"  Current={current} → sample #{sample_idx}")
    print(f"  Gate={gate} → effect 0x{eff_cmd:X} param 0x{eff_param:X}")

    # Phase 4 post‑render pipeline
    _run_phase4(args.output, args)


if __name__ == '__main__':
    main()
