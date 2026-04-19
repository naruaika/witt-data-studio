from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    import polars as pl

    from typing import TypeAlias
    from polars.datatypes import DataType, DataTypeClass

    IntoExprColumn: TypeAlias = Union[pl.Expr, str, pl.Series]
    PolarsDataType: TypeAlias = Union[DataType, DataTypeClass]