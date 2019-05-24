import asyncio
import json
import logging
import os

import aio_pika
import structlog

from django import db
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from os2datascanner.engine.run_webscan import StartWebScan
from os2datascanner.engine.run_filescan import StartFileScan

from ...models.scans.scan_model import Scan

logger = structlog.get_logger()


async def check_running_scans():
    while True:
        try:
            with transaction.atomic():
                running_scans = Scan.objects.filter(
                    status=Scan.STARTED
                ).select_for_update(nowait=True)

                logger.debug("check_running_scans", scans=len(running_scans))

                for scan in running_scans:
                    if not scan.pid and not hasattr(scan, "exchangescan"):
                        continue
                    try:
                        # Check if process is still running
                        os.kill(scan.pid, 0)
                        logger.debug(
                            "scan_ok", scan=scan.pk, scan_pid=scan.pid
                        )
                    except OSError:
                        logger.critical(
                            "scan_disappeared",
                            scan_id=scan.pk,
                            scan_pid=scan.pid,
                            exc_info=True,
                        )

                        scan.set_scan_status_failed(
                            "FAILED: process {} disappeared".format(scan.pid)
                        )

        except Exception:
            logger.warning("check_running_scans_failed", exc_info=True)

        await asyncio.sleep(settings.CHECK_SCAN_INTERVAL)


def handle_exit(pid, returncode, scan_id):
    """A scan process died; update its status pending on the success value."""

    if returncode == 0:
        event = "scan_done"
        level = logging.INFO

        # should we call scan.set_status_done() here?

    else:
        event = "scan_failed"
        level = logging.CRITICAL

        scan = Scan.objects.get(pk=scan_id)
        scan.set_status_failed("process exited with {}".format(returncode))

    logger.log(level, event, scan_id=scan_id, scan_pid=pid, status=returncode)


async def process_message(message):
    """Process the given AMQP message, representing a scan.

    This function should handle all exception internally.
    """
    try:
        body = message.body.decode("utf-8")
        body = json.loads(body)
    except Exception:
        logger.exception("scan_invalid_message", message=message)
        return

    try:
        logger.debug("scan_received", **body)

        # Collect scan object and map properties
        if body['type'] == 'WebScanner':
            scanjob = StartWebScan(body)
        else:
            scanjob = StartFileScan(body)

        scanjob.start()

        asyncio.get_child_watcher().add_child_handler(
            scanjob.pid, handle_exit, body["id"]
        )

        logger.info("scan_started", **body, child_id=scanjob.pid)

        await message.ack()

    except Exception as exc:
        logger.critical("scan_start_failed", **body, exc_info=True)

        scan = Scan.objects.get(pk=body["id"])
        scan.set_scan_status_failed(str(exc))

        await message.reject(requeue=False)


async def listen(loop, host, queue_name):
    logger.info("scanner_manager_ready")

    # check for running scans at first available opportunity
    loop.create_task(check_running_scans())

    async with await aio_pika.connect_robust(host=host, loop=loop) as conn:
        chann = await conn.channel()
        queue = await chann.declare_queue(queue_name)

        async with queue.iterator() as messages:
            async for message in messages:
                async with message.process(ignore_processed=True):
                    await process_message(message)


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            '-H',
            '--amqp-host',
            type=str,
            default='localhost',
            help='Host name of the AMQP server',
        )
        parser.add_argument(
            '-Q',
            '--amqp-queue',
            type=str,
            default='datascanner',
            help='Queue to listen for changes',
        )

    def handle(self, amqp_queue, amqp_host, **kwargs):
        try:
            with asyncio.FastChildWatcher() as watcher:
                asyncio.set_child_watcher(watcher)

                loop = asyncio.get_event_loop()

                loop.run_until_complete(listen(loop, amqp_host, amqp_queue))
                loop.close()
        except KeyboardInterrupt:
            pass
