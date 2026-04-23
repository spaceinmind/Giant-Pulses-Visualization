# Giant Pulses Visualization

Tools for visualizing pulsar giant pulse profiles from PSRCHIVE archive files.

---

## Scripts

### `plot_joydivision_style.py` — Joy Division / Unknown Pleasures Style

Stacks normalized pulse profiles in the iconic Joy Division *Unknown Pleasures* style — white lines on a (optionally) dark background, with optional horizontal color gradients.

![Joy Division style example](docs/example_joydivision.png)

#### Usage

```bash
# Basic: plot first 50 pulses
./plot_joydivision_style.py xprof.pdmp.giants.catalog -n 50

# With SNR threshold and custom amplitude/spacing
./plot_joydivision_style.py xprof.pdmp.giants.catalog -s 15 -v 2.0 -l 0.8

# Focus on a phase window (e.g. main pulse only)
./plot_joydivision_style.py xprof.pdmp.giants.catalog -n 100 --phase-min 0.3 --phase-max 0.7

# Enable horizontal colour gradient (black → white by default)
./plot_joydivision_style.py xprof.pdmp.giants.catalog -n 100 --gradient

# Custom gradient colours
./plot_joydivision_style.py xprof.pdmp.giants.catalog -n 100 --gradient --gradient-colors purple white orange
```

#### Options

| Flag | Default | Description |
|------|---------|-------------|
| `catalog` | — | Path to catalog file (required) |
| `-o`, `--output` | `giant_pulses_joydivision.png` | Output filename |
| `-n`, `--max-pulses` | all | Maximum number of pulses to plot |
| `-dt`, `--downsample-time` | 1 | Plot every Nth pulse |
| `-dp`, `--downsample-phase` | 1 | Average every N phase bins |
| `-s`, `--snr-threshold` | None | Minimum SNR to include |
| `--width-min` | None | Minimum pulse width (ms) |
| `--width-max` | None | Maximum pulse width (ms) |
| `-v`, `--vertical-scale` | 1.0 | Amplitude scale factor |
| `-l`, `--line-spacing` | 1.0 | Vertical spacing between lines |
| `--phase-min` | 0.0 | Start of phase window |
| `--phase-max` | 1.0 | End of phase window |
| `--gradient` / `--no-gradient` | gradient on | Horizontal colour gradient |
| `--gradient-colors` | black white | Space-separated gradient colours |

---

### `plot_giant_pulses_3d.py` — 3D Waterfall Plot

Creates a 3D perspective waterfall of pulse profiles stacked in time, rendered as white polygons with black outlines.

![3D waterfall example](docs/example_3d.png)

#### Usage

```bash
# Basic usage
./plot_giant_pulses_3d.py xprof.pdmp.giants.catalog

# Limit pulses, set viewing angle
./plot_giant_pulses_3d.py xprof.pdmp.giants.catalog -n 100 --elevation 25 --azimuth -45

# With SNR filter and phase downsampling
./plot_giant_pulses_3d.py xprof.pdmp.giants.catalog -s 12 -dp 4

# Save to custom file
./plot_giant_pulses_3d.py xprof.pdmp.giants.catalog -o my_waterfall.png
```

#### Options

| Flag | Default | Description |
|------|---------|-------------|
| `catalog` | — | Path to catalog file (required) |
| `-o`, `--output` | `giant_pulses_3d.png` | Output filename |
| `-n`, `--max-pulses` | all | Maximum number of pulses to plot |
| `--no-normalize` | normalize on | Disable per-profile normalization |
| `--elevation` | 30 | 3D view elevation angle (degrees) |
| `--azimuth` | -60 | 3D view azimuth angle (degrees) |
| `-dt`, `--downsample-time` | 1 | Plot every Nth pulse |
| `-dp`, `--downsample-phase` | 1 | Average every N phase bins |
| `-s`, `--snr-threshold` | None | Minimum SNR to include |

---

## Catalog Format

Both scripts expect a whitespace-delimited catalog file with at least the following columns:

```
filename    toa_xprof    snr_xprof    width_ms    time_s
```

Lines beginning with `#` are treated as comments.

---

## Installation

```bash
pip install numpy matplotlib pandas
```

[PSRCHIVE](http://psrchive.sourceforge.net/) must be installed and its Python bindings available:

```python
import psrchive  # should work without error
```

---

## Requirements

See [`requirements.txt`](requirements.txt) for the full Python dependency list.

---

## License

MIT
