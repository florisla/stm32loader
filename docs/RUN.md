
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
from stm32loader.main import Stm32Loader

loader = Stm32Loader()
loader.configuration.port = "/dev/cu.usbserial-A5XK3RJT"
loader.connect()
loader.stm32.readout_unprotect()
loader.disconnect()
```
