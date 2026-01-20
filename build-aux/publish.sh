#!/bin/bash
cd plugins/polars/witt-strutil
cp target/wheels/* dist/
python3 -m twine upload dist/*