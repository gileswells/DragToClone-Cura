# Drag to Clone — Cura Plugin

Hold **Alt/Option** while dragging a model on the build plate to leave a clone behind at the original position. Works with both the **Move** and **Rotate** tools.

## Usage

1. Select a model on the build plate.
2. Switch to the **Move** tool (T) or **Rotate** tool (R).
3. Hold **Alt/Option** and drag.

A copy of the model stays at the original location while the original moves or rotates to wherever you drag it. Releasing the mouse completes the operation. **Undo (Ctrl+Z / Cmd+Z)** reverts both the clone and the drag in a single step.

Also works a user would expect with multi-selection and grouped models.

## Compatibility

| Cura version | Supported |
|---|---|
| 5.x (SDK 8) | ✓ |
| 4.x (SDK 7) | Not tested |

## Installation

### Via the UltiMaker Marketplace
Search for **"Drag to Clone"** in the Marketplace panel inside Cura and click **Install**.

### Manual installation
1. Download or clone this repository.
2. Copy the `DragToClone` folder into your Cura plugins directory:
   - **macOS:** `~/Library/Application Support/cura/<version>/plugins/`
   - **Windows:** `%APPDATA%\cura\<version>\plugins\`
   - **Linux:** `~/.local/share/cura/<version>/plugins/`
3. Restart Cura.

## How it works

The plugin is a lightweight Cura **Extension** (no toolbar UI). It listens to the controller's `toolOperationStarted` signal and, when Alt/Option is held, deep-copies the selected node(s) and parents them into the scene immediately so the clone is visible during the drag. When the drag finishes (`toolOperationStopped`), it registers an `_AddClonesOperation` on the undo stack that merges with the tool's own move/rotate operation — the same merge pattern used by Cura's built-in `PlatformPhysicsOperation` — so the whole action collapses into a single undo step.

## License

Released under the [LGPLv3](https://www.gnu.org/licenses/lgpl-3.0.html) or higher, consistent with Cura's own licensing.
