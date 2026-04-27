# Horner Python Test

Overview
- Small project demonstrating a Horner-style polynomial GUI and CLI interface plus supporting services.

Contents
- `main.py` — Primary GUI entry point (runs the application window).
- `cli.py` — Command-line interface for quick testing or non-GUI usage.
- `horner_gui.ui` — Qt Designer UI file for the GUI.
- `horner_gui_ui.py` — Generated Python UI module for the `.ui` file.
- `gui_designer.py`, `gui_step1.py`, `gui_test.py` — helper GUI scripts and experiments.
- `modbus_service.py` — Modbus-related service (if your setup uses Modbus communication).
- `test_service.py` — Small test harness for services or integration tests.
- `main_registers.py` — Register management helpers used by the GUI/services.

Requirements
- Python 3.8 or newer recommended.
- Recommended (install into a virtualenv):

```bash
python -m venv .venv
source .venv/bin/activate   # On Windows use: .venv\\Scripts\\activate
pip install -r requirements.txt  # if a requirements file exists
```

If you don't have a `requirements.txt`, common dependencies used by this project include `PyQt5` (or `PySide2`) and `pymodbus` for Modbus support. Install them with:

```bash
pip install PyQt5 pymodbus
```

Running the GUI
- Start the GUI application (default entry):

```bash
python main.py
```

- If you modify the Qt Designer file `horner_gui.ui`, regenerate the Python UI file with `pyuic5` (PyQt5) or the equivalent for your toolkit:

```bash
pyuic5 -x horner_gui.ui -o horner_gui_ui.py
```

Running the CLI
- Use the CLI script for quick tests or headless operation:

```bash
python cli.py
```

Services & Tests
- Run the Modbus service (if applicable to your environment):

```bash
python modbus_service.py
```

- Run the simple test harness:

```bash
python test_service.py
```

Using the System Architecture (Multi-PLC Management)
- The `system/` folder contains a scalable architecture for managing multiple PLCs:
  - `plc_manager.py` — Central manager coordinating multiple PLCs
  - `plc_device.py` — Individual PLC device abstraction
  - `config.py` — Centralized PLC configuration
  - `events.py` — Event system for real-time notifications
  - `constants.py` — Shared constants (coil/register addresses)

System CLI Examples
- The new `system_cli.py` provides a modern interface for all operations:

```bash
# Connect to all PLCs
python system_cli.py connect

# Show system status
python system_cli.py status

# Read/write single PLC
python system_cli.py read-coil HORNER_1 6000
python system_cli.py write-coil HORNER_1 6000 true
python system_cli.py read-register HORNER_1 3000
python system_cli.py write-register HORNER_1 3000 123

# Synchronized reads across all PLCs
python system_cli.py sync-read-coil 6000
python system_cli.py sync-read-register 3000

# Full demo
python system_cli.py demo --debug

# Show command help
python system_cli.py --help
```

Development notes
- Use a virtual environment and keep dependencies in a `requirements.txt` for reproducible installs.
- Keep the generated UI file (`horner_gui_ui.py`) in sync with `horner_gui.ui` if you edit the UI.
- The new `system/` architecture supports easy scaling to multiple PLCs without code duplication.
- Events are emitted for all operations, enabling real-time monitoring and logging.

Contact
- If something doesn't run, open an issue in this repo or contact the project maintainer.
