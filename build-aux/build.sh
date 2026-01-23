#!/bin/bash
cd plugins/polars/witt-strutil
maturin develop
maturin build --release