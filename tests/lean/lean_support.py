"""Load the seven release cells with an explicitly local transport for unit tests."""
import ast
import contextlib
import copy
import io
import os
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests"))
CELLS = Path(os.environ.get("LEAN_CELLS_DIR", ROOT / "notebooks/cells"))


class Row(dict):
    def as_dict(self, recursive=True):
        return dict(self)


class Frame:
    def __init__(self, rows):
        self.rows = [Row(copy.deepcopy(row)) for row in rows]
        self.columns = list(self.rows[0]) if self.rows else []

    def collect(self):
        return list(self.rows)

    def count(self):
        return len(self.rows)

    def to_local_iterator(self):
        return iter(self.rows)


class Field:
    def __init__(self, name, datatype=None, **kwargs):
        self.name = name


class Session:
    def create_dataframe(self, rows, schema=None):
        if schema is not None:
            rows = [dict(zip([field.name for field in schema], row)) for row in rows]
        return Frame(rows)


def namespace(cells_dir=None, models=("SSP", "ASSESSMENT_RESULTS")):
    """Execute fresh definitions; no fallback to another engine's functions."""
    directory = Path(cells_dir) if cells_dir is not None else CELLS
    ns = dict(session=Session(), get_active_session=Session, StructType=list, StructField=Field,
              StringType=lambda: None, TimestampType=lambda *args: None,
              TimestampTimeZone=SimpleNamespace(TZ="TZ"))
    with contextlib.redirect_stdout(io.StringIO()):
        for path in sorted(directory.glob("*.py")):
            number = int(path.name[:2])
            body = []
            for node in ast.parse(path.read_text(encoding="utf-8")).body:
                if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("snowflake"):
                    continue
                if number == 2 and not isinstance(node, (ast.FunctionDef, ast.Import, ast.ImportFrom)):
                    continue
                if isinstance(node, ast.Assign):
                    names = [target.id for target in node.targets if isinstance(target, ast.Name)]
                    if set(names) & {"MAPPING_CONTEXTS", "MODEL_GRAPHS"}:
                        break
                    if names == ["SELECTED_MODELS"]:
                        node.value = ast.parse(repr(models), mode="eval").body
                body.append(node)
            tree = ast.fix_missing_locations(ast.Module(body=body, type_ignores=[]))
            exec(compile(tree, str(path), "exec"), ns)
    return ns


def business(frame):
    audit = {"DW_PIPELINE_RUN_ID", "DW_LOAD_TIMESTAMP", "DW_LOAD_TIMESTAMP_TZ", "PARENT_NODE_PATH"}
    rows = [{key: value for key, value in row.items() if key not in audit} for row in frame.rows]
    return sorted(rows, key=lambda row: row.get("NODE_KEY", row.get("EDGE_KEY")))


def build(ns, context, records):
    config = context["config"]
    return ns["build_oscal_graph"](Frame(records), None, None, config["OSCAL_MODEL"],
                                   config["SOURCE_SYSTEM_NAME"], config["SOURCE_TABLE_NAME"], context=context)
