#!/usr/bin/env python3
"""
Output volumes of each probabilistic label in an atlas in microliters.
Accepts multiple 4D prob atlas files

Usage
----
prob_label_volumes.py <atlas_file>
prob_label_volumes.py -h

Example
----
>>> prob_label_vol_info.py *_probs.nii.gz

Authors
----
Mike Tyszka, Caltech Brain Imaging Center

Dates
----
2015-05-31 JMT Adapt from label_volumes.py
2017-10-22 WMP Adapt from prob_label_volumes.py
               Add latex table output
2017-12-12 JMT Extended latex table with left and right volumes

License
----
This file is part of atlaskit.

    atlaskit is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    atlaskit is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with atlaskit.  If not, see <http://www.gnu.org/licenses/>.

Copyright
----
2017 California Institute of Technology.
"""

__version__ = '0.1.0'

import os
import sys
import argparse
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
from atlas_report import do_strip_prefix


def load_labels(filename):
    """
    Load labels from file, which was used as label key in inkscape

    Parameters
    ----------
    filename

    Returns
    -------

    """

    keys = []
    
    label_file = open(filename, 'r')
    entries = label_file.readlines()
    label_file.close()

    for e in range(0, len(entries)):
        entry = entries[e]
        if not entry[0].startswith('#'):
            start = entry.find('"') + 1
            end = entry.find('"', start)
            label_name = entry[start:end]
            if not 'Clear Label' in label_name:
                keys.append(label_name)

    return keys


def create_histogram(p, keys, nrows=4, ncols=4, fontsize=16, img_fname='prob_atlas_hist.png'):
    """
    Create a cumulative histogram for each label in a probabilistic atlas

    Parameters
    ----------
    p: numpy array
    keys
    nrows
    ncols
    fontsize
    img_fname

    Returns
    -------

    """

    fig, axs = plt.subplots(nrows, ncols, figsize=(12,9))
    axs = np.array(axs).reshape(-1)

    im = []

    # Determine lower left axis index
    lower_left = (nrows - 1) * ncols

    for aa, ax in enumerate(axs):

        if aa < len(keys):
            v = p[:,:,:,aa].ravel()
            v = v[v > 0]
            im = ax.hist(v, bins=50, cumulative=True, density=True, range=(0,1))
            key = do_strip_prefix(keys[aa])
            ax.set_title(key, fontsize=fontsize)
        else:
            ax.axis('off')

        if aa == lower_left:

            ax.set_xlabel('Label Probability', fontsize=fontsize)
            ax.set_ylabel('CRF', fontsize=fontsize)

            for tick in ax.xaxis.get_major_ticks():
                tick.label.set_fontsize(int(fontsize * 0.9))
            for tick in ax.yaxis.get_major_ticks():
                tick.label.set_fontsize(int(fontsize * 0.9))

        else:

            ax.get_xaxis().set_visible(False)
            ax.get_yaxis().set_visible(False)

    # Tidy up spacing
    plt.tight_layout()

    print('Saving image to %s' % img_fname)
    plt.savefig(os.path.join(img_fname), dpi=300, bbox_inches='tight')


def print_vol_info(p_file, keys, latex=False):
    """
    Generate integrated volume table for left and right hemispheres

    Parameters
    ----------
    p_file
    keys
    latex

    Returns
    -------

    """

    # Load the source atlas image
    p_nii = nib.load(p_file)
    p = p_nii.get_data()
    nd = p.ndim
        
    # Atlas voxel volume in mm^3 (microliters)
    atlas_vox_vol_ul = np.array(p_nii.header.get_zooms()).prod()
                   
    nx, ny, nz, nt = p.shape
    hx = int(nx/2)

    # Table preamble
    if latex:

        # Print latex header (depends on booktabs package)
        print("")
        print("\\begin{tabular}{l c c c c}")
        print("\\cmidrule{1-5}")
        print("\\multicolumn{2}{c}{} & \\multicolumn{2}{c}{Volume ($\\mu l$)} \\\\")
        print("\\cmidrule{3-4}")
        print("Label & Acronym & Left & Right & Laterality (\\%) \\\\")
        print("\\cmidrule{1-5}")

    else:

        print("")
        print('%s\t%s\t%s\t%s' % ("Label", "Vol_Left_ul", "Vol_Right_ul", "LI_perc"))

    for t in range(0,nt):

        label = keys[t]

        # Split at underscores and retain final acronym
        acronym = label.rsplit('_')[-1]

        # Right and left integrated volumes
        # x-dimension is assumed to run R-L, so right hemisphere is lower x half-space
        Vr = np.sum(p[0:hx, :, :, t]) * atlas_vox_vol_ul
        Vl = np.sum(p[hx:-1, :, :, t]) * atlas_vox_vol_ul

        # Laterality Index (%)
        LIp = (Vl - Vr) / (Vl + Vr) * 100.0

        if latex:
            print('%s & %s & %0.0f & %0.0f & %0.1f \\\\' % ("LABEL", acronym, Vl, Vr, LIp))
        else:
            print('%s\t%0.0f\t%0.0f\t%0.1f' % (acronym, Vl, Vr, LIp))

    if latex:
        print("\\cmidrule{1-5}")
        print("\\end{tabular}")

    # Final newline
    print("")
    
    return p


def main():
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Probabilistic label volumes in microliters')
    parser.add_argument('-d', '--atlas_dir', required=False, help="Directory of probabilistic atlas and label file")
    parser.add_argument('--latex', dest='latex', action='store_true')

    # Parse command line arguments
    args = parser.parse_args()

    if args.atlas_dir:
        atlas_dir = args.atlas_dir
    else:
        atlas_dir = os.getcwd()

    print("Atlas Directory : %s" % atlas_dir)
    p_file = os.path.join(atlas_dir, 'prob_atlas_bilateral.nii.gz')
    l_file = os.path.join(atlas_dir, 'labels.txt')

    if os.path.exists(p_file):
        print("Prob Atlas File : %s" % p_file)
    if os.path.exists(l_file):
        print("Label Text File : %s" % l_file)

    latex = args.latex
    
    keys = load_labels(l_file)
        
    # Force absolute path
    p_file = os.path.abspath(p_file)
                
    p = print_vol_info(p_file, keys, latex=latex)
    
    # create histogram of label probabilities for each label
    create_histogram(p, keys)
    
    # Clean exit
    sys.exit(0)

    
# This is the standard boilerplate that calls the main() function.
if __name__ == '__main__':
    main()
