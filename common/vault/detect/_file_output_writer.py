import base64
import os

from common.errors import SkyflowError
from common.utils import SkyflowMessages
from common.utils.enums.detect import DataSourceType

from ._constants import (
    PROCESSED_FILE_PREFIX,
    ENTITIES_TYPE_TOKEN,
    ENTITIES_EXTENSION,
    BINARY_EXTENSION,
    DEFAULT_OUTPUT_BASE_NAME,
    EXTENSION_SEPARATOR,
    UNDERSCORE,
    DASH,
)


def write_outputs(outputs, output_type, input_file_name, output_directory):
    if not outputs:
        return []
    if output_type != DataSourceType.BASE64:
        return []

    directory = None
    if output_directory and output_directory.strip():
        directory = output_directory
        if not os.path.isdir(directory):
            try:
                os.makedirs(directory, exist_ok=True)
            except OSError:
                raise SkyflowError(
                    SkyflowMessages.Error.FAILED_TO_WRITE_OUTPUT_FILE.value.format(directory),
                    None,
                )

    base = _strip_extension(input_file_name)
    used = set()
    written = []
    for output in outputs:
        if output.processed_file is None:
            continue
        name = _file_name(base, output, used)
        used.add(name)
        target = name if directory is None else os.path.join(directory, name)
        try:
            data = base64.b64decode(output.processed_file)
            with open(target, "wb") as handle:
                handle.write(data)
        except (ValueError, OSError):
            raise SkyflowError(
                SkyflowMessages.Error.FAILED_TO_WRITE_OUTPUT_FILE.value.format(target),
                None,
            )
        written.append(target)
    return written


def _strip_extension(file_name):
    if not file_name:
        return DEFAULT_OUTPUT_BASE_NAME
    base = os.path.basename(file_name)
    dot = base.rfind(EXTENSION_SEPARATOR)
    if dot > 0:
        base = base[:dot]
    return base or DEFAULT_OUTPUT_BASE_NAME


def _file_name(base, output, used):
    file_type = output.processed_file_type or ""
    is_entities = ENTITIES_TYPE_TOKEN in file_type.upper()
    if output.processed_file_extension is not None:
        extension = output.processed_file_extension.value
    elif is_entities:
        extension = ENTITIES_EXTENSION
    else:
        extension = BINARY_EXTENSION

    if is_entities:
        stem = PROCESSED_FILE_PREFIX + file_type.lower().replace(UNDERSCORE, DASH) + DASH + base
    else:
        stem = PROCESSED_FILE_PREFIX + base

    name = stem + EXTENSION_SEPARATOR + extension
    if name in used:
        disambiguator = str(len(used)) if file_type == "" else file_type.lower()
        name = stem + EXTENSION_SEPARATOR + disambiguator + EXTENSION_SEPARATOR + extension
    return name
