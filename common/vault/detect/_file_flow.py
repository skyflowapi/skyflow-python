import time

from common.utils.enums.detect import DetectRunStatus

from ._file_output_writer import write_outputs
from ._mappers import submitted_deidentify_file_response, to_deidentify_file_response
from ._polling import poll_run


def complete_deidentify_file(request, run_id, fetcher, logger=None, sleeper=time.sleep):
    if request.poll_options is None or run_id is None:
        return submitted_deidentify_file_response(run_id)

    run = poll_run(run_id, request.poll_options, fetcher, logger=logger, sleeper=sleeper)
    response = to_deidentify_file_response(run_id, run)

    if response.status == DetectRunStatus.SUCCESS and (request.file is not None or request.file_path is not None):
        input_name = request.file_path if request.file_path is not None else getattr(request.file, "name", None)
        write_outputs(response.output, response.output_type, input_name, request.output_directory)

    return response
