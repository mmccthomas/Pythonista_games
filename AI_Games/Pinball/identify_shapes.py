import hashlib
import json
import numpy as np
from pathlib import Path

FINGERPRINT_FILE = 'sprite_fingerprints.json'


# ── Fingerprinting ────────────────────────────────────────────────────────────

def _radial_signature(coords: np.ndarray, n_bins: int = 32) -> np.ndarray:
    """
    Compute a rotation-invariant radial signature from outline coordinates.

    For each angular bin, record the mean distance of points from the centroid.
    Rotate so the bin with the largest value is always first (canonical form).
    Normalise by the overall mean distance so scale doesn't matter.
    """
    centroid = coords.mean(axis=0)
    deltas = coords - centroid
    distances = np.linalg.norm(deltas, axis=1)
    angles = np.arctan2(deltas[:, 1], deltas[:, 0])  # -π ... π

    # Map each point to a bin
    bin_indices = ((angles + np.pi) / (2 * np.pi) * n_bins).astype(int) % n_bins
    bins = np.zeros(n_bins)
    counts = np.zeros(n_bins)
    for i, b in enumerate(bin_indices):
        bins[b] += distances[i]
        counts[b] += 1

    # Fill empty bins by interpolation from neighbours
    for b in range(n_bins):
        if counts[b] == 0:
            prev_b = (b - 1) % n_bins
            next_b = (b + 1) % n_bins
            bins[b] = (bins[prev_b] + bins[next_b]) / 2
        else:
            bins[b] /= counts[b]

    # Canonical rotation: roll so the maximum-distance bin is at index 0
    bins = np.roll(bins, -np.argmax(bins))

    # Normalise by mean so scale is irrelevant
    mean_dist = bins.mean()
    if mean_dist > 0:
        bins /= mean_dist

    return bins


def fingerprint_coords(coords: np.ndarray) -> str:
    """
    Return a short hex string fingerprinting the shape's outline.
    Stable across small extraction variations; invariant to rotation and scale.
    """
    sig = _radial_signature(coords)
    # Quantise to 8-bit integers to absorb tiny float noise
    quantised = (sig * 100).astype(int).clip(0, 255).tolist()
    raw = bytes(quantised)
    return hashlib.md5(raw).hexdigest()[:12]


def signature_distance(coords: np.ndarray, stored_sig: list) -> float:
    """
    L2 distance between a live shape's signature and a stored one.
    Used for fuzzy matching when hash doesn't match exactly.
    """
    live = _radial_signature(coords)
    stored = np.array(stored_sig)
    return float(np.linalg.norm(live - stored))


# ── Registration ──────────────────────────────────────────────────────────────
def register_sprites(shapes: list, image_show=True) -> dict:
    """
    Interactive registration that updates the existing fingerprint file.
    """
    # 1. Load existing data so we don't lose it
    catalogue = load_catalogue()

    for i, shape in enumerate(shapes):
        if image_show:
            shape.image.show()

        print(f'\nShape {i}:')
        print(f'  Auto-description : {shape.description}')
        name = input('  Enter name (blank to skip/exit): ').strip()

        if not name:
            continue

        fp = fingerprint_coords(shape.coordinates)
        if fp in catalogue:
            print(f"  Note: This shape is already registered as '{catalogue[fp]['name']}'")
            overwrite = input("  Overwrite? (y/n): ").lower()
            if overwrite != 'y':
                continue
        sig = _radial_signature(shape.coordinates).tolist()

        # 2. Update the dictionary (this will overwrite if the fingerprint exists)
        catalogue[fp] = {
            'name': name,
            'signature': sig,
            'description': shape.description,
        }
        print(f'  Registered as "{name}" (fp={fp})')

    # 3. Save the merged dictionary back to the file
    with open(FINGERPRINT_FILE, 'w') as f:
        json.dump(catalogue, f, indent=2)

    print(f'\nCatalogue updated. Total sprites: {len(catalogue)}')
    return catalogue
    

# ── Matching ──────────────────────────────────────────────────────────────────

def load_catalogue() -> dict:
    if not Path(FINGERPRINT_FILE).exists():
        return {}
    with open(FINGERPRINT_FILE, 'r') as f:
        return json.load(f)


def identify_shape(shape, catalogue: dict, fuzzy_threshold: float = 0.3) -> str | None:
    """
    Identify a shape by matching its fingerprint against the catalogue.

    1. Try exact hash match first (fast).
    2. Fall back to nearest-neighbour signature distance (robust to
       minor extraction variation).

    Returns the name string, or None if no match is confident enough.
    """
    if not catalogue:
        return None

    fp = fingerprint_coords(shape.coordinates)

    # 1. Exact match
    if fp in catalogue:
        return catalogue[fp]['name']

    # 2. Fuzzy match — find the closest signature
    best_name = None
    best_dist = float('inf')

    for entry in catalogue.values():
        dist = signature_distance(shape.coordinates, entry['signature'])
        if dist < best_dist:
            best_dist = dist
            best_name = entry['name']

    if best_dist <= fuzzy_threshold:
        return best_name

    return None  # unrecognised


def remove_from_catalogue(identifier: str, search_by_name: bool = False):
    """
    Remove a sprite from the JSON file.
    :param identifier: The fingerprint hex string OR the sprite name.
    :param search_by_name: If True, treats identifier as a name.
    """
    catalogue = load_catalogue()
    original_count = len(catalogue)

    if search_by_name:
        # Find all keys where the name matches
        keys_to_remove = [fp for fp, data in catalogue.items() if data['name'] == identifier]
        for k in keys_to_remove:
            del catalogue[k]
    else:
        # Direct fingerprint removal
        if identifier in catalogue:
            del catalogue[identifier]

    if len(catalogue) < original_count:
        with open(FINGERPRINT_FILE, 'w') as f:
            json.dump(catalogue, f, indent=2)
        print(f"Successfully removed '{identifier}'.")
    else:
        print(f"Could not find '{identifier}' in the catalogue.")

                
def list_registered_sprites():
    catalogue = load_catalogue()
    if not catalogue:
        print("Catalogue is empty.")
        return

    print(f"{'Fingerprint':<15} | {'Name':<20} | {'Description'}")
    print("-" * 60)
    for fp, data in catalogue.items():
        print(f"{fp:<15} | {data['name']:<20} | {data.get('description', 'N/A')}")

# Usage:
# list_registered_sprites()
# remove_from_catalogue('Enemy_Slime', search_by_name=True)
