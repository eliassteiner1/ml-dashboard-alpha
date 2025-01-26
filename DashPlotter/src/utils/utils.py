import matplotlib.colors as mcolors
  
def adjust_alpha(color: str, adjust_a: float):
    """Takes a css "color name", "rgb(r, g, b)", or "rgba(r, g, b, a)" string and outputs the color in "rgba" format
    with adjust_a times the original alpha value."""
    
    if color.startswith("rgb"):
        components = color[color.index("(")+1:color.index(")")].split(",")
        r, g, b    = map(int, components[:3])  # Extract RGB components
        a          = float(components[3]) if len(components) == 4 else 1.0  # a assumed to be 1.0 if not provided
    else:
        # Assume it's a CSS color name
        r, g, b = [int(c * 255) for c in mcolors.to_rgb(color)]
        a = 1.0

    a *= adjust_a
    a = max(0, min(a, 1)) # Ensure alpha stays in range [0, 1]
    return f"rgba({r}, {g}, {b}, {a:.3f})"