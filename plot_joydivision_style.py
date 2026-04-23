#!/usr/bin/env python3
"""
Create a Joy Division "Unknown Pleasures" style plot for giant pulses.
Stacks pulse profiles with white lines on black background.
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
from psrchive import Archive
import argparse
import matplotlib
from matplotlib.colors import LinearSegmentedColormap
matplotlib.use('TkAgg') 

# Set the style to dark background
# plt.style.use('dark_background')


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
        ar.remove_baseline()
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
            profile = profile[:n_new_bins * downsample_phase].reshape(n_new_bins, downsample_phase).mean(axis=1)
        
        return profile
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None


def plot_joydivision_style(catalog_file, output_file='giant_pulses_joydivision.png', 
                           max_pulses=None, downsample_time=1, downsample_phase=1, 
                           snr_threshold=None, width_min=None, width_max=None, 
                           vertical_scale=1.0, line_spacing=1.0,
                           phase_min=0.0, phase_max=1.0, use_gradient=True,
                           gradient_colors=None):
    """
    Create a Joy Division "Unknown Pleasures" style plot of giant pulses.
    
    Parameters:
    -----------
    catalog_file : str
        Path to the catalog file
    output_file : str
        Output filename for the plot
    max_pulses : int or None
        Maximum number of pulses to plot (None = all)
    downsample_time : int
        Downsample factor in time (plot every Nth pulse)
    downsample_phase : int
        Downsample factor for phase bins
    snr_threshold : float or None
        Minimum SNR threshold
    width_min : float or None
        Minimum width in milliseconds
    width_max : float or None
        Maximum width in milliseconds
    vertical_scale : float
        Scale factor for profile amplitudes (default: 1.0)
    line_spacing : float
        Vertical spacing between lines (default: 1.0)
    phase_min : float
        Minimum phase to display (0.0 to 1.0)
    phase_max : float
        Maximum phase to display (0.0 to 1.0)
    use_gradient : bool
        Whether to use color gradient horizontally (default: True)
    gradient_colors : list or None
        List of colors for gradient from left to right, e.g., ['black', 'white']
        Default: ['#000000', '#FFFFFF'] (black to white, left to right)
    """
    
    # Read the catalog
    print(f"Reading catalog: {catalog_file}")
    df = pd.read_csv(catalog_file, sep=r'\s+', comment='#')
    
    # Filter by SNR threshold if specified
    if snr_threshold is not None:
        initial_count = len(df)
        df = df[df['snr_xprof'] >= snr_threshold].reset_index(drop=True)
        print(f"Filtered by SNR >= {snr_threshold}: {len(df)}/{initial_count} pulses")
    
    # Filter by width_ms range if specified
    if width_min is not None or width_max is not None:
        initial_count = len(df)
        if width_min is not None and width_max is not None:
            df = df[(df['width_ms'] >= width_min) & (df['width_ms'] <= width_max)].reset_index(drop=True)
            print(f"Filtered by {width_min} <= width <= {width_max} ms: {len(df)}/{initial_count} pulses")
        elif width_min is not None:
            df = df[df['width_ms'] >= width_min].reset_index(drop=True)
            print(f"Filtered by width >= {width_min} ms: {len(df)}/{initial_count} pulses")
        elif width_max is not None:
            df = df[df['width_ms'] <= width_max].reset_index(drop=True)
            print(f"Filtered by width <= {width_max} ms: {len(df)}/{initial_count} pulses")
    
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
    
    for idx, row in df.iterrows():
        filepath = row['filename']
        
        # Check if file exists
        if not os.path.exists(filepath):
            print(f"Warning: File not found: {filepath}")
            continue
            
        profile = load_pulse_profile(filepath, downsample_phase=downsample_phase)
        
        if profile is not None:
            # Normalize profile
            profile = profile - np.min(profile)
            if np.max(profile) > 0:
                profile = profile / np.max(profile)
            
            profiles.append(profile)
            times.append(row['toa_xprof'])
        
        if (idx + 1) % 100 == 0:
            print(f"Loaded {idx + 1}/{len(df)} profiles...")
    
    if len(profiles) == 0:
        print("Error: No profiles could be loaded!")
        return
    
    print(f"Successfully loaded {len(profiles)} profiles")
    
    # Set up gradient colors (default: black to white for left to right)
    if gradient_colors is None:
        gradient_colors = ['#000000', '#FFFFFF']  # Black to white
    
    # Create the figure with white background
    fig, ax = plt.subplots(figsize=(12, 10), facecolor='white')
    ax.set_facecolor('white')
    
    # Get the number of phase bins
    n_bins = len(profiles[0])
    phase = np.linspace(0, 1, n_bins)
    
    # Filter phase range
    phase_mask = (phase >= phase_min) & (phase <= phase_max)
    phase = phase[phase_mask]
    
    n_profiles = len(profiles)
    
    # Plot each profile - NOT reversed, so top profiles are drawn last (on top)
    for i, profile in enumerate(profiles):
        # Filter by phase range
        profile_segment = profile[phase_mask]
        
        # Scale the profile
        scaled_profile = profile_segment * vertical_scale
        
        # Calculate vertical offset (reverse the y position)
        y_offset = (len(profiles) - 1 - i) * line_spacing
        
        # Fill under the curve with white first (this will hide lines below)
        ax.fill_between(phase, y_offset, scaled_profile + y_offset, 
                        color='white', zorder=i*2)
        
        # Plot the line with horizontal gradient (black to white, left to right)
        if use_gradient:
            # Create a colormap for black to white gradient
            cmap = LinearSegmentedColormap.from_list('custom', gradient_colors)
            
            # Plot line segments with varying colors
            n_segments = len(phase) - 1
            for j in range(n_segments):
                # Normalize position along the phase axis (0 at left, 1 at right)
                color_position = j / (n_segments - 1) if n_segments > 1 else 0.5
                segment_color = cmap(color_position)
                
                ax.plot(phase[j:j+2], scaled_profile[j:j+2] + y_offset, 
                       color=segment_color, linewidth=1.5, antialiased=True, 
                       solid_capstyle='round', solid_joinstyle='round',
                       zorder=i*2+1, alpha=0.3)
        else:
            # Plot solid black line
            ax.plot(phase, scaled_profile + y_offset, 'k-', 
                   linewidth=1.5, antialiased=True, 
                   solid_capstyle='round', solid_joinstyle='round',
                   zorder=i*2+1, alpha=0.1)

    # Remove axes for clean look
    ax.axis('off')
    
    # Adjust layout
    plt.tight_layout(pad=0)
    
    # Save the figure
    print(f"Saving plot to: {output_file}")
    plt.savefig(output_file, dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none', pad_inches=0.1)
    print(f"Plot saved successfully!")
    
    # Also show the plot
    plt.show()


def main():
    parser = argparse.ArgumentParser(
        description='Create Joy Division style plot of giant pulses',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with first 50 pulses
  ./plot_joydivision_style.py xprof.pdmp.giants.catalog -n 50
  
  # With SNR threshold and custom scaling
  ./plot_joydivision_style.py xprof.pdmp.giants.catalog -s 15 -v 2.0 -l 0.8
  
  # Focus on main pulse region (phase 0.3-0.7)
  ./plot_joydivision_style.py xprof.pdmp.giants.catalog -n 100 --phase-min 0.3 --phase-max 0.7
  
  # With gradient (blue to white to red)
  ./plot_joydivision_style.py xprof.pdmp.giants.catalog -n 100 --gradient
  
  # Custom gradient colors
  ./plot_joydivision_style.py xprof.pdmp.giants.catalog -n 100 --gradient --gradient-colors purple white orange
        """
    )
    
    parser.add_argument(
        'catalog', 
        type=str, 
        help='Path to the catalog file'
    )
    parser.add_argument(
        '-o', '--output', 
        type=str, 
        default='giant_pulses_joydivision.png',
        help='Output filename (default: giant_pulses_joydivision.png)'
    )
    parser.add_argument(
        '-n', '--max-pulses', 
        type=int, 
        default=None,
        help='Maximum number of pulses to plot (default: all)'
    )
    parser.add_argument(
        '-dt', '--downsample-time', 
        type=int, 
        default=1,
        help='Downsample factor in time - plot every Nth pulse (default: 1)'
    )
    parser.add_argument(
        '-dp', '--downsample-phase', 
        type=int, 
        default=1,
        help='Downsample factor for phase bins (default: 1)'
    )
    parser.add_argument(
        '-s', '--snr-threshold', 
        type=float, 
        default=None,
        help='Minimum SNR threshold (default: None, plot all)'
    )
    parser.add_argument(
        '--width-min', 
        type=float, 
        default=None,
        help='Minimum pulse width in milliseconds (default: None)'
    )
    parser.add_argument(
        '--width-max', 
        type=float, 
        default=None,
        help='Maximum pulse width in milliseconds (default: None)'
    )
    parser.add_argument(
        '-v', '--vertical-scale', 
        type=float, 
        default=1.0,
        help='Vertical scale factor for profile amplitudes (default: 1.0)'
    )
    parser.add_argument(
        '-l', '--line-spacing', 
        type=float, 
        default=1.0,
        help='Vertical spacing between lines (default: 1.0)'
    )
    parser.add_argument(
        '--phase-min', 
        type=float, 
        default=0.0,
        help='Minimum phase to display (0.0-1.0, default: 0.0)'
    )
    parser.add_argument(
        '--phase-max', 
        type=float, 
        default=1.0,
        help='Maximum phase to display (0.0-1.0, default: 1.0)'
    )
    parser.add_argument(
        '--gradient',
        action='store_true',
        help='Enable color gradient (default: True, use --no-gradient to disable)'
    )
    parser.add_argument(
        '--no-gradient',
        action='store_true',
        help='Disable color gradient (use solid black lines)'
    )
    parser.add_argument(
        '--gradient-colors',
        type=str,
        nargs='+',
        default=None,
        help='Custom gradient colors (e.g., blue white red, or #0000FF #FFFFFF #FF0000)'
    )
    
    args = parser.parse_args()
    
    # Validate phase range
    if not (0.0 <= args.phase_min < args.phase_max <= 1.0):
        print("Error: phase_min must be < phase_max, and both must be in [0, 1]")
        return
    
    # Determine gradient usage
    use_gradient = not args.no_gradient  # Default is True unless --no-gradient is used
    if args.gradient:
        use_gradient = True
    
    plot_joydivision_style(
        catalog_file=args.catalog,
        output_file=args.output,
        max_pulses=args.max_pulses,
        downsample_time=args.downsample_time,
        downsample_phase=args.downsample_phase,
        snr_threshold=args.snr_threshold,
        width_min=args.width_min,
        width_max=args.width_max,
        vertical_scale=args.vertical_scale,
        line_spacing=args.line_spacing,
        phase_min=args.phase_min,
        phase_max=args.phase_max,
        use_gradient=use_gradient,
        gradient_colors=args.gradient_colors
    )


if __name__ == '__main__':
    main()