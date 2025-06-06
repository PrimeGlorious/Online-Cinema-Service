from loguru import logger


def setup_logger():
    logger.remove()
    log_path = "/app/logs/core_logs.log"
    logger.add(
        log_path,
        colorize=False,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {file}:{line} | {message}",
        rotation=None,
        retention=None,
        compression=None,
    )
