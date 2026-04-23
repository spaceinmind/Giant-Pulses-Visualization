#!/usr/bin/env python3
"""
Plot 3D waterfall visualization of giant pulses from a catalog.
Creates a plot similar to the reference image with pulse profiles stacked in time.
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import pandas as pd
import os
from psrchive import Archive
import argparse
import matplotlib
matplotlib.use('TkAgg') 

plt.rcParams['font.family'] = 'serif'


def load_pulse_profile(filepath, downsample_phase=1):
    """
    Load a pulse profile from a .zapp file using psrchive.
    
    Parameters:
    -----------
    filepath : str
        Path to the .zapp archive file
    downsample_phase : int
        Downsampling factor for phase bins (average every N bins)
        
    Returns:
    --------
    profile : np.array
        1D array of pulse profile intensities
    """
    try:
        ar = Archive.load(filepath)
        ar.remove_baseline()  # Don't remove baseline
        ar.dedisperse()
        ar.fscrunch()
        ar.tscrunch()
        ar.pscrunch()
        
        data = ar.get_data()
        profile = data.squeeze()
        
        # Downsample the profile if requested
        if downsample_phase > 1:
            n_bins = len(profile)
            n_new_bins = n_bins // downsample_phase
            # Reshape and average
            profile = profile[:n_new_bins * downsample_phase].reshape(n_new_bins, downsample_phase).mean(axis=1)
        
        return profile
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None


def plot_3d_waterfall(catalog_file, output_file='giant_pulses_3d.png', 
                      max_pulses=None, normalize=True, elevation=30, azimuth=-60,
                      downsample_time=1, downsample_phase=1, snr_threshold=None):
    """
    Create a 3D waterfall plot of giant pulses.
    
    Parameters:
    -----------
    catalog_file : str
        Path to the TSV catalog file
    output_file : str
        Output filename for the plot
    max_pulses : int or None
        Maximum number of pulses to plot (None = all)
    normalize : bool
        Whether to normalize each profile
    elevation : float
        Elevation angle for 3D view
    azimuth : float
        Azimuth angle for 3D view
    downsample_time : int
        Downsample factor in time (plot every Nth pulse, default: 1)
    downsample_phase : int
        Downsample factor for phase bins (average every N bins, default: 1)
    snr_threshold : float or None
        Minimum SNR threshold - only plot pulses with SNR >= threshold (default: None)
    """
    
    # Read the catalog
    print(f"Reading catalog: {catalog_file}")
    df = pd.read_csv(catalog_file, sep='\s+', comment='#')
    
    # Filter by SNR threshold if specified
    if snr_threshold is not None:
        initial_count = len(df)
        df = df[df['snr_xprof'] >= snr_threshold].reset_index(drop=True)
        print(f"Filtered by SNR >= {snr_threshold}: {len(df)}/{initial_count} pulses")
    
    # Limit number of pulses if specified
    if max_pulses is not None:
        df = df.head(max_pulses)
    
    # Downsample in time if requested
    if downsample_time > 1:
        df = df.iloc[::downsample_time].reset_index(drop=True)
        print(f"Downsampling in time by factor {downsample_time}")
    
    if downsample_phase > 1:
        print(f"Downsampling phase bins by factor {downsample_phase}")
    
    print(f"Loading {len(df)} pulse profiles...")
    
    # Load all profiles
    profiles = []
    times = []
    snrs = []
    
    for idx, row in df.iterrows():
        filepath = row['filename']
        
        # Check if file exists
        if not os.path.exists(filepath):
            print(f"Warning: File not found: {filepath}")
            continue
            
        profile = load_pulse_profile(filepath, downsample_phase=downsample_phase)
        
        if profile is not None:
            if normalize:
                # Normalize to [0, 1]
                profile = profile - np.min(profile)
                if np.max(profile) > 0:
                    profile = profile / np.max(profile)
            
            profiles.append(profile)
            times.append(row['time_s'])
            snrs.append(row['snr_xprof'])
    
    if len(profiles) == 0:
        print("Error: No profiles could be loaded!")
        return
    
    print(f"Successfully loaded {len(profiles)} profiles")
    
    # Create the 3D plot
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Get the number of phase bins
    n_bins = len(profiles[0])
    phase = np.linspace(0, 1, n_bins)
    
    # Create polygon vertices for each profile
    verts = []
    for i, (profile, time, snr) in enumerate(zip(profiles, times, snrs)):
        # Create vertices as (x, z) pairs for this profile
        # Start at baseline (z=0), trace the profile, return to baseline
        v = [(phase[0], 0)]  # Start at baseline
        for j in range(len(phase)):
            v.append((phase[j], profile[j]))
        v.append((phase[-1], 0))  # End at baseline
        verts.append(v)
    
    # Create PolyCollection with white faces and black edges
    from matplotlib.collections import PolyCollection
    poly = PolyCollection(verts, facecolors=(1, 1, 1, 0.9), edgecolors='black', linewidths=0.5)
    
    # Add the collection to the 3D plot at the corresponding time positions
    ax.add_collection3d(poly, zs=times, zdir='y')
    
    # Set axis limits
    ax.set_xlim3d(0, 1)
    ax.set_ylim3d(min(times), max(times))
    
    # Find global min/max intensity for z-axis
    zmin = min([min(p) for p in profiles])
    zmax = max([max(p) for p in profiles])
    ax.set_zlim3d(zmin, zmax)
    
    # Labels and title
    ax.set_xlabel('Phase', fontsize=16, labelpad=10)
    ax.set_ylabel('Time (s)', fontsize=16, labelpad=10)
    ax.set_zlabel('Intensity', fontsize=16, labelpad=10)
    ax.tick_params(axis='both', which='major', labelsize=16)

    # Set viewing angle
    ax.view_init(elev=elevation, azim=azimuth)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the figure
    print(f"Saving plot to: {output_file}")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Plot saved successfully!")
    
    # Also show the plot
    plt.show()


def main():
    parser = argparse.ArgumentParser(
        description='Create 3D waterfall plot of giant pulses from catalog'
    )
    parser.add_argument(
        'catalog', 
        type=str, 
        help='Path to the TSV catalog file'
    )
    parser.add_argument(
        '-o', '--output', 
        type=str, 
        default='giant_pulses_3d.png',
        help='Output filename (default: giant_pulses_3d.png)'
    )
    parser.add_argument(
        '-n', '--max-pulses', 
        type=int, 
        default=None,
        help='Maximum number of pulses to plot (default: all)'
    )
    parser.add_argument(
        '--no-normalize', 
        action='store_true',
        help='Do not normalize pulse profiles'
    )
    parser.add_argument(
        '--elevation', 
        type=float, 
        default=30,
        help='Elevation angle for 3D view (default: 30)'
    )
    parser.add_argument(
        '--azimuth', 
        type=float, 
        default=-60,
        help='Azimuth angle for 3D view (default: -60)'
    )
    parser.add_argument(
        '-dt', '--downsample-time', 
        type=int, 
        default=1,
        help='Downsample factor in time - plot every Nth pulse (default: 1, no downsampling)'
    )
    parser.add_argument(
        '-dp', '--downsample-phase', 
        type=int, 
        default=1,
        help='Downsample factor for phase bins - average every N bins to smooth profiles (default: 1, no downsampling)'
    )
    parser.add_argument(
        '-s', '--snr-threshold', 
        type=float, 
        default=None,
        help='Minimum SNR threshold - only plot pulses with SNR >= threshold (default: None, plot all)'
    )
    
    args = parser.parse_args()
    
    plot_3d_waterfall(
        catalog_file=args.catalog,
        output_file=args.output,
        max_pulses=args.max_pulses,
        normalize=False,
        elevation=args.elevation,
        azimuth=args.azimuth,
        downsample_time=args.downsample_time,
        downsample_phase=args.downsample_phase,
        snr_threshold=args.snr_threshold
    )


if __name__ == '__main__':
    main()
