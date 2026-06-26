"""
Button Handler Patch — bridges Pi5 power button events to OLED actions.

Monkey-patches the Pi5PowerButtonAddon to add:
  - Short press: advance to next OLED page
  - Double press: pause/resume rotation (shows a tiny pause indicator)
  - Long press (2s+): graceful shutdown (default behavior preserved)

Installation:
  This file patches the existing button addon's callback method.
  Import and call patch_button_handler() after the pironman5 service starts.

  Alternatively, replace the button_callback in pi5_power_button.py directly:
    1. Copy this logic into the button_callback method
    2. Restart pironman5

For the orchestrator integration, the pause state is communicated via
a file flag at /tmp/oled_paused. The orchestrator checks this file
and stops advancing when it exists.
"""
import os
import time

PAUSE_FLAG = '/tmp/oled_paused'


def is_paused():
    """Check if OLED rotation is paused."""
    return os.path.exists(PAUSE_FLAG)


def toggle_pause():
    """Toggle the pause state."""
    if is_paused():
        os.remove(PAUSE_FLAG)
        return False  # now unpaused
    else:
        with open(PAUSE_FLAG, 'w') as f:
            f.write(str(time.time()))
        return True  # now paused


def create_patched_callback(original_addon):
    """
    Create a patched button_callback that adds OLED control.

    Wire this into the Pi5PowerButtonAddon:
        addon.button_callback = create_patched_callback(addon)
    """
    from pm_auto.libs.pi5_power_button import ButtonStatus

    def patched_callback(state):
        if state == ButtonStatus.CLICK:
            # Short press: advance to next page (wake if sleeping)
            original_addon.log.info("Button: short press → next page")
            original_addon.event.publish('oled_wake_page_next', state)

        elif state == ButtonStatus.DOUBLE_CLICK:
            # Double press: toggle pause
            paused = toggle_pause()
            original_addon.log.info(f"Button: double press → {'paused' if paused else 'resumed'}")
            # Publish a custom event the orchestrator can listen for
            original_addon.event.publish('oled_pause_toggle', paused)

        elif state == ButtonStatus.LONG_PRESS_2S:
            # Long press: shutdown (preserve default behavior)
            original_addon.log.info("Button: long press → shutdown")
            original_addon.event.publish('pi5_power_button_long_press', 'button_long_press')

        elif state == ButtonStatus.LONG_PRESS_2S_RELEASED:
            original_addon.log.info("Button: long press released → executing shutdown")
            original_addon.event.publish('shutdown', 'button_long_press')

    return patched_callback
