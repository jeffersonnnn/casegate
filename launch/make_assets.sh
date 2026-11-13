#!/usr/bin/env bash
# Build the two music beds and copy the shared files into both HyperFrames projects.
# Run from anywhere: bash launch/make_assets.sh. Needs ffmpeg. Writes only inside launch/.
# Sync points (frames at 30 fps) are in launch/SPEC.md; the bed edits sit on the same times.
set -euo pipefail
L="$(cd "$(dirname "$0")" && pwd)"
SRC="$L/audio/circuit-synthwave-alt.mp3"   # CC0, 124 BPM (launch/CREDITS.md)

# bed SOURCE_OFFSET DURATION DROP_T PASSED_T OUT
# Before DROP_T: low-passed (tense). DROP_T to DROP_T + one bar: music out, the thud rings alone.
# Then low-passed again until PASSED_T. From PASSED_T: full band. Last 2 s fade out.
bed() {
  local off="$1" dur="$2" drop="$3" passed="$4" out="$5"
  local bar=1.9355 back fadest
  back=$(python3 -c "print(round($drop + $bar, 3))")
  fadest=$(python3 -c "print(round($dur - 2.0, 3))")
  local lp="if(lt(t,$drop),0.55+0.35*t/$drop,if(lt(t,$drop+0.027),0.9*($drop+0.027-t)/0.027,if(lt(t,$back),0,if(lt(t,$back+0.33),0.75*(t-$back)/0.33,if(lt(t,$passed),0.75,if(lt(t,$passed+0.037),0.75*($passed+0.037-t)/0.037,0))))))"
  local fb="if(lt(t,$passed),0,min(1,(t-$passed)/0.03))"
  ffmpeg -v error -y -i "$SRC" -filter_complex \
    "[0]atrim=start=$off:duration=$dur,asetpts=PTS-STARTPTS,aresample=48000,asplit[a][b];\
[a]lowpass=f=700,lowpass=f=700,volume='$lp':eval=frame[lp];\
[b]volume='$fb':eval=frame[fb];\
[lp][fb]amix=inputs=2:normalize=0,afade=t=out:st=$fadest:d=2,volume=-1.5dB,alimiter=limit=0.79:level=disabled:latency=1[o]" \
    -map "[o]" -ac 2 -ar 48000 -c:a pcm_s16le "$out"
}

# Film: a bar line of the track sits on the arm-drop frame 619 (20.633 s); PASSED on frame 880.
bed 0.683 45 20.633 29.333 "$L/audio/bed-film.wav"
# Cut: a bar line on the arm-drop frame 75 (2.5 s); PASSED on frame 351.
bed 36.235 20 2.5 11.7 "$L/audio/bed-cut.wav"

for p in film cut; do
  mkdir -p "$L/$p/assets/fonts" "$L/$p/assets/audio"
  cp "$L/shared/fonts/"*.woff2 "$L/$p/assets/fonts/"
  cp "$L/shared/mark3d.js" "$L/$p/assets/"
  cp "$L/audio/tick.mp3" "$L/audio/thud.mp3" "$L/audio/click.mp3" "$L/$p/assets/audio/"
done
# The beds are .wav: the repo ignores launch/**/*.wav outside launch/audio/, so each project
# gets an uncommitted copy that this script recreates.
cp "$L/audio/bed-film.wav" "$L/film/assets/audio/bed.wav"
cp "$L/audio/bed-cut.wav" "$L/cut/assets/audio/bed.wav"
echo "beds and shared assets ready"
