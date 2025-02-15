
import colorsys

import d3script

import colorsys


def adjust_color_feel_hue_saturation_hsb(hue, saturation, adjustment_channel, adjustment_value, epsilon=1e-3):
    """
    Adjusts the color to feel more or less red, green, or blue by modifying other channels only if the target channel
    cannot be modified further. In the case of secondary adjustment, only half of the adjustment value is applied to the other channels.

    The brightness is assumed to be 1 in HSB model.

    Parameters:
    hue (float): The hue value (0-1).
    saturation (float): The saturation value (0-1).
    adjustment_channel (str): The channel to adjust ('red', 'green', or 'blue').
    adjustment_value (float): The adjustment value (-1 to 1) to modify the color feel. Negative reduces the feel, positive increases it.
    epsilon (float): A small threshold to consider values very close to 0 or 1 as limits.

    Returns:
    tuple: (new_hue, new_saturation)
    """

    # Convert HSB (hue, saturation, brightness) to RGB with brightness always 1
    r, g, b = colorsys.hsv_to_rgb(hue, saturation, 1)

    # Store RGB values in a dictionary for easier manipulation
    channels = {'red': r, 'green': g, 'blue': b}

    # Identify the other two channels for secondary adjustment
    primary_value = channels[adjustment_channel]
    other_channels = [ch for ch in channels if ch != adjustment_channel]

    # Helper function to adjust a channel value with bounds check
    def adjust_primary(value, adj):
        return min(1, max(0, value + adj * (1 - value) if adj > 0 else value * (1 + adj)))

    def adjust_secondary(value, adj):
        return min(1, max(0, value * (1 - adj / 2) if adj > 0 else value + (-adj * (1 - value) / 2)))

    # Perform primary and secondary adjustments
    if epsilon < primary_value < 1 - epsilon:
        channels[adjustment_channel] = adjust_primary(primary_value, adjustment_value)
    else:  # If close to 0 or 1, perform secondary adjustment
        for ch in other_channels:
            channels[ch] = adjust_secondary(channels[ch], adjustment_value)

    # Extract updated RGB values
    r, g, b = channels['red'], channels['green'], channels['blue']

    # Convert back to HSB (HSV)
    new_hue, new_saturation, new_brightness = colorsys.rgb_to_hsv(r, g, b)

    return new_hue, new_saturation


def adjust_temperature_cct(hue, saturation, cct_increment):
    """
    Adjusts the color temperature based on correlated color temperature (CCT) degrees.

    Args:
        hue (float): The hue value (normalized 0-1).
        saturation (float): The saturation value (normalized 0-1).
        cct_increment (float): The change in color temperature in degrees (positive for cooler, negative for warmer).

    Returns:
        tuple: A tuple containing the modified hue and saturation (both normalized 0-1).
    """
    # Convert HSV (Hue, Saturation, Value) to RGB
    value = 1  # Assume full brightness for the color
    r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)

    # Normalize the cct_increment to a range we can work with (assuming -10000 to +10000 for temperature)
    max_cct = 10000  # You can set this to any reasonable maximum temperature range
    adjustment_factor = cct_increment / max_cct

    if adjustment_factor > 0:
        # Cooler: Increase blue, decrease red and green
        b = min(1, b + adjustment_factor)  # Increase blue
        r = max(0, r - adjustment_factor)  # Decrease red
        g = max(0, g - adjustment_factor)  # Decrease green
    elif adjustment_factor < 0:
        # Warmer: Increase red, decrease blue and green
        r = min(1, r - adjustment_factor)  # Increase red
        b = max(0, b + adjustment_factor)  # Decrease blue
        g = max(0, g + adjustment_factor)  # Decrease green

    # Convert the modified RGB back to HSV
    new_hue, new_saturation, _ = colorsys.rgb_to_hsv(r, g, b)

    return new_hue, new_saturation