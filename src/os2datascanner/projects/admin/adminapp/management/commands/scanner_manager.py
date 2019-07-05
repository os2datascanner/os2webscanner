# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2Webscanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2web.dk/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )

import asyncio
import datetime
import json

import aio_pika
import structlog

from django import db
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from os2datascanner.engine.run_webscan import StartWebScan
from os2datascanner.engine.run_filescan import StartFileScan

from ...models.scans.scan_model import Scan

logger = structlog.get_logger()


async def check_running_scans():
    while True:
        try:
            Scan.check_running_scans()

        except Exception:
            logger.warning("check_running_scans_failed", exc_info=True)

        await asyncio.sleep(settings.CHECK_SCAN_INTERVAL)


async def cleanup_finished_scans():
    # Delete all inactive scan's queue items to start with
    last_cleanup_time = timezone.make_aware(datetime.datetime(2000, 1, 1))

    while True:
        next_cleanup_time = timezone.now()

        try:
            Scan.cleanup_finished_scans(last_cleanup_time)

            last_cleanup_time = next_cleanup_time

        except Exception:
            logger.warning("cleanup_finished_scans_failed", exc_info=True)

        await asyncio.sleep(settings.CLEANUP_SCAN_INTERVAL)


def handle_exit(pid, returncode, scan_id):
    """A scan process died; update its status pending on the success value."""

    if returncode == 0:
        logger.info(
            "scan_done", scan_id=scan_id, scan_pid=pid, status=returncode
        )

        # should we call scan.set_scan_status_done() here?

    else:
        logger.critical(
            "scan_failed", scan_id=scan_id, scan_pid=pid, status=returncode
        )

        try:
            scan = Scan.objects.get(pk=scan_id)

            scan.set_scan_status_failed(
                "Scanner process exited with status {}".format(returncode)
            )

        except Exception:
            logger.exception("handle_exit_failed")


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

        # sharing opened connections between processes leads to issues
        # with closed/open state getting out-of-sync -- so just close
        # them all prior to forking the process
        db.connections.close_all()

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

    async with await aio_pika.connect_robust(host=host, loop=loop) as conn:
        chann = await conn.channel()
        queue = await chann.declare_queue(queue_name)

        async with queue.iterator() as messages:
            async for message in messages:
                async with message.process(ignore_processed=True):
                    await process_message(message)


def add_permanent_task(loop, func):
    def handle_task_done(task):
        # if one of the "permanent" tasks return, stop the process so
        # someone notices
        loop.stop()

        try:
            task.result()
        except Exception:
            logger.exception("task_failed", task=func.__name__)

    task = loop.create_task(func)
    task.add_done_callback(handle_task_done)

    return task


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            '-H',
            '--amqp-host',
            type=str,
            default=settings.AMQP_HOST,
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

                # check for running scans at first available opportunity
                add_permanent_task(loop, check_running_scans())
                add_permanent_task(loop, cleanup_finished_scans())
                add_permanent_task(loop, listen(loop, amqp_host, amqp_queue))

                loop.run_forever()

                loop.close()
        except KeyboardInterrupt:
            pass
