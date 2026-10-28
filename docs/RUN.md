
# Running stm32loader


## Execute as a module

After installing stm32loader with `pip`, it's available as a Python module.

You can execute this with `python -m [modulename]`.

```shell
python3 -m stm32loader
```


## Run from a repository checkout

Install the project in editable mode, then run it as a module.

```shell
python3 -m pip install --editable .
python3 -m stm32loader
```

Alternatively, with `uv`:

```shell
uv run stm32loader
```


## Use from Python

You can use the classes of `stm32loader` from a Python script.

Example:

```python
import logging

from stm32loader.main import Stm32Loader

# Show stm32loader's progress messages.
logging.basicConfig(level=logging.INFO, format="%(message)s")

loader = Stm32Loader()
loader.parse_arguments(["--port", "/dev/cu.usbserial-A5XK3RJT"])
loader.connect()
try:
    loader.stm32.readout_unprotect()
finally:
    loader.stm32.connection.disconnect()
```
